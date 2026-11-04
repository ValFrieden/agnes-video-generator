#!/usr/bin/env python3
"""scripts/modelscope_p0_check.py — P0-Validierung: ModelScope API-Inference (Video)

Gehört zu docs/plans/v7.4/free_multi_provider_plan.md (§五 P0 / §八 Messprotokoll).

Stufen (kumulativ):
  1. immer:          Erreichbarkeit/Latenz + Routen-Probe (401/400/500-auth =
                     Route existiert, 404 = existiert nicht)
  2. --token:        authentifizierter Modellkatalog (gibt es Video-Modelle?) +
                     Schema-Probe (leerer Submit — der Fehlerbody dokumentiert i.
                     d. R. die erwarteten Request-Felder)
  3. --submit:       EIN echter Text-to-Video-Task (verbraucht Gratis-Quota!),
                     inkl. Polling bis Abschluss
  4. --submit-i2v:   EIN echter Image-to-Video-Task (First-Frame-URL via --image-url)

Token: modelscope.cn → Konto → Access Tokens (Format ``ms-…``).
**Wichtig — zwei getrennte Portale (P0-Befund 2026-10-10):**
  - international: Token auf **modelscope.ai** erstellt → Host ``api-inference.modelscope.ai``
    (Default hier); Konto muss zusätzlich einen **Alibaba-Cloud-Account gebunden** haben,
    sonst: ``"Please bind your Alibaba Cloud account before use"`` (Bindung:
    https://modelscope.ai/my/settings/account)
  - China: Token auf **modelscope.cn** erstellt → ``--base https://api-inference.modelscope.cn``
env: MODELSCOPE_API_TOKEN oder MODELSCOPE_TOKEN.

Bewusst stdlib-only (urllib, kein requests) — läuft auf jedem Python ohne Installation.
Rohantworten landen in --out (Default: docs/plans/v7.4/p0_modelscope_logs/).

Beispiele:
  python scripts/modelscope_p0_check.py
  python scripts/modelscope_p0_check.py --token ms-xxx
  python scripts/modelscope_p0_check.py --token ms-xxx --submit
  python scripts/modelscope_p0_check.py --token ms-xxx --submit-i2v --image-url https://example.com/frame.png
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api-inference.modelscope.ai"  # Default: internationales Portal; CN-Tokens via --base

# Bekannte Rate-Limit-Header (ImageForge-README + P0-Beobachtung)
RATE_HEADERS = (
    "modelscope-ratelimit-requests-remaining",
    "modelscope-ratelimit-model-requests-remaining",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-remaining-tokens",
)

VIDEO_KEYWORDS = ("wan", "video", "t2v", "i2v", "animate", "seedance", "ltx", "mochi", "cogvideo")

# Submit-Kandidaten, falls der Katalog keine Video-Modelle listet (P0-Fall):
# Reihenfolge = Versuchreihenfolge bei --submit; erster Treffer gewinnt.
DEFAULT_T2V_CANDIDATES = [
    "Wan-AI/Wan2.2-T2V-A14B",
    "Wan-AI/Wan2.1-T2V-14B",
    "Wan-AI/Wan2.1-T2V-1.3B",
    "Wan-AI/wan2.2-t2v-plus",
    "Wan-AI/wan2.1-t2v-plus",
]
DEFAULT_I2V_CANDIDATES = [
    "Wan-AI/Wan2.2-I2V-A14B",
    "Wan-AI/Wan2.1-I2V-14B",
    "Wan-AI/wan2.2-i2v-plus",
    "Wan-AI/wan2.1-i2v-plus",
]

DEFAULT_PROMPT = (
    "A red balloon drifting slowly over old European rooftops at golden hour, cinematic"
)


class Resp:
    """Minimal-Response-Shim über urllib (Status, Header, Text, JSON)."""

    def __init__(self, status_code: int, headers: dict, text: str, elapsed: float):
        self.status_code = status_code
        self.status = status_code  # Alias
        self.headers = headers
        self.text = text
        self.elapsed = elapsed

    def json(self):
        return json.loads(self.text)


def _request(method: str, url: str, token: str = "", payload=None, timeout: float = 30) -> Resp:
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return Resp(r.status, dict(r.headers), r.read().decode("utf-8", "replace"),
                        time.perf_counter() - t0)
    except urllib.error.HTTPError as e:  # 4xx/5xx → Body trotzdem lesbar
        return Resp(e.code, dict(e.headers), e.read().decode("utf-8", "replace"),
                    time.perf_counter() - t0)


def _log(msg: str) -> None:
    print(msg, flush=True)


def _ratelimit(resp: Resp) -> dict:
    low = {k.lower(): v for k, v in resp.headers.items()}
    return {h: low[h] for h in RATE_HEADERS if low.get(h) is not None}


def _dump(out_dir: Path, name: str, resp: Resp) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.json"
    try:
        body = json.dumps(resp.json(), ensure_ascii=False, indent=2)
    except ValueError:
        body = resp.text
    path.write_text(
        f"HTTP {resp.status_code}\n\n"
        + "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
        + "\n\n"
        + body,
        encoding="utf-8",
    )
    _log(f"  [raw -> {path}]")


def _find_video_urls(obj, hits=None):
    """Schema-agnostisch: alle Strings, die nach Video-URL aussehen, einsammeln."""
    if hits is None:
        hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith(("http://", "https://")) and (
                ".mp4" in v.lower() or "video" in k.lower()
            ):
                hits.append((k, v))
            else:
                _find_video_urls(v, hits)
    elif isinstance(obj, list):
        for item in obj:
            _find_video_urls(item, hits)
    return hits


def _extract_task_id(body: dict):
    """task_id finden (bekannte Layouts: top-level / output / data; sonst 'id')."""
    for container in (body, body.get("output") or {}, body.get("data") or {}):
        if isinstance(container, dict):
            for key in ("task_id", "taskId", "request_id", "id"):
                val = container.get(key)
                if isinstance(val, str) and val:
                    return val
    return None


def _extract_status(body: dict):
    for container in (body, body.get("output") or {}, body.get("data") or {}):
        if isinstance(container, dict):
            for key in ("task_status", "status"):
                val = container.get(key)
                if isinstance(val, str) and val:
                    return val.upper()
    return ""


def step_reachability() -> None:
    _log("== Stufe 1a: Erreichbarkeit/Latenz (ohne Token) ==")
    for _ in range(2):
        resp = _request("GET", f"{BASE}/v1/models")
        _log(f"  GET /v1/models -> HTTP {resp.status_code} in {resp.elapsed:.2f}s"
             f"  rate-limit: {_ratelimit(resp) or '-'}")


def step_routes(token: str, out_dir: Path) -> None:
    _log("== Stufe 1b: Routen-Probe (401/400/500-auth = existiert, 404 = fehlt) ==")
    probes = [
        ("GET", "/v1/models"),
        ("POST", "/v1/chat/completions"),
        ("POST", "/v1/images/generations"),
        ("POST", "/v1/videos/generations"),
        ("GET", "/v1/tasks/nonexistent-p0-probe"),
        ("POST", "/v1/videos"),
        ("GET", "/v1/tasks"),
    ]
    for method, path in probes:
        try:
            resp = _request(method, f"{BASE}{path}", token=token,
                            payload={} if method == "POST" else None, timeout=20)
        except (urllib.error.URLError, OSError) as exc:
            _log(f"  {method:4} {path:38} -> FEHLER {exc}")
            continue
        _log(f"  {method:4} {path:38} -> HTTP {resp.status_code}")
        if resp.status_code != 404 and path != "/v1/models":
            _dump(out_dir, "route" + path.replace("/", "_"), resp)


def step_catalog(token: str, out_dir: Path) -> list:
    _log("== Stufe 2a: authentifizierter Modellkatalog ==")
    resp = _request("GET", f"{BASE}/v1/models", token=token)
    _dump(out_dir, "models_authed", resp)
    try:
        ids = [m.get("id", "") for m in (resp.json().get("data") or [])]
    except ValueError:
        _log(f"  Katalog nicht parsebar: {resp.text[:200]}")
        return []
    _log(f"  Modelle gesamt: {len(ids)}")
    video_models = [i for i in ids if any(k in i.lower() for k in VIDEO_KEYWORDS)]
    _log(f"  Video-Kandidaten im Katalog: {video_models or 'KEINE'}")
    return video_models


def step_schema_probe(token: str, out_dir: Path) -> None:
    _log("== Stufe 2b: Schema-Probe (leerer Submit; Fehlerbody dokumentiert Felder) ==")
    resp = _request("POST", f"{BASE}/v1/videos/generations", token=token, payload={}, timeout=60)
    _log(f"  POST /v1/videos/generations (leer) -> HTTP {resp.status_code}")
    _log(f"  Body: {resp.text[:500]}")
    _dump(out_dir, "schema_probe_empty", resp)


def _poll_until_done(token: str, out_dir: Path, label: str, task_id: str,
                     poll_interval: int, timeout: int) -> bool:
    """Task beobachten bis SUCCEEDED/FAILED/Timeout; True nur bei fertigen Video-URLs."""
    t0 = time.perf_counter()
    deadline = time.monotonic() + timeout
    last_status = ""
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        poll = _request("GET", f"{BASE}/v1/tasks/{task_id}", token=token, timeout=30)
        try:
            poll_body = poll.json()
        except ValueError:
            poll_body = {}
        status = _extract_status(poll_body)
        if status != last_status:
            _log(f"  [{time.perf_counter() - t0:6.0f}s] status={status or '?'}"
                 f"  http={poll.status_code}  rate-limit: {_ratelimit(poll) or '-'}")
            last_status = status
        if status in ("SUCCEEDED", "COMPLETED"):
            urls = _find_video_urls(poll_body)
            _log(f"  FERTIG nach {time.perf_counter() - t0:.0f}s. "
                 f"Video-URLs: {urls or 'keine erkannt'}")
            _dump(out_dir, f"{label}_result", poll)
            return bool(urls)
        if status in ("FAILED", "CANCELED", "CANCELLED", "UNKNOWN"):
            _log(f"  Task fehlgeschlagen: {poll.text[:400]}")
            _dump(out_dir, f"{label}_result", poll)
            return False
    _log(f"  Timeout nach {timeout}s (letzter Status: {last_status or '?'})")
    return False


def _submit_and_poll(token: str, out_dir: Path, kind: str, payload: dict,
                     poll_interval: int, timeout: int) -> bool:
    label = f"{kind}_{int(time.time())}"
    resp = _request("POST", f"{BASE}/v1/videos/generations", token=token,
                    payload=payload, timeout=90)
    _log(f"  Submit ({kind}, model={payload.get('model')}) -> HTTP {resp.status_code}"
         f" in {resp.elapsed:.2f}s")
    _dump(out_dir, f"{label}_submit", resp)
    try:
        body = resp.json()
    except ValueError:
        _log("  Kein JSON — Abbruch.")
        return False
    if resp.status_code >= 400:
        _log(f"  Submit fehlgeschlagen: {resp.text[:300]}")
        return False
    task_id = _extract_task_id(body)
    if not task_id:
        _log(f"  Keine task_id erkannt — Body ansehen: {str(body)[:400]}")
        return False
    _log(f"  task_id = {task_id}")
    return _poll_until_done(token, out_dir, label, task_id, poll_interval, timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="https://api-inference.modelscope.ai",
                        help="API-Host (Default: internationales Portal .ai; "
                             "CN-Portal-Tokens: https://api-inference.modelscope.cn)")
    parser.add_argument("--token", default="", help="ModelScope-Token (ms-…); sonst env")
    parser.add_argument("--submit", action="store_true",
                        help="EIN echtes T2V-Task ausführen (verbraucht Gratis-Quota)")
    parser.add_argument("--submit-i2v", action="store_true",
                        help="EIN echtes I2V-Task ausführen (braucht --image-url)")
    parser.add_argument("--image-url", default="",
                        help="öffentliche First-Frame-URL für --submit-i2v")
    parser.add_argument("--poll-task", default="",
                        help="bereits eingereichte task_id nur weiter beobachten (kein neuer Submit)")
    parser.add_argument("--model", default="",
                        help="Modell-Id erzwingen (sonst Kandidatenliste)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Test-Prompt")
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=900, help="Polling-Timeout in s")
    parser.add_argument("--out", default=str(
        Path(__file__).resolve().parent.parent / "docs" / "plans" / "v7.4" / "p0_modelscope_logs"))
    args = parser.parse_args()

    out_dir = Path(args.out)
    global BASE
    BASE = args.base.rstrip("/")
    token = (args.token or os.environ.get("MODELSCOPE_API_TOKEN")
             or os.environ.get("MODELSCOPE_TOKEN") or "").strip()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows-Konsole
    except AttributeError:
        pass

    step_reachability()
    step_routes(token, out_dir)

    catalog_video_models: list = []
    if token:
        catalog_video_models = step_catalog(token, out_dir)
        step_schema_probe(token, out_dir)
    else:
        _log("== Stufen 2-4 übersprungen: kein Token (--token oder MODELSCOPE_API_TOKEN) ==")
        _log("   Token: modelscope.cn → Konto → Access Tokens (Format ms-…)")

    if token and args.poll_task:
        _log(f"== Poll-only: Task {args.poll_task} ==")
        done = _poll_until_done(token, out_dir, "pollonly", args.poll_task,
                                args.poll_interval, args.timeout)
        _log(f"== Ende ({'OK' if done else 'nicht abgeschlossen'}) — Rohdaten: {out_dir} ==")
        return 0 if done else 1

    ok = True
    if token and args.submit:
        _log("== Stufe 3: echter T2V-Task ==")
        model = args.model or (catalog_video_models or DEFAULT_T2V_CANDIDATES)[0]
        ok &= _submit_and_poll(
            token, out_dir, "t2v", {"model": model, "prompt": args.prompt},
            args.poll_interval, args.timeout,
        )
    if token and args.submit_i2v:
        _log("== Stufe 4: echter I2V-Task ==")
        if not args.image_url:
            _log("  --submit-i2v braucht --image-url (öffentlich erreichbare First-Frame-URL)")
            return 2
        model = args.model or (catalog_video_models or DEFAULT_I2V_CANDIDATES)[0]
        # Schema der Bild-Referenz ist (noch) nicht verifiziert — beide gängigen Varianten
        # mitschicken; der Fehler-/Erfolgsbody zeigt, welche greift:
        payload = {
            "model": model,
            "prompt": args.prompt,
            "image_url": args.image_url,
            "input": {"image_url": args.image_url},
        }
        ok &= _submit_and_poll(
            token, out_dir, "i2v", payload, args.poll_interval, args.timeout,
        )

    _log(f"== Ende ({'OK' if ok else 'mit Fehlern'}) — Rohdaten: {out_dir} ==")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
