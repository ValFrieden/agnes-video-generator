# Mandatory Project Memory Persistence Rule (Обязательное сохранение знаний в проекте)

> **Статус**: Железное правило воркспейса. Действует непрерывно во всех сессиях.

## Правило
Любая информация, полученная в ходе работы — результаты поиска (`find-skills`, `search_web`), выявленные баги генерации (например, обрезание персонажа краем кадра), принципы драматургии и режиссуры, технические параметры инструментов (Google Flow, Veo, 720p, Kling, Seedance) и все договорённости с пользователем — **ОБЯЗАНЫ немедленно сохраняться в постоянные файлы проекта**:

1. **Главная база знаний**: [`docs/dev/video_generation_master_playbook.md`](file:///d:/Projects/VideoGenerator/docs/dev/video_generation_master_playbook.md)
2. **Файлы знаний проекта**: `docs/knowledge/*.md` (включая `syntx-directing-methodology.md`, `frontend-design-standards.md`, `production-log.md`)
3. **Индексирование в SQLite**: Обязательный вызов `python scripts/knowledge_base.py sync` для актуализации поискового FTS5-индекса `project_knowledge_base/knowledge.db`.
4. **Конституция агента**: [`AGENTS.md`](file:///d:/Projects/VideoGenerator/AGENTS.md) (§6.13)
5. **Правила воркспейса**: `.agents/rules/*.md`
6. **Долгосрочная память агента**: Сохранение через MCP `claude-mem` (`save_memory`).

### Запрет:
Категорически запрещается оставлять важные выводы, пользовательские указания и правила только в текущей переписке или забывать их между сессиями. Каждое новое знание должно иметь свой постоянный дом в файловой структуре проекта и быть немедленно проиндексировано.
