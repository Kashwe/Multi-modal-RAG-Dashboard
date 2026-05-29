# from pathlib import Path

# from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
# from sqlalchemy.orm import Session

# from app.db.database import get_db
# from app.models.document import Document

# from app.core.config import settings
# from app.schemas.documents import DocumentListResponse, DocumentUploadResponse
# from app.services.document_parser import (
#     UnsupportedFileType,
#     parse_and_chunk,
# )
# from app.services.session_store import session_store
# from app.services.vector_store import vector_store_manager

# router = APIRouter(prefix="/documents", tags=["Documents"])


# @router.post("/{session_id}", response_model=DocumentUploadResponse)
# async def upload_document(
#     session_id: str,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ) -> DocumentUploadResponse:

#     session = session_store.get(session_id)

#     if session is None:
#         raise HTTPException(status_code=404, detail="session not found")

#     filename = file.filename or "upload"

#     suffix = Path(filename).suffix.lower()

#     if suffix not in settings.ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=415,
#             detail=f"unsupported file type: {suffix}"
#         )

#     content = await file.read()

#     if len(content) > settings.MAX_UPLOAD_SIZE:
#         raise HTTPException(
#             status_code=413,
#             detail="file too large"
#         )

#     try:
#         doc_id, chunks = parse_and_chunk(filename, content)

#     except UnsupportedFileType as exc:
#         raise HTTPException(
#             status_code=415,
#             detail=str(exc)
#         )

#     if not chunks:
#         raise HTTPException(
#             status_code=422,
#             detail="no text extracted from file"
#         )

#     # Store chunks in vector database
#     vector_store_manager.add_documents(session_id, chunks)

#     # Save metadata to PostgreSQL
#     db_document = Document(
#         filename=filename,
#         uploaded_by=session_id,
#         status="uploaded"
#     )

#     db.add(db_document)
#     db.commit()
#     db.refresh(db_document)

#     # Update session store
#     doc_ids = list(session.get("doc_ids", []))

#     doc_ids.append(doc_id)

#     session_store.update(session_id, doc_ids=doc_ids)

#     return DocumentUploadResponse(
#         doc_id=doc_id,
#         filename=filename,
#         chunks=len(chunks),
#         session_id=session_id
#     )


# @router.get("/{session_id}", response_model=DocumentListResponse)
# async def list_documents(session_id: str) -> DocumentListResponse:

#     session = session_store.get(session_id)

#     if session is None:
#         raise HTTPException(
#             status_code=404,
#             detail="session not found"
#         )

#     return DocumentListResponse(
#         session_id=session_id,
#         doc_ids=session.get("doc_ids", [])
#     )





from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import Document

from app.core.config import settings
from app.schemas.documents import DocumentListResponse, DocumentUploadResponse
from app.services.document_parser import (
    UnsupportedFileType,
    parse_and_chunk,
)
from app.services.session_store import session_store
from app.services.vector_store import vector_store_manager

# 🔐 RBAC IMPORT
from app.core.rbac import check_document_access

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/{session_id}", response_model=DocumentUploadResponse)
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> DocumentUploadResponse:

    session = session_store.get(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()

    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"unsupported file type: {suffix}")

    content = await file.read()

    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="file too large")

    try:
        doc_id, chunks = parse_and_chunk(filename, content)

    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc))

    if not chunks:
        raise HTTPException(status_code=422, detail="no text extracted from file")

    # Store chunks in vector DB
    vector_store_manager.add_documents(session_id, chunks)

    # Save metadata to PostgreSQL
    db_document = Document(
        filename=filename,
        uploaded_by=session.get("user_id"),  # 🔐 FIXED (was session_id)
        status="uploaded",
        owner_id=session.get("user_id")      # 🔐 IMPORTANT
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # Update session store
    doc_ids = list(session.get("doc_ids", []))
    doc_ids.append(doc_id)

    session_store.update(session_id, doc_ids=doc_ids)

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=filename,
        chunks=len(chunks),
        session_id=session_id
    )


@router.get("/{session_id}", response_model=DocumentListResponse)
async def list_documents(session_id: str) -> DocumentListResponse:

    session = session_store.get(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    return DocumentListResponse(
        session_id=session_id,
        doc_ids=session.get("doc_ids", [])
    )