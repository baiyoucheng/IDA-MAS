"""Pydantic models for chat API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户问题")
    session_id: Optional[str] = Field(default="default", description="会话标识")


class SourceCitation(BaseModel):
    document: str = Field(..., description="来源文档名")
    chunk_preview: str = Field(..., description="引用片段预览")
    chunk_index: int = Field(..., description="片段序号")
    distance: float = Field(..., description="余弦距离")


class ChatResponse(BaseModel):
    response: str = Field(..., description="助手回答")
    sources: List[SourceCitation] = Field(default_factory=list, description="引用来源")
