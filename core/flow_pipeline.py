"""core/flow_pipeline.py — Kommandozeile für die Google-Flow-Produktion.

Ersetzt die Einmal-Skripte durch feste Befehle, die Zustandsdatei, Budget-Policy
und Journal automatisch nutzen::

    python -m core.flow_pipeline status
    python -m core.flow_pipeline balance
    python -m core.flow_pipeline check --a foto.jpg --b toon.jpg
    python -m core.flow_pipeline image --prompt "..." --ref frame.jpg --out s03_key.jpg
    python -m core.flow_pipeline video --shot S03 --frame s03_key.jpg --motion "..." --out clips/clip_03.mp4
    python -m core.flow_pipeline morph --photo a.jpg --toon b.jpg --out morph.mp4 --sheet sheet.jpg
    python -m core.flow_pipeline sheet --video clip.mp4 --out sheet.jpg

Konten kommen aus ``flow_accounts.json``, der Zustand aus ``flow_state/shots.json``,
das Guthaben-Journal aus ``flow_state/credits.jsonl``. Genehmigt wird nur
einmalig („Genehmigen“), nie „Immer genehmigen“.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from core import flow_frames, flow_prompts, flow_transitions
from core.api.google_flow_engine import GoogleFlowEngine
from core.api.google_flow_errors import FlowStoppedError
from core.flow_budget import BudgetPolicy, CreditLedger, FlowAccounts
from core.flow_shot_state import ShotAlreadySubmittedError, ShotStateStore

logger = logging.getLogger("flow_pipeline")

STATE_DIR = Path("flow_state")
ACCOUNTS_FILE = Path("flow_accounts.json")


def _store(root: Path) -> ShotStateStore:
    return ShotStateStore(root / STATE_DIR / "shots.json")


def _ledger(root: Path) -> CreditLedger:
    return CreditLedger(root / STATE_DIR / "credits.jsonl")


async def open_project(engine: GoogleFlowEngine, accounts: FlowAccounts, account: Optional[str]):
    """Öffnet das Projekt des Kontos und schließt Dialoge."""
    page = await engine.connect()
    await page.goto(accounts.project_url(account), wait_until="domcontentloaded")
    await asyncio.sleep(6)
    await page.keyboard.press("Escape")
    await engine.exit_editor_if_open()
    return page


# ── Befehle ──────────────────────────────────────────────────────────────────


def cmd_status(args) -> int:
    store, ledger = _store(args.root), _ledger(args.root)
    shots = store.all()
    if not shots:
        print("Keine Shots in", args.root / STATE_DIR / "shots.json")
    for sid, rec in sorted(shots.items()):
        credits = sum(int(h.get("credits") or 0) for h in rec.get("history", []))
        print(f"{sid:<6} v{rec.get('version', 1)} {rec.get('status', '?'):<15} {credits:>4} Credits  {rec.get('clip', '')}")
    print(f"Summe laut Shots: {store.total_credits()}  |  laut Journal: {ledger.spent()}")
    return 0


def cmd_check(args) -> int:
    problems = flow_frames.check_pair(args.a, args.b) if args.b else flow_frames.check_frame(args.a).problems
    for p in problems:
        print("PROBLEM:", p)
    if not problems:
        print("OK")
    return 1 if problems else 0


def cmd_sheet(args) -> int:
    times = [float(t) for t in args.times.split(",")]
    print(flow_transitions.contact_sheet(args.video, args.out, times))
    return 0


def cmd_morph(args) -> int:
    out = flow_transitions.render_morph(args.photo, args.toon, args.out, duration=args.duration)
    print(out)
    if args.sheet:
        d = args.duration
        print(flow_transitions.contact_sheet(out, args.sheet, [0.2 * d / 8, 0.28 * d, 0.45 * d, 0.6 * d, 0.9 * d]))
    return 0


async def cmd_balance(args) -> int:
    accounts = FlowAccounts.load(args.root / ACCOUNTS_FILE)
    engine = GoogleFlowEngine()
    try:
        await open_project(engine, accounts, args.account)
        balance = await engine.read_credit_balance()
    finally:
        await engine.close()
    if balance is None:
        print("Kontostand nicht lesbar")
        return 1
    name = args.account or accounts.default_name
    _ledger(args.root).record("balance", 0, account=name, balance_after=balance)
    print(f"{name}: {balance} Credits")
    return 0


async def cmd_character(args) -> int:
    accounts = FlowAccounts.load(args.root / ACCOUNTS_FILE)
    account = args.account or accounts.default_name
    engine = GoogleFlowEngine()
    try:
        await open_project(engine, accounts, account)
        if args.char_action == "list":
            chars = await engine.list_characters()
            if not chars:
                print(f"Keine Charaktere im Projekt von '{account}' gefunden.")
            else:
                print(f"Charaktere in '{account}':")
                for c in chars:
                    print(f" - @{c}")
            return 0
        elif args.char_action == "create":
            if not args.images:
                print("Fehler: Mindestens ein Referenzbild (--images) ist erforderlich.")
                return 1
            for img in args.images:
                if not Path(img).is_file():
                    print(f"Referenzbild nicht gefunden: {img}")
                    return 1
            ok = await engine.create_character(
                name=args.name,
                image_paths=args.images,
                description=args.desc,
            )
            print(f"Charakter '{args.name}' {'angelegt' if ok else 'existierte bereits'}.")
            return 0 if ok else 0
        else:
            print("Unbekannte Aktion:", args.char_action)
            return 1
    except FlowStoppedError as exc:
        print("GESTOPPT:", exc)
        return 2
    except Exception as exc:
        print("FEHLER:", exc)
        return 1
    finally:
        await engine.close()


async def cmd_scene(args) -> int:
    accounts = FlowAccounts.load(args.root / ACCOUNTS_FILE)
    account = args.account or accounts.default_name
    engine = GoogleFlowEngine()
    try:
        await open_project(engine, accounts, account)
        if args.scene_action == "add":
            ok = await engine.add_latest_clip_to_scene()
            print("Clip zur Szene hinzugefügt." if ok else "Clip konnte nicht zur Szene hinzugefügt werden.")
            return 0 if ok else 1
        elif args.scene_action == "open":
            ok = await engine.open_scenes_view()
            print("Szenen-Ansicht geöffnet." if ok else "Szenen-Ansicht konnte nicht geöffnet werden.")
            return 0 if ok else 1
        else:
            print("Unbekannte Szenen-Aktion:", args.scene_action)
            return 1
    finally:
        await engine.close()


async def cmd_image(args) -> int:
    accounts = FlowAccounts.load(args.root / ACCOUNTS_FILE)
    prompt = flow_prompts.image_prompt(
        args.prompt,
        same_composition_as_reference=args.same_composition,
        character=getattr(args, "character", None),
    )
    for ref in args.ref or []:
        # Referenzen dürfen jede Form haben (Charakterkarte, Hochformat); geprüft wird nur das Vorhandensein.
        if not Path(ref).is_file():
            print(f"Referenz nicht gefunden: {ref}")
            return 1
    engine = GoogleFlowEngine()
    try:
        await open_project(engine, accounts, args.account)
        path = await engine.generate_image(
            prompt,
            references=args.ref or [],
            output_path=args.out,
            character=getattr(args, "character", None),
        )
    except FlowStoppedError as exc:
        print("GESTOPPT:", exc)
        return 2
    finally:
        await engine.close()
    print(path)
    return 0


async def cmd_video(args) -> int:
    accounts = FlowAccounts.load(args.root / ACCOUNTS_FILE)
    account = args.account or accounts.default_name
    if not getattr(args, "force", False):
        problems = flow_frames.check_frame(args.frame).problems
        if problems:
            print(f"Startkader {args.frame}: {'; '.join(problems)} (Nutze --force zum Ignorieren)")
            return 1
    for ref in args.ref or []:
        if not Path(ref).is_file():
            print(f"Referenz nicht gefunden: {ref}")
            return 1
    char_name = getattr(args, "character", None)
    add_scene = getattr(args, "add_to_scene", False)
    prompt = flow_prompts.video_prompt(
        args.motion,
        seconds=args.seconds,
        extra_refs=len(args.ref or []),
        character=char_name,
    )
    policy = BudgetPolicy(per_clip_max=args.max_clip, session_budget=args.budget, reserve=args.reserve)
    store, ledger = _store(args.root), _ledger(args.root)
    model_name = getattr(args, "model", "Veo 3.1 - Fast")
    engine = GoogleFlowEngine(default_model=model_name)
    try:
        await open_project(engine, accounts, account)
        if ledger.last_balance(account) is None:
            balance = await engine.read_credit_balance()
            if balance is not None:
                ledger.record("balance", 0, account=account, balance_after=balance)
        ok = await engine.generate_scene(
            prompt=prompt,
            reference_image_path=args.frame,
            output_clip_path=args.out,
            prompt_as_is=True,
            extra_references=args.ref or [],
            shot_store=store,
            shot_id=args.shot,
            policy=policy,
            ledger=ledger,
            account=account,
            character=char_name,
            add_to_scene=add_scene,
        )
    except ShotAlreadySubmittedError as exc:
        print("NICHT GESENDET:", exc)
        return 3
    except FlowStoppedError as exc:
        print("GESTOPPT:", exc)
        return 2
    finally:
        await engine.close()
    print("fertig:" if ok else "nicht fertig (Pending-Marke prüfen):", args.out)
    return 0 if ok else 1


# ── Einstieg ─────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flow_pipeline", description=__doc__.splitlines()[0])
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Projektordner (flow_accounts.json, flow_state/)")
    p.add_argument("--account", default=None, help="Kontoname aus flow_accounts.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("balance").set_defaults(func=cmd_balance)

    c = sub.add_parser("check")
    c.add_argument("--a", required=True)
    c.add_argument("--b")
    c.set_defaults(func=cmd_check)

    s = sub.add_parser("sheet")
    s.add_argument("--video", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--times", default="0.3,2,4,6,7.7")
    s.set_defaults(func=cmd_sheet)

    m = sub.add_parser("morph")
    m.add_argument("--photo", required=True)
    m.add_argument("--toon", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--sheet")
    m.add_argument("--duration", type=float, default=8.0)
    m.set_defaults(func=cmd_morph)

    # character subcommands
    ch = sub.add_parser("character", help="Verwaltung nativer Google-Flow-Charaktere (0 Credits beim Upload)")
    ch_sub = ch.add_subparsers(dest="char_action", required=True)
    ch_sub.add_parser("list", help="Listet alle Charaktere im Projekt auf")
    ch_create = ch_sub.add_parser("create", help="Legt einen Charakter aus 1–2 Referenzbildern an (0 Credits)")
    ch_create.add_argument("--name", required=True, help="Name des Charakters (für @Name im Prompt)")
    ch_create.add_argument("--images", nargs="+", required=True, help="1 bis 2 Bildpfade (Turnaround / Portrait)")
    ch_create.add_argument("--desc", default=None, help="Optionale Textbeschreibung des Charakters")
    ch.set_defaults(func=cmd_character)

    # scene subcommands
    sc = sub.add_parser("scene", help="Szenen-Montage in Google Flow")
    sc_sub = sc.add_subparsers(dest="scene_action", required=True)
    sc_sub.add_parser("add", help="Fügt den neuesten Videoclip der aktuellen Szene hinzu")
    sc_sub.add_parser("open", help="Öffnet die Szenen-Ansicht in Flow")
    sc.set_defaults(func=cmd_scene)

    i = sub.add_parser("image")
    i.add_argument("--prompt", required=True)
    i.add_argument("--ref", action="append")
    i.add_argument("--out", required=True)
    i.add_argument("--character", help="Name des Flow-Charakters für @Mention-Konsistenz")
    i.add_argument("--same-composition", action="store_true")
    i.set_defaults(func=cmd_image)

    v = sub.add_parser("video")
    v.add_argument("--shot", required=True)
    v.add_argument("--frame", required=True)
    v.add_argument("--motion", required=True)
    v.add_argument("--out", required=True)
    v.add_argument("--character", help="Name des Flow-Charakters für @Mention-Konsistenz")
    v.add_argument("--add-to-scene", action="store_true", help="Fügt den fertigen Clip der Flow-Szene hinzu")
    v.add_argument("--ref", action="append", help="Zusatzreferenz hinter dem Startkader (Charakterkarte, Props-Karte)")
    v.add_argument("--seconds", type=float, default=flow_prompts.VEO_FAST_16_9_SECONDS)
    v.add_argument("--model", default="Veo 3.1 - Fast", help="Flow-Modell (z. B. 'Veo 3.1 - Fast', 'Veo 3.1 - Quality')")
    v.add_argument("--force", action="store_true", help="Ignoriert Format-Warnungen des Startbildes")
    v.add_argument("--max-clip", type=int, default=20)
    v.add_argument("--budget", type=int, default=None, help="Gesamtbudget dieses Laufs")
    v.add_argument("--reserve", type=int, default=0, help="Guthaben, das übrig bleiben muss")
    v.set_defaults(func=cmd_video)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = args.func(args)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    return int(result or 0)


if __name__ == "__main__":
    sys.exit(main())
