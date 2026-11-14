from pathlib import Path

file_path = Path("core/api/google_flow_engine.py")
content = file_path.read_text(encoding="utf-8")

old_block = """    async def _choose_on_last_card(self, labels: List[str]) -> bool:
        \"\"\"Wählt die erste verfügbare Option auf der letzten Kostenkarte.\"\"\"
        page = await self.connect()
        card = page.locator("flow-permission-message").last
        for label in labels:
            option = card.locator(f'[role="radio"][aria-label="{label}"]').first
            if not await self._visible(option, 2000):
                continue"""

new_block = """    async def _choose_on_last_card(self, labels: List[str]) -> bool:
        \"\"\"Wählt die erste verfügbare Option auf der letzten Kostenkarte (unterstützt flow-permission-message und choice-container).\"\"\"
        page = await self.connect()
        card = page.locator("flow-permission-message, div.choice-container, [role='radiogroup']").last
        for label in labels:
            option = card.locator(f'[role="radio"][aria-label*="{label}"], .option-row:has-text("{label}")').first
            if not await self._visible(option, 1500):
                option = page.locator(f'[role="radio"][aria-label*="{label}"], [aria-label="{label}"], button:has-text("{label}")').last
                if not await self._visible(option, 1500):
                    continue"""

if old_block in content:
    content = content.replace(old_block, new_block)
    file_path.write_text(content, encoding="utf-8")
    print("PATCH_APPLIED_SUCCESSFULLY")
else:
    print("OLD_BLOCK_NOT_FOUND")
