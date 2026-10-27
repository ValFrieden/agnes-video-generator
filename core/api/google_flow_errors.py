"""core.api.google_flow_errors — Gemeinsame Fehlerklassen der Google-Flow-Strecke.

Eigenes Modul, damit der MCP-Wrapper (``google_flow.py``) die Klassen ohne das
Playwright-Import der Engine (``google_flow_engine.py``) nutzen kann.

Leitregel der Flow-Strecke: **nach dem Absenden wird nie automatisch neu
abgeschickt.** Jede Generierung kostet Guthabenpunkte, deshalb unterscheiden die
Fehlerklassen, ob in Flow etwas angestoßen wurde oder nicht:

- ``FlowStoppedError``: Flow hat nichts gestartet (abgelehnt, Kosten über dem
  Limit, Kostenkarte unlesbar, Aktivitätswarnung). Guthaben ist unberührt, der
  Aufrufer soll den Stapel abbrechen.
- ``FlowPendingError``: Es wurde genehmigt oder könnte genehmigt worden sein,
  das Ergebnis ist aber unbekannt (Zeitüberschreitung, Download gescheitert).
  Guthaben ist womöglich verbraucht — nicht neu abschicken, sondern in Flow
  nachsehen.
"""

from __future__ import annotations


class FlowError(RuntimeError):
    """Basisklasse aller Google-Flow-Fehler."""


class FlowStoppedError(FlowError):
    """Flow hat die Generierung nicht gestartet — Guthaben unberührt.

    Args:
        message: Klartextmeldung für Log und Aufrufer.
        status: Kennung des Abbruchgrunds, etwa ``cost_blocked``,
            ``cost_unreadable``, ``flow_unusual_activity``, ``decline_failed``.
    """

    def __init__(self, message: str, status: str = "stopped"):
        super().__init__(message)
        self.status = status


class FlowPendingError(FlowError):
    """Generierung läuft/lief in Flow, das Ergebnis ist hier unbekannt.

    Args:
        message: Klartextmeldung für Log und Aufrufer.
        status: Kennung der Ursache, etwa ``timeout`` oder ``download_failed``.
    """

    def __init__(self, message: str, status: str = "pending"):
        super().__init__(message)
        self.status = status
