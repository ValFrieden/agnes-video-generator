#!/usr/bin/env python3
"""scripts/knowledge_base.py — CLI утилита управления базой знаний проекта VideoGenerator.

Использование:
  python scripts/knowledge_base.py sync               # Полная синхронизация/индексация документов
  python scripts/knowledge_base.py search "prompt"    # Быстрый FTS5 поиск по документам проекта
  python scripts/knowledge_base.py status             # Статус базы знаний и статистика
  python scripts/knowledge_base.py cross "seedance"   # Поиск по проекту + внешняя база видеогайдов из D:\\Projects\\watch
"""
import argparse
import json
import os
import sys
from pathlib import Path

# UTF-8 вывод для Windows консоли
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_knowledge_base.kb_core import (
    sync_knowledge_base,
    search_knowledge_base,
    get_status,
)


def cmd_sync(args):
    print("🔄 Синхронизация базы знаний проекта VideoGenerator...")
    res = sync_knowledge_base(PROJECT_ROOT, rebuild=args.rebuild)
    print(f"✅ Успешно! Проиндексировано: {res['indexed_or_updated']} файлов.")
    print(f"📚 Всего документов в базе: {res['total_documents']} (секций: {res['total_sections']})")
    print(f"💾 База данных: {res['database_path']}")


def cmd_search(args):
    results = search_knowledge_base(args.query, category=args.category, limit=args.limit)
    if not results:
        print(f"🔍 По запросу '{args.query}' ничего не найдено.")
        return

    print(f"\n🎯 Найдено совпадений: {len(results)} по запросу '{args.query}':\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.title} ({r.category})")
        print(f"    📄 Файл: {r.rel_path} → ## {r.heading}")
        # Очищаем сниппет от переносов
        clean_snip = r.snippet.replace("<b>", "\033[1;33m").replace("</b>", "\033[0m")
        print(f"    💬 {clean_snip}\n")


def cmd_status(args):
    status = get_status()
    if not status.get("ready"):
        print("⚠️ База знаний ещё не создана. Запустите: python scripts/knowledge_base.py sync")
        return

    print("📊 Статус базы знаний VideoGenerator:")
    print(f"• Документов: {status['document_count']}")
    print(f"• Секций (FTS5): {status['section_count']}")
    print(f"• База: {status['database_path']}")
    print("\n📂 Категории:")
    for cat, cnt in status["categories"].items():
        print(f"  - {cat}: {cnt} документов")
    print("\n🛠️ Топ обнаруженных инструментов/технологий:")
    print("  " + ", ".join(status["top_tools"]))


def cmd_cross(args):
    """Сквозной поиск по проекту + внешняя база видеогайдов из D:\\Projects\\watch."""
    print(f"🌐 Сквозной поиск по проекту и архиву видеогайдов: '{args.query}'\n")

    # 1. Поиск в проекте
    local_hits = search_knowledge_base(args.query, limit=args.limit)
    print(f"📁 [VideoGenerator] Найдено в проекте: {len(local_hits)}")
    for i, r in enumerate(local_hits, 1):
        print(f"  {i}. {r.title} ({r.rel_path})")

    # 2. Поиск в watch базе
    watch_db = Path("D:/Projects/watch/video_knowledge_base/knowledge.db")
    if watch_db.exists():
        import sqlite3
        try:
            c = sqlite3.connect(str(watch_db))
            c.row_factory = sqlite3.Row
            rows = c.execute("""
                SELECT d.title, d.category, s.heading, d.report_path
                FROM section_search ss
                JOIN sections s ON ss.section_id = s.id
                JOIN documents d ON ss.document_id = d.id
                WHERE section_search MATCH ?
                LIMIT ?
            """, (f'"{args.query}"*', args.limit)).fetchall()
            print(f"\n🎬 [Watch Video KB] Найдено в видеогайдах: {len(rows)}")
            for i, r in enumerate(rows, 1):
                print(f"  {i}. {r['title']} [{r['category']}] → {r['heading']}")
        except Exception as e:
            print(f"\n⚠️ Не удалось опросить watch базу: {e}")


def main():
    parser = argparse.ArgumentParser(description="База знаний VideoGenerator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="Индексация проектных документов")
    p_sync.add_argument("--rebuild", action="store_true", help="Полная пересборка с нуля")

    p_search = sub.add_parser("search", help="FTS5 поиск по документам")
    p_search.add_argument("query", help="Поисковый запрос")
    p_search.add_argument("--category", default="", help="Фильтр по категории")
    p_search.add_argument("--limit", type=int, default=8, help="Лимит выдачи")

    sub.add_parser("status", help="Статистика базы")

    p_cross = sub.add_parser("cross", help="Сквозной поиск (проект + watch)")
    p_cross.add_argument("query", help="Поисковый запрос")
    p_cross.add_argument("--limit", type=int, default=5, help="Лимит выдачи")

    args = parser.parse_args()
    if args.command == "sync":
        cmd_sync(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "cross":
        cmd_cross(args)


if __name__ == "__main__":
    main()
