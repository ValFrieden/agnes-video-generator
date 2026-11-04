"""Visual QC for agnes_clip_pipeline scenes — free Agnes multimodal chat.

For every finished scene sends its 3 QA frames (10/50/90 %) to Agnes vision
with a strict checklist and writes one verdict line per scene to stdout and
agnes_out/qc_report.txt. Light-touch by design: verdicts guide manual
re-review, no automatic regeneration.

Usage:
  .venv/Scripts/python.exe agnes_clip_qc.py [--scene N]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agnes_clip_pipeline import SCENES  # noqa: E402

INTENTS = {
    0: "a lavender field at golden hour: a young farmer man with short hair and a thin mustache and a young woman with long chestnut hair stand facing each other between the rows, shy smiles, petals and pollen in the wind",
    1: "Japan, an old wooden bridge under cherry blossoms: a young Japanese fisherman with short black hair and a thin mustache and a woman in a pink kimono with a paper parasol stand in the middle of the bridge, she offers him a cherry branch, petals drift",
    2: "1920s Paris street cafe at golden hour: a man in a brown suit and fedora with a thin mustache and a woman in a champagne dress with pearls dance slowly and calmly together, small gentle steps, facing each other, no spinning",
    3: "a small fishing boat on a calm turquoise sunset sea: a young sailor with curly black hair and a thin mustache steers at the stern, a woman in a light blue dress and golden headscarf stands at the bow with arms spread into the wind, no dolphins, no fish",
    4: "an autumn park with falling golden leaves: a man in a honey sweater rides a vintage bicycle straight along the alley, a woman in a mustard skirt and beret sits on the rear rack with arms spread like wings, bicycle never sideways",
    5: "a cozy attic in the evening with rain outside: a man with a thin mustache plays guitar in a warm sweater, a woman paints at an easel by the round window - her canvas shows them in a lavender field - she looks back at him",
    6: "a stormy sea at dusk: he stands on the deck of a departing sailing ship looking back, she stands on the stone pier with one arm stretched toward him, gulls glide high, first rain, their gazes locked",
    7: "the harbor at a magnificent golden sunset: the couple embraces closely on the wooden pier, he holds her against his chest, her dress and hair streaming in the wind, golden light swirling, no spinning, no lifting",
    8: "their wedding in the same lavender field: guests with paper umbrellas line the aisle, she in an ivory dress with a wildflower wreath walks toward him, he waits in a cream suit, they join hands, petals drift",
    9: "the same lavender field decades later: the same couple now elderly - white-haired man with white mustache and beard and silver-haired woman in a rose shawl - sit on a porch bench, her head on his shoulder, fireflies and first stars",
}

SYSTEM = (
    "You are a strict music-video quality supervisor. You will see NINE "
    "frames evenly spread across one generated animated video clip. The "
    "film must be hand-painted 2D storybook animation in a warm "
    "golden-hour palette (amber, honey, rose, cream; teal shadows). "
    "Answer with ONE line in this exact format: "
    "PASS - <one short sentence>  or  FAIL - <frame k, reason>. "
    "RULE 1, checked in EVERY frame: there must be exactly ONE couple of "
    "lovers - ONE adult MAN (short hair, thin dark mustache, masculine) "
    "and ONE adult WOMAN (long hair, dress or skirt, feminine). If in ANY "
    "frame the couple is two women, two men, or the 'man' has no "
    "mustache/reads female - it is an instant FAIL. If a frame contains "
    "no people at all (landscape, empty boat) that frame alone is fine. "
    "Also FAIL if any frame shows: badly melting or deformed faces; a "
    "photorealistic or live-action look instead of hand-drawn animation; "
    "a cold or grey palette outside the warm golden-hour palette; any "
    "readable text, letters, watermark, logo; any flag or emblem; a "
    "person singing with a wide-open mouth. Otherwise PASS."
)


def qc_scene(chat, i: int) -> str:
    qa_dir = ROOT / "agnes_out" / "preview"
    frames = [str(qa_dir / f"qa_s{i:02d}_{f}.jpg")
              for f in (10, 20, 30, 40, 50, 60, 70, 80, 90)]
    frames = [p for p in frames if os.path.exists(p)]
    if not frames:
        return f"scene {i:02d}: NO QA FRAMES"
    user = (
        f"This clip should show: {INTENTS[i]}. "
        f"Scene name: {SCENES[i]['name']}. "
        "Apply RULE 1 (one man + one woman couple) to EVERY frame. "
        "Judge the frames now."
    )
    verdict = chat.chat_multimodal(SYSTEM, user, frames)
    verdict = (verdict or "").strip().splitlines()[0] if verdict else ""
    return f"scene {i:02d} [{SCENES[i]['name']}]: {verdict[:200]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int, default=None)
    args = ap.parse_args()
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        sys.exit("AGNES_API_KEY is not set")
    from core.api.agnes_chat import AgnesChatAPI

    chat = AgnesChatAPI(api_key=api_key)
    indices = [args.scene] if args.scene is not None else range(len(SCENES))
    lines = []
    for i in indices:
        video = ROOT / "agnes_out" / f"scene_{i:02d}_{SCENES[i]['name']}" / "video.mp4"
        if not video.exists():
            lines.append(f"scene {i:02d}: NOT GENERATED YET")
            continue
        try:
            lines.append(qc_scene(chat, i))
        except Exception as e:
            lines.append(f"scene {i:02d}: QC ERROR {type(e).__name__}: {e}")
        print(lines[-1], flush=True)
    out = ROOT / "agnes_out" / "qc_report.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
