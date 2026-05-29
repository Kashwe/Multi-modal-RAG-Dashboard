# import logging
# import os
# import threading
# from pathlib import Path
# from typing import Dict, List, Optional, Tuple

# from langchain_community.vectorstores import FAISS
# from langchain_core.documents import Document

# from app.core.config import settings
# from app.services.embeddings import get_embeddings

# logger = logging.getLogger(__name__)


# class VectorStoreManager:
#     """
#     Per-session FAISS index. Each session has its own index so a user's
#     documents stay isolated. Indexes are persisted to disk so they survive
#     a restart for the lifetime of the demo.
#     """

#     def __init__(self) -> None:
#         self._stores: Dict[str, FAISS] = {}
#         self._lock = threading.RLock()
#         os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)

#     def _index_path(self, session_id: str) -> Path:
#         return Path(settings.FAISS_INDEX_DIR) / session_id

#     def _load_from_disk(self, session_id: str) -> Optional[FAISS]:
#         path = self._index_path(session_id)
#         if not path.exists():
#             return None
#         try:
#             return FAISS.load_local(
#                 str(path), get_embeddings(), allow_dangerous_deserialization=True
#             )
#         except Exception as exc:
#             logger.warning("Failed to load FAISS index for %s: %s", session_id, exc)
#             return None

#     def _persist(self, session_id: str, store: FAISS) -> None:
#         store.save_local(str(self._index_path(session_id)))

#     def add_documents(self, session_id: str, docs: List[Document]) -> int:
#         if not docs:
#             return 0
#         with self._lock:
#             store = self._stores.get(session_id) or self._load_from_disk(session_id)
#             if store is None:
#                 store = FAISS.from_documents(docs, get_embeddings())
#             else:
#                 store.add_documents(docs)
#             self._stores[session_id] = store
#             self._persist(session_id, store)
#             return len(docs)

#     def has_index(self, session_id: str) -> bool:
#         with self._lock:
#             if session_id in self._stores:
#                 return True
#             return self._index_path(session_id).exists()

#     # def search(
#     #     self, session_id: str, query: str, k: Optional[int] = None
#     # ) -> List[Tuple[Document, float]]:
#     #     k = k or settings.RETRIEVAL_K
#     #     with self._lock:
#     #         store = self._stores.get(session_id) or self._load_from_disk(session_id)
#     #         if store is None:
#     #             return []
#     #         self._stores[session_id] = store
#     #     results = store.similarity_search_with_score(query, k=k)
#     #     return results
    

#     def search(
#         self, session_id: str, query: str, k: Optional[int] = None, doc_id: Optional[str] = None,
#     ) -> List[Tuple[Document, float]]:

#         k = k or settings.RETRIEVAL_K

#         with self._lock:
#             store = self._stores.get(session_id) or self._load_from_disk(session_id)

#             if store is None:
#                return []

#             self._stores[session_id] = store

#         results = store.similarity_search_with_score(query, k=k)

#         # ✅ FILTER BY DOCUMENT ID
#         if doc_id:
#             results = [
#                 (doc, score)
#                 for doc, score in results
#                 if doc.metadata.get("doc_id") == doc_id
#             ]

#         return results
    

     

    

#     def drop(self, session_id: str) -> bool:
#         with self._lock:
#             self._stores.pop(session_id, None)
#             path = self._index_path(session_id)
#             if path.exists():
#                 import shutil

#                 shutil.rmtree(path, ignore_errors=True)
#                 return True
#             return False


# vector_store_manager = VectorStoreManager()







import logging
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import settings
from app.services.embeddings import get_embeddings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Per-session FAISS index.
    """

    def __init__(self) -> None:
        self._stores: Dict[str, FAISS] = {}
        self._lock = threading.RLock()

        os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)

    def _index_path(self, session_id: str) -> Path:
        return Path(settings.FAISS_INDEX_DIR) / session_id

    def _load_from_disk(self, session_id: str) -> Optional[FAISS]:
        path = self._index_path(session_id)

        if not path.exists():
            return None

        try:
            return FAISS.load_local(
                str(path),
                get_embeddings(),
                allow_dangerous_deserialization=True,
            )

        except Exception as exc:
            logger.warning(
                "Failed to load FAISS index for %s: %s",
                session_id,
                exc
            )
            return None

    def _persist(self, session_id: str, store: FAISS) -> None:
        store.save_local(str(self._index_path(session_id)))

    def add_documents(self, session_id: str, docs: List[Document]) -> int:

        if not docs:
            return 0

        with self._lock:

            store = (
                self._stores.get(session_id)
                or self._load_from_disk(session_id)
            )

            if store is None:
                store = FAISS.from_documents(
                    docs,
                    get_embeddings()
                )
            else:
                store.add_documents(docs)

            self._stores[session_id] = store

            self._persist(session_id, store)

            return len(docs)

    def has_index(self, session_id: str) -> bool:

        with self._lock:

            if session_id in self._stores:
                return True

            return self._index_path(session_id).exists()

    def search(
        self,
        session_id: str,
        query: str,
        k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:

        k = k or settings.RETRIEVAL_K

        with self._lock:

            store = (
                self._stores.get(session_id)
                or self._load_from_disk(session_id)
            )

            if store is None:
                return []

            self._stores[session_id] = store

        results = store.similarity_search_with_score(query, k=k)

        return results

    # ✅ US322
    def search_grouped_by_document(
        self,
        session_id: str,
        query: str,
        k: Optional[int] = None,
    ):

        results = self.search(session_id, query, k)

        grouped = {}

        for doc, score in results:

            source = doc.metadata.get("source", "unknown")

            grouped.setdefault(source, []).append(
                (doc, score)
            )

        return grouped

    def drop(self, session_id: str) -> bool:

        with self._lock:

            self._stores.pop(session_id, None)

            path = self._index_path(session_id)

            if path.exists():

                import shutil

                shutil.rmtree(path, ignore_errors=True)

                return True

            return False


vector_store_manager = VectorStoreManager()