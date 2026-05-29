from fastapi import HTTPException

def require_role(session: dict, required_role: str):
    if not session:
        raise HTTPException(status_code=401, detail="No session")

    if session.get("role") != required_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return True


def check_document_access(doc, session):
    if session.get("role") == "admin":
        return True

    if doc.owner_id != session.get("user_id"):
        raise HTTPException(
            status_code=403,
            detail="Not allowed to access this document"
        )

    return True