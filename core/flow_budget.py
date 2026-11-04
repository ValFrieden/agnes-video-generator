"""core/flow_budget.py — Budget-Policy, Credit-Journal und Konten für Google Flow.

Ersetzt das Nachfragen „Darf ich diese Generierung genehmigen?“ durch feste
Regeln, die jede Generierung automatisch prüft:

- ``BudgetPolicy``: Limit pro Clip, Gesamtbudget des Laufs und Reserve, die auf
  dem Konto bleiben muss. Wer die Regeln verletzt, bekommt keine Genehmigung
  (der Aufrufer lehnt die Kostenkarte ab).
- ``CreditLedger``: Journal (eine JSON-Zeile pro Ereignis) mit Konto, Shot,
  Guthabenpunkten und, wenn lesbar, Kontostand vor und nach der Generierung.
- ``FlowAccounts``: Konten und Projekte (``/u/<Index>/project/<ID>``) aus einer
  Konfigurationsdatei statt aus Einmal-Skripten.

Bewusst bleibt der Grundsatz der Engine bestehen: genehmigt wird nur einmalig
(„Genehmigen“), nie „Immer genehmigen“.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BudgetPolicy:
    """Regeln, unter denen eine Kostenkarte automatisch genehmigt werden darf.

    Attributes:
        per_clip_max: Höchstpreis einer einzelnen Generierung.
        session_budget: Gesamtbudget dieses Laufs (``None`` = unbegrenzt).
        reserve: Guthaben, das nach der Generierung mindestens bleiben muss.
    """

    per_clip_max: int = 20
    session_budget: Optional[int] = None
    reserve: int = 0

    def check(self, cost: int, spent: int = 0, balance: Optional[int] = None) -> Optional[str]:
        """Gibt ``None`` zurück, wenn erlaubt, sonst den Grund der Ablehnung."""
        if cost > self.per_clip_max:
            return f"Preis {cost} über dem Limit pro Clip ({self.per_clip_max})"
        if self.session_budget is not None and spent + cost > self.session_budget:
            return (
                f"Gesamtbudget überschritten: {spent} bereits ausgegeben + {cost} "
                f"> {self.session_budget}"
            )
        if balance is not None and balance - cost < self.reserve:
            return f"Reserve unterschritten: Kontostand {balance} - {cost} < {self.reserve}"
        return None


class CreditLedger:
    """Anhängendes Journal (JSON Lines) der Guthaben-Ereignisse."""

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)

    def record(
        self,
        action: str,
        credits: int,
        account: str = "default",
        shot_id: Optional[str] = None,
        balance_before: Optional[int] = None,
        balance_after: Optional[int] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        entry = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "account": account,
            "shot": shot_id,
            "action": action,  # "approved" | "blocked" | "balance"
            "credits": int(credits),
            "balance_before": balance_before,
            "balance_after": balance_after,
            "note": note,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def entries(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue  # halb geschriebene Zeile überspringen, nicht abstürzen
        return out

    def spent(self, account: Optional[str] = None) -> int:
        """Summe der genehmigten Guthabenpunkte (optional je Konto)."""
        return sum(
            e["credits"]
            for e in self.entries()
            if e.get("action") == "approved" and (account is None or e.get("account") == account)
        )

    def last_balance(self, account: str = "default") -> Optional[int]:
        """Letzter bekannter Kontostand eines Kontos."""
        for e in reversed(self.entries()):
            if e.get("account") == account and e.get("balance_after") is not None:
                return int(e["balance_after"])
        return None


class FlowAccounts:
    """Konten und Projekte aus einer Konfigurationsdatei.

    Format ``flow_accounts.json``::

        {"default": "second",
         "accounts": {"second": {"index": 3, "project": "0559cf6d-...",
                                  "note": "1050 Credits"}}}
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._accounts: Dict[str, Dict[str, Any]] = data.get("accounts", {})
        if not self._accounts:
            raise ValueError("flow_accounts: kein Konto definiert")

    @classmethod
    def load(cls, path: str | os.PathLike) -> "FlowAccounts":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def default_name(self) -> str:
        name = self._data.get("default") or next(iter(self._accounts))
        if name not in self._accounts:
            raise KeyError(f"Standardkonto '{name}' nicht definiert")
        return name

    def get(self, name: Optional[str] = None) -> Dict[str, Any]:
        key = name or self.default_name
        try:
            return self._accounts[key]
        except KeyError:
            raise KeyError(f"Konto '{key}' nicht definiert") from None

    def project_url(self, name: Optional[str] = None) -> str:
        acc = self.get(name)
        index, project = acc.get("index"), acc.get("project")
        if index is None or not project:
            raise ValueError(f"Konto '{name or self.default_name}': index und project sind Pflicht")
        return f"https://flow.google.com/u/{int(index)}/project/{project}"
