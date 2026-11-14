import asyncio
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

    parents = await page.evaluate("""() => {
        const opt = document.querySelector('[role="radio"][aria-label*="Genehmigen"], [aria-label="Genehmigen"]');
        if (!opt) return 'NOT_FOUND';
        let p = opt;
        const chain = [];
        while (p && p.tagName !== 'BODY') {
            chain.push(p.tagName + (p.className ? '.' + p.className : ''));
            p = p.parentElement;
        }
        return chain;
    }""")
    print("PARENT CHAIN:", parents)

    # Проверим, есть ли вообще элемент flow-permission-message
    has_custom = await page.evaluate("() => document.querySelectorAll('flow-permission-message').length")
    print("flow-permission-message count:", has_custom)


if __name__ == "__main__":
    asyncio.run(main())
