"""core/flow_shot_state.py — Zustandsdatei der Flow-Szenen (``shots.json``).

Bisher lebten Status, Preise und Clip-Pfade nur im Chat und in Einmal-Skripten.
Nach einem Abbruch oder Kontextverlust musste alles neu rekonstruiert werden,
und ein zweites Absenden desselben Shots (kostet erneut Guthaben) war nur durch
Aufpassen verhindert.

Diese Datei hält je Shot: Status, Version, Eingangsbilder, Promptprüfsumme,
Guthabenpunkte, Clip-Pfad und Verlauf. Geschrieben wird atomar (Temp-Datei +
``os.replace``), damit ein Absturz mitten im Schreiben die Datei nie halb lässt.

Regel gegen doppelte Kosten: ``guard_submit`` wirft, sobald der Shot einmal
angefragt wurde. Erst ``new_version`` (nach Prüfung in Flow) gibt ihn wieder frei.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class ShotStatus(IntEnum):
    """Reihenfolge der Stationen eines Shots; höher = weiter."""

    PLANNED = 0
    KEYFRAME_READY = 1
    REQUESTED = 2  # Prompt abgeschickt, Kosten ggf. noch nicht genehmigt
    APPROVED = 3  # Kostenkarte einmalig genehmigt: ab hier fallen Kosten an
    RENDERED = 4
    DOWNLOADED = 5


class ShotAlreadySubmittedError(RuntimeError):
    """Der Shot wurde in dieser Version schon abgeschickt — nicht erneut senden."""

    def __init__(self, shot_id: str, status: ShotStatus, version: int):
        self.shot_id = shot_id
        self.status = status
        self.version = version
        super().__init__(
            f"Shot '{shot_id}' (Version {version}) steht auf {status.name}; "
            "erneutes Absenden würde erneut Guthaben kosten. Ergebnis in Flow prüfen, "
            "danach new_version() aufrufen."
        )


def prompt_hash(prompt: str) -> str:
    """Kurze Prüfsumme eines Prompts, um Änderungen zu erkennen."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]


class ShotStateStore:
    """Dateibasierter Speicher für den Zustand aller Shots eines Projekts."""

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)

    # ── Datei ────────────────────────────────────────────────────────────────

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"shots": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"Zustandsdatei '{self.path}' nicht lesbar: {exc}") from exc
        data.setdefault("shots", {})
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ── Lesen ────────────────────────────────────────────────────────────────

    @staticmethod
    def _blank(shot_id: str) -> Dict[str, Any]:
        return {
            "id": shot_id,
            "status": ShotStatus.PLANNED.name,
            "version": 1,
            "history": [],
        }

    def get(self, shot_id: str) -> Dict[str, Any]:
        """Liefert den Datensatz (leer-neu, wenn der Shot noch nicht existiert)."""
        return dict(self._load()["shots"].get(shot_id) or self._blank(shot_id))

    def status(self, shot_id: str) -> ShotStatus:
        return ShotStatus[self.get(shot_id)["status"]]

    def all(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._load()["shots"])

    def total_credits(self, shot_ids: Optional[Iterable[str]] = None) -> int:
        """Summe der genehmigten Guthabenpunkte (über alle Versionen)."""
        total = 0
        for sid, rec in self._load()["shots"].items():
            if shot_ids is not None and sid not in set(shot_ids):
                continue
            total += sum(int(h.get("credits") or 0) for h in rec.get("history", []))
        return total

    # ── Schreiben ────────────────────────────────────────────────────────────

    def update(self, shot_id: str, **fields: Any) -> Dict[str, Any]:
        """Setzt beliebige Felder (Statuswechsel nur über ``advance``)."""
        if "status" in fields:
            raise ValueError("Status nur über advance() ändern.")
        data = self._load()
        rec = data["shots"].setdefault(shot_id, self._blank(shot_id))
        rec.update(fields)
        rec["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save(data)
        return dict(rec)

    def advance(self, shot_id: str, status: ShotStatus, **fields: Any) -> Dict[str, Any]:
        """Setzt den Status vorwärts. Rückwärts nur über ``new_version``.

        Gleicher Status ist erlaubt (idempotent, z. B. nach Wiederholung der
        Meldung), ein niedrigerer wirft ``ValueError``.
        """
        data = self._load()
        rec = data["shots"].setdefault(shot_id, self._blank(shot_id))
        current = ShotStatus[rec["status"]]
        if status < current:
            raise ValueError(
                f"Shot '{shot_id}': {current.name} → {status.name} geht rückwärts; new_version() nutzen."
            )
        rec["status"] = status.name
        rec.update(fields)
        entry = {"status": status.name, "version": rec["version"], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if "credits" in fields:
            entry["credits"] = fields["credits"]
        rec.setdefault("history", []).append(entry)
        rec["updated_at"] = entry["at"]
        self._save(data)
        return dict(rec)

    def new_version(self, shot_id: str, reason: str = "") -> Dict[str, Any]:
        """Startet eine neue Version (z. B. nach Neuanforderung) und gibt den Shot frei."""
        data = self._load()
        rec = data["shots"].setdefault(shot_id, self._blank(shot_id))
        rec["version"] = int(rec.get("version", 1)) + 1
        rec["status"] = ShotStatus.PLANNED.name
        rec.setdefault("history", []).append(
            {
                "status": "NEW_VERSION",
                "version": rec["version"],
                "reason": reason,
                "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        )
        rec["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save(data)
        return dict(rec)

    def guard_submit(self, shot_id: str) -> None:
        """Wirft ``ShotAlreadySubmittedError``, wenn der Shot schon angefragt wurde."""
        rec = self.get(shot_id)
        status = ShotStatus[rec["status"]]
        if status >= ShotStatus.REQUESTED:
            raise ShotAlreadySubmittedError(shot_id, status, int(rec["version"]))
