"""Скачать самый новый клип из Flow под заданным именем: python scripts/download_masha_latest.py <out.mp4>"""
import asyncio, sys, importlib, types
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
for n, s in (("core", ROOT / "core"), ("core.api", ROOT / "core" / "api")):
    m = types.ModuleType(n); m.__path__ = [str(s)]; sys.modules[n] = m
E = importlib.import_module("core.api.google_flow_engine").GoogleFlowEngine
async def main(out):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(out)
    e = E(downloads_dir=str(out.parent))
    await e.connect()
    await e.download_latest_video(str(out))
    print("OK", out, out.stat().st_size)
asyncio.run(main(sys.argv[1]))
