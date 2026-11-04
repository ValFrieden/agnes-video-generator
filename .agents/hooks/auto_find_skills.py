import sys
import json

def main():
    response = {
        "injectSteps": [
            {
                "ephemeralMessage": (
                    "[AUTO DIRECTIVE: FIND-SKILLS]\n"
                    "Для каждого пользовательского промпта обязательно активировать рабочий процесс find-skills: "
                    "выделить ключевые слова задачи, выполнить поиск подходящих скиллов (`npx skills find <keywords>`) "
                    "и применить лучшие практики из экосистемы навыков."
                )
            }
        ]
    }
    sys.stdout.write(json.dumps(response))
    sys.stdout.flush()

if __name__ == "__main__":
    main()
