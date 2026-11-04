#!/usr/bin/env python3
"""scripts/create_scenario.py — CLI-инструмент для создания профессиональных сценариев и раскадровок.

Использование:
  python scripts/create_scenario.py --idea "Космическая одиссея исследователя..." --bpm 120 --scenes 12 --out my_scenario.md
"""

import argparse
import sys
from pathlib import Path

# Fix Windows stdout utf-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.screenwriter.scenario_director import ScenarioDirector


def main():
    parser = argparse.ArgumentParser(description="AI Scenario Director — Профессиональный сценарный генератор")
    parser.add_argument("--idea", type=str, required=True, help="Идея, сюжет или тема песни/видео")
    parser.add_argument("--style", type=str, default="Vintage Gouache Cel Animation, Edward Hopper lighting, cinematic 16:9", help="Визуальный художественный стиль")
    parser.add_argument("--duration", type=float, default=96.0, help="Общая длительность видео в секундах")
    parser.add_argument("--bpm", type=int, default=120, help="Темп музыки в BPM для точной склейки по тактам")
    parser.add_argument("--scenes", type=int, default=12, help="Количество сцен")
    parser.add_argument("--anchor", type=str, default="A vibrant canary-yellow umbrella", help="Сквозной символический предмет")
    parser.add_argument("--out", type=str, default="generated_scenario.md", help="Путь для сохранения сценария (Markdown)")

    args = parser.parse_args()

    print(f"🎬 Запуск Scenario Director...")
    print(f"  • Идея: {args.idea[:70]}...")
    print(f"  • Стиль: {args.style}")
    print(f"  • Хронометраж: {args.duration}с ({args.bpm} BPM, {args.scenes} сцен)")
    print(f"  • Лейтмотив: {args.anchor}")

    director = ScenarioDirector()
    project = director.generate_scenario(
        story_idea=args.idea,
        visual_style=args.style,
        total_duration_s=args.duration,
        bpm=args.bpm,
        num_scenes=args.scenes,
        symbolic_anchor=args.anchor
    )

    md_content = director.export_to_markdown(project)
    out_path = Path(args.out)
    out_path.write_text(md_content, encoding="utf-8")

    print(f"\n✅ Сценарий успешно создан и сохранён в: {out_path.resolve()}")
    print(f"Персонаж: {project.character.name} (~{project.character.age} лет)")
    print(f"Сцен сгенерировано: {len(project.shots)}")


if __name__ == "__main__":
    main()
