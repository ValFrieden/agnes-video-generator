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

    chat_history = await page.evaluate("""() => {
        const rows = Array.from(document.querySelectorAll('.message-row, flow-chat-bubble, .agent-row, .user-row'));
        return rows.map(r => ({
            type: r.className,
            text: (r.innerText || '').trim()
        })).filter(r => r.text.length > 0);
    }""")

    print(f"Total chat items: {len(chat_history)}")
    print("LAST 10 CHAT MESSAGES:")
    for item in chat_history[-10:]:
        print(f"[{item['type']}]")
        print(item['text'])
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
