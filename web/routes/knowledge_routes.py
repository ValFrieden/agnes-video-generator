"""web.routes.knowledge_routes — REST API для доступа к проектной базе знаний VideoGenerator."""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from project_knowledge_base.kb_core import (
    search_knowledge_base,
    search_watch_knowledge_base,
    get_document_content,
    get_status,
    sync_knowledge_base,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/status")
async def knowledge_status():
    """Возвращает статус готовности и статистику базы знаний проекта."""
    import json
    import os
    data = dict(get_status())
    graph_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "graphify-out", "graph.json")
    graph_nodes = None
    graph_edges = None
    if os.path.isfile(graph_path):
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                g = json.load(f)
            nodes = g.get("nodes")
            links = g.get("links") or g.get("edges")
            if isinstance(nodes, list):
                graph_nodes = len(nodes)
            if isinstance(links, list):
                graph_edges = len(links)
        except Exception:
            pass
    data["graph_nodes"] = graph_nodes
    data["graph_edges"] = graph_edges
    return {"ok": True, "data": data}


@router.get("/search")
async def knowledge_search(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    limit: int = Query(10, ge=1, le=50, description="Максимум результатов"),
    cross_search: bool = Query(False, description="Включить результаты из видеогайдов watch")
):
    """Полнотекстовый поиск FTS5 по всей проектной документации и сценариям."""
    hits = search_knowledge_base(query=q, category=category or "", limit=limit)
    watch_hits = []
    if cross_search:
        watch_hits = search_watch_knowledge_base(query=q, limit=limit)

    return {
        "ok": True,
        "query": q,
        "category": category,
        "count": len(hits),
        "results": [
            {
                "document_id": h.document_id,
                "title": h.title,
                "rel_path": h.rel_path,
                "category": h.category,
                "heading": h.heading,
                "snippet": h.snippet,
                "score": h.score,
                "modified_at": h.modified_at,
                "source": "project"
            }
            for h in hits
        ],
        "watch_results": watch_hits
    }


@router.get("/document/{doc_id}")
async def knowledge_document(doc_id: int):
    """Возвращает полное содержимое документа по его ID."""
    doc = get_document_content(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return {"ok": True, "document": doc}


@router.post("/sync")
async def knowledge_sync(rebuild: bool = Query(False, description="Полная переиндексация с нуля")):
    """Запускает синхронизацию и индексацию всех markdown документов проекта."""
    import asyncio
    try:
        res = await asyncio.to_thread(sync_knowledge_base, rebuild=rebuild)
        return {"ok": True, "result": res}
    except Exception as e:
        logger.error(f"[Knowledge] Ошибка синхронизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))
