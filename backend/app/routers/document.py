from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.document import DocumentCreate, Document
from app.models.document import Document as DocumentModel
from datetime import datetime
import os

# app/routers/document.py
from fastapi import APIRouter

router = APIRouter(
    prefix='/documents',
    tags=['documents']
)

# Define your endpoints here


@router.post("/documents/", response_model=Document)
async def create_document(
        document: DocumentCreate,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # Handle file upload
    file_location = f"uploads/{file.filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)
    with open(file_location, "wb+") as file_object:
        file_content = await file.read()
        file_object.write(file_content)

    db_document = DocumentModel(**document.dict(), file_path=file_location)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.get("/documents/", response_model=List[Document])
def list_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    documents = db.query(DocumentModel).filter(
        DocumentModel.is_deleted == False
    ).offset(skip).limit(limit).all()
    return documents


@router.get("/documents/{document_id}", response_model=Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(DocumentModel).filter(
        DocumentModel.id == document_id,
        DocumentModel.is_deleted == False
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/documents/{document_id}", response_model=Document)
def update_document(document_id: int, document: DocumentCreate, db: Session = Depends(get_db)):
    db_document = db.query(DocumentModel).filter(
        DocumentModel.id == document_id,
        DocumentModel.is_deleted == False
    ).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")

    for key, value in document.dict().items():
        setattr(db_document, key, value)

    db_document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_document)
    return db_document


@router.delete("/documents/{document_id}", response_model=Document)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(DocumentModel).filter(
        DocumentModel.id == document_id,
        DocumentModel.is_deleted == False
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.is_deleted = True
    document.updated_at = datetime.utcnow()
    db.commit()
    return document

