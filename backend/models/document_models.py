"""Pydantic models for documents API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    name: str = Field(..., description="文档文件名")
    doc_id: str = Field(..., description="文档唯一 ID")
    chunk_count: int = Field(..., description="分块数量")
    last_indexed: Optional[str] = Field(default="", description="最后索引时间")


class DocumentListResponse(BaseModel):
    documents: List[DocumentSummary] = Field(default_factory=list)
    total: int = Field(default=0)


class UploadResponse(BaseModel):
    success: bool = True
    filename: str = Field(..., description="文件名")
    chunk_count: int = Field(..., description="分块数")
    message: str = Field(default="上传成功")


class DeleteResponse(BaseModel):
    success: bool = True
    filename: str = Field(...)
    message: str = Field(default="删除成功")
