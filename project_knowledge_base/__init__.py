"""project_knowledge_base — VideoGenerator Project Knowledge Base package."""
from project_knowledge_base.kb_core import (
    sync_knowledge_base,
    search_knowledge_base,
    get_status,
    SearchResult
)

__all__ = ["sync_knowledge_base", "search_knowledge_base", "get_status", "SearchResult"]
