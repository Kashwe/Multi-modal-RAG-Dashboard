from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.db.database import Base


class Document(Base):

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)

    uploaded_by = Column(String, default="anonymous")

    status = Column(String, default="uploaded")

    created_at = Column(DateTime, default=datetime.utcnow)