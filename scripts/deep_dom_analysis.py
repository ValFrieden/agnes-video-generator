import asyncio
import json
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine


async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()

    analysis = await page.evaluate("""() => {
        // Рекурсивный поиск по Shadow DOM и обычному DOM
        function getAllElements(root = document) {
            let elements = Array.from(root.querySelectorAll('*'));
            for (const el of elements) {
                if (el.shadowRoot) {
                    elements = elements.concat(getAllElements(el.shadowRoot));
                }
            }
            return elements;
        }

        const all = getAllElements();
        const matches = [];

        for (const el of all) {
            const txt = (el.innerText || el.textContent || '').trim();
            if (txt.includes('Genehmigen') || txt.includes('Guthabenpunkte') || txt.includes('Approve')) {
                matches.push({
                    tag: el.tagName,
                    classes: el.className,
                    id: el.id,
                    role: el.getAttribute('role'),
                    ariaLabel: el.getAttribute('aria-label'),
                    text: txt.slice(0, 100),
                    isClickable: typeof el.click === 'function',
                    rect: el.getBoundingClientRect()
                });
            }
        }

        return {
            totalElementsScanned: all.length,
            matchCount: matches.length,
            matches: matches.slice(-10) // последние 10 релевантных
        };
    }""")

    print(json.dumps(analysis, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
