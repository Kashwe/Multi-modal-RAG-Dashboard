"""Streamlit UI for the Multi-Modal RAG Dashboard backend.

Run with:
    streamlit run ui/app.py
"""
import os
import time
from typing import Any, Dict, Optional

import pandas as pd
import requests
import streamlit as st

API_BASE = os.environ.get("RAG_API_BASE", "http://127.0.0.1:8000/api/v1")
HEALTH_URL = os.environ.get("RAG_HEALTH_URL", "http://127.0.0.1:8000/health")

st.set_page_config(
    page_title="Multi-Modal RAG Dashboard",
    page_icon="📚",
    layout="wide",
)


def api_get(path: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=30)
        if r.status_code >= 400:
            st.error(f"GET {path} → {r.status_code}: {r.text}")
            return None
        return r.json()
    except requests.RequestException as exc:
        st.error(f"Backend unreachable: {exc}")
        return None


def api_post(path: str, **kwargs) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(f"{API_BASE}{path}", timeout=120, **kwargs)
        if r.status_code >= 400:
            st.error(f"POST {path} → {r.status_code}: {r.text}")
            return None
        if r.status_code == 204 or not r.content:
            return {}
        return r.json()
    except requests.RequestException as exc:
        st.error(f"Backend unreachable: {exc}")
        return None


def api_delete(path: str) -> bool:
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=30)
        return r.status_code < 400
    except requests.RequestException as exc:
        st.error(f"Backend unreachable: {exc}")
        return False


def check_backend() -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        return None
    return None


# Session state init
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Sidebar: backend status + session management
with st.sidebar:
    st.title("📚 RAG Dashboard")
    health = check_backend()
    if health is None:
        st.error("Backend not reachable at " + HEALTH_URL)
        st.stop()
    st.success(f"Backend: {health.get('status', 'unknown')}")
    st.caption(f"Project: {health.get('project')}")
    st.caption(f"Groq configured: {health.get('groq_configured')}")

    st.divider()
    st.subheader("Session")

    if st.session_state.session_id:
        st.code(st.session_state.session_id, language=None)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New", use_container_width=True):
                st.session_state.session_id = None
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("Delete", use_container_width=True, type="primary"):
                if api_delete(f"/sessions/{st.session_state.session_id}"):
                    st.session_state.session_id = None
                    st.session_state.chat_history = []
                    st.rerun()
    else:
        if st.button("Create session", type="primary", use_container_width=True):
            resp = api_post("/sessions")
            if resp:
                st.session_state.session_id = resp["session_id"]
                st.session_state.chat_history = []
                st.success(f"Backend store: {resp['backend']}")
                st.rerun()

    sessions_resp = api_get("/sessions")
    if sessions_resp:
        st.caption(
            f"Store: **{sessions_resp['backend']}** · Active sessions: "
            f"**{sessions_resp['count']}**"
        )


# Main area
if not st.session_state.session_id:
    st.title("Multi-Modal RAG Dashboard")
    st.info("👈 Create a session from the sidebar to get started.")
    st.markdown(
        """
        ### What this demo does
        1. **Sessions** — Each session has isolated documents and analytics
            (Redis with in-memory fallback).
        2. **Upload** — PDF / DOCX / TXT / MD files are parsed and chunked.
        3. **Embed & Index** — Chunks embedded locally (sentence-transformers)
            and indexed in a per-session FAISS store.
        4. **Ask** — LangChain + Groq answers your questions using the
            retrieved chunks.
        5. **Analyze** — Latency, retrieval-score, and token-usage
            dashboards update live.
        """
    )
    st.stop()


tab_upload, tab_chat, tab_analytics = st.tabs(
    ["📤 Upload", "💬 Chat", "📊 Analytics"]
)


# Upload tab
with tab_upload:
    st.subheader("Upload documents")
    uploaded = st.file_uploader(
        "Drop a PDF / DOCX / TXT / MD file",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
    )
    if uploaded and st.button("Index files", type="primary"):
        for f in uploaded:
            with st.spinner(f"Indexing {f.name}…"):
                files = {"file": (f.name, f.getvalue(), f.type or "application/octet-stream")}
                resp = api_post(
                    f"/documents/{st.session_state.session_id}", files=files
                )
                if resp:
                    st.success(
                        f"{f.name} → {resp['chunks']} chunks (doc_id={resp['doc_id'][:8]}…)"
                    )

    st.divider()
    docs = api_get(f"/documents/{st.session_state.session_id}")
    if docs:
        st.caption(f"Indexed documents in this session: {len(docs['doc_ids'])}")
        if docs["doc_ids"]:
            st.dataframe(
                pd.DataFrame({"doc_id": docs["doc_ids"]}),
                use_container_width=True,
                hide_index=True,
            )


# Chat tab
with tab_chat:
    st.subheader("Ask a question")

    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.write(entry["answer"])
            meta = entry["meta"]
            cols = st.columns(4)
            cols[0].metric("Latency", f"{meta['latency_ms']:.0f} ms")
            cols[1].metric("Retrieval", f"{meta['retrieval_latency_ms']:.0f} ms")
            cols[2].metric("LLM", f"{meta['llm_latency_ms']:.0f} ms")
            cols[3].metric("Tokens", meta["total_tokens"])
            if entry["sources"]:
                with st.expander(f"Sources ({len(entry['sources'])})"):
                    for i, s in enumerate(entry["sources"], 1):
                        st.markdown(
                            f"**[{i}] {s['source']}** · score `{s['score']:.3f}` · chunk #{s['chunk_index']}"
                        )
                        st.caption(s["preview"])

    question = st.chat_input("Type your question…")
    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                t0 = time.time()
                resp = api_post(
                    f"/query/{st.session_state.session_id}",
                    json={"question": question},
                )
                wall = (time.time() - t0) * 1000
            if resp:
                st.write(resp["answer"])
                cols = st.columns(4)
                cols[0].metric("Latency", f"{resp['latency_ms']:.0f} ms")
                cols[1].metric("Retrieval", f"{resp['retrieval_latency_ms']:.0f} ms")
                cols[2].metric("LLM", f"{resp['llm_latency_ms']:.0f} ms")
                cols[3].metric("Tokens", resp["total_tokens"])
                if resp["sources"]:
                    with st.expander(f"Sources ({len(resp['sources'])})"):
                        for i, s in enumerate(resp["sources"], 1):
                            st.markdown(
                                f"**[{i}] {s['source']}** · score `{s['score']:.3f}` · chunk #{s['chunk_index']}"
                            )
                            st.caption(s["preview"])
                st.session_state.chat_history.append(
                    {
                        "question": question,
                        "answer": resp["answer"],
                        "sources": resp["sources"],
                        "meta": {
                            "latency_ms": resp["latency_ms"],
                            "retrieval_latency_ms": resp["retrieval_latency_ms"],
                            "llm_latency_ms": resp["llm_latency_ms"],
                            "total_tokens": resp["total_tokens"],
                        },
                    }
                )


# Analytics tab
with tab_analytics:
    refresh = st.button("🔄 Refresh", key="refresh_analytics")
    summary = api_get("/analytics/summary")
    session_metrics = api_get(f"/analytics/sessions/{st.session_state.session_id}")

    if not summary:
        st.warning("No analytics yet.")
        st.stop()

    # Top KPIs
    lat = summary["latency"]
    tok = summary["tokens"]
    ret = summary["retrieval"]
    cols = st.columns(4)
    cols[0].metric("Queries", tok["queries"])
    cols[1].metric("Avg latency", f"{lat['avg_ms']:.0f} ms")
    cols[2].metric("P95 latency", f"{lat.get('p95_ms', 0):.0f} ms")
    cols[3].metric("Total tokens", tok["total_tokens"])

    st.divider()

    col_lat, col_ret = st.columns(2)
    with col_lat:
        st.subheader("Latency (ms) — recent")
        samples = lat.get("samples", [])
        if samples:
            st.line_chart(pd.DataFrame({"latency_ms": samples}))
        else:
            st.caption("No samples yet.")

    with col_ret:
        st.subheader("Retrieval score distribution")
        hist = ret.get("histogram", [])
        if hist:
            df = pd.DataFrame(hist)
            st.bar_chart(df.set_index("bucket"))
            st.caption(
                f"avg={ret['avg']:.3f} · min={ret['min']:.3f} · max={ret['max']:.3f}"
            )
        else:
            st.caption("No retrieval scores yet.")

    st.divider()
    st.subheader("Token usage — recent queries")
    recent = tok.get("recent", [])
    if recent:
        df = pd.DataFrame(recent)
        st.bar_chart(df[["prompt", "completion"]])
        st.caption(
            f"prompt={tok['prompt_tokens']} · completion={tok['completion_tokens']} "
            f"· avg/query={tok['avg_per_query']}"
        )
    else:
        st.caption("No token data yet.")

    if session_metrics:
        st.divider()
        st.subheader("This session")
        cols = st.columns(3)
        cols[0].metric("Messages", session_metrics["message_count"])
        cols[1].metric("Avg latency", f"{session_metrics['latency']['avg_ms']:.0f} ms")
        cols[2].metric("Total tokens", session_metrics["tokens"]["total"])
