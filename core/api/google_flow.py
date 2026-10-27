"""core.api.google_flow — Google Flow Browser Automation Adapter

Ermoeglicht die Generierung von Videos (Veo 3.1 / Omni) und Bildern (Imagen 4 / Nano Banana)
ueber eine aktive Google Flow Browser-Sitzung unter Verwendung des Google AI Pro Kontingents.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from core.api.agnes_image import ImageOutput
from core.api.agnes_video import VideoOutput
from core.api.google_flow_errors import FlowPendingError, FlowStoppedError

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
FLOW_MCP_DIR = ROOT / "tools" / "google-flow-browser-mcp"
SERVER_SCRIPT = FLOW_MCP_DIR / "src" / "index.js"

# Logikcheck Befund 3: Der Node-Server wartet nach dem Absenden bis zu
# 120 s auf die Kostenkarte (agentResponseTimeoutMs) und danach bis zu 900 s
# auf das Rendern (videoGenerationTimeoutMs), plus Download. Ein kürzerer
# Timeout hier tötet den Prozess, NACHDEM die Guthabenpunkte genehmigt wurden —
# der Clip wäre bezahlt, aber verloren.
VIDEO_TIMEOUT_SECONDS = 1200.0
IMAGE_TIMEOUT_SECONDS = 180.0

# Antwortstatus ohne Datei: Flow hat nichts gestartet, Guthaben unberührt.
_STOPPED_STATUSES = {
    "cost_blocked",
    "cost_unreadable",
    "flow_unusual_activity",
    "decline_failed",
    "ready_for_confirmation",
}


def _get_node_executable() -> str:
    candidates = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        shutil.which("node"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return "node"


class GoogleFlowAPI:
    """Client fuer den lokalen Google Flow Browser-MCP-Server."""

    def __init__(self, node_exe: Optional[str] = None):
        self.node_exe = node_exe or _get_node_executable()
        self.server_script = str(SERVER_SCRIPT)

    async def _call_mcp_tool(self, tool_name: str, arguments: dict, timeout_seconds: float = 360.0) -> dict:
        """Ruft ein MCP-Tool auf dem Server via JSON-RPC Stdio auf."""
        cmd = [self.node_exe, self.server_script]

        logger.info(f"[GoogleFlow] Calling MCP tool '{tool_name}'...")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "video-generator-client", "version": "1.0.0"},
            },
        }

        initialized_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        call_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        try:
            # Sende initialize gefolgt von initialized notification und tool call
            payload = (
                json.dumps(init_req) + "\n"
                + json.dumps(initialized_notif) + "\n"
                + json.dumps(call_req) + "\n"
            ).encode("utf-8")
            proc.stdin.write(payload)
            await proc.stdin.drain()

            tool_result = None
            async def _read_response():
                nonlocal tool_result
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    txt = line.decode("utf-8", errors="replace").strip()
                    if not txt:
                        continue
                    try:
                        resp = json.loads(txt)
                        if resp.get("id") == 2:
                            if "error" in resp:
                                raise RuntimeError(f"[GoogleFlow] MCP tool error: {resp['error']}")
                            tool_result = resp.get("result", {})
                            break
                    except json.JSONDecodeError:
                        continue

            await asyncio.wait_for(_read_response(), timeout=timeout_seconds)
            try:
                proc.kill()
            except Exception:
                pass

        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            # Logikcheck Befund 3: Zum Zeitpunkt des Timeouts kann die
            # Generierung in Flow längst genehmigt und bezahlt sein. Als
            # „ausstehend“ melden, damit der Aufrufer NICHT neu abschickt.
            raise FlowPendingError(
                f"[GoogleFlow] Tool '{tool_name}' timed out after {timeout_seconds}s. "
                "Die Generierung kann in Flow bereits genehmigt sein — dort nachsehen, "
                "nicht erneut abschicken.",
                status="timeout",
            )
        except Exception as e:
            try:
                proc.kill()
            except Exception:
                pass
            raise RuntimeError(f"[GoogleFlow] Error executing MCP tool '{tool_name}': {e}")

        if not tool_result:
            raise RuntimeError(f"[GoogleFlow] No valid JSON-RPC result received for '{tool_name}'.")

        content_list = tool_result.get("content", [])
        if content_list and content_list[0].get("type") == "text":
            try:
                return json.loads(content_list[0].get("text", "{}"))
            except Exception:
                return {"text": content_list[0].get("text")}

        return tool_result

    async def connect(self) -> dict:
        """Verbindet mit der laufenden Chrome-Instanz."""
        return await self._call_mcp_tool("flow_connect", {"open_flow": True}, timeout_seconds=60.0)

    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        duration: int = 6,
        width: int = 1280,
        height: int = 720,
        model: str = "Veo 3.1 - Fast",
        output_folder: Optional[str] = None,
        **kwargs,
    ) -> VideoOutput:
        """Generiert ein Video mit Google Veo ueber Google Flow."""
        dur_str = f"{duration}s" if duration in [4, 6, 8, 10] else "6s"
        ratio = "9:16" if height > width else "16:9"

        args = {
            "prompt": prompt,
            "model": model,
            "duration": dur_str,
            "ratio": ratio,
            "auto_confirm": True,
        }
        if output_folder:
            args["output_folder"] = str(output_folder)
        if reference_image_paths:
            args["reference_images"] = [str(p) for p in reference_image_paths]

        logger.info(f"[GoogleFlow] Submitting video prompt: {prompt[:80]}... ({dur_str}, {ratio})")
        res = await self._call_mcp_tool(
            "flow_generate_video", args, timeout_seconds=VIDEO_TIMEOUT_SECONDS
        )

        files = res.get("files") or []
        if files:
            video_file = files[0]
            logger.info(f"[GoogleFlow] Video downloaded successfully: {video_file}")
            return VideoOutput(fmt="file", ext="mp4", data=video_file)

        self._raise_for_fileless_result("Video", res)

    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        size: Optional[str] = None,
        model: str = "Nano Banana 2",
        output_folder: Optional[str] = None,
        **kwargs,
    ) -> ImageOutput:
        """Generiert ein Bild mit Imagen / Nano Banana ueber Google Flow."""
        ratio = "1:1"
        if size:
            try:
                w, h = [int(x) for x in size.lower().split("x")]
                if w > h:
                    ratio = "16:9"
                elif h > w:
                    ratio = "9:16"
            except Exception:
                pass

        args = {
            "prompt": prompt,
            "model": model,
            "ratio": ratio,
            "auto_confirm": True,
        }
        if output_folder:
            args["output_folder"] = str(output_folder)
        if reference_image_paths:
            args["reference_images"] = [str(p) for p in reference_image_paths]

        logger.info(f"[GoogleFlow] Submitting image prompt: {prompt[:80]}... ({ratio})")
        res = await self._call_mcp_tool(
            "flow_generate_image", args, timeout_seconds=IMAGE_TIMEOUT_SECONDS
        )

        files = res.get("files") or []
        if files:
            image_file = files[0]
            logger.info(f"[GoogleFlow] Image downloaded successfully: {image_file}")
            return ImageOutput(fmt="file", ext="png", data=image_file)

        self._raise_for_fileless_result("Image", res)

    @staticmethod
    def _raise_for_fileless_result(kind: str, res: dict) -> None:
        """Übersetzt eine Antwort ohne Datei in den passenden Fehler.

        Logikcheck Befund 3: Ein Statusfeld wie ``cost_blocked`` heißt, dass
        Flow nichts gestartet hat (Stapel anhalten). Jede andere dateilose
        Antwort kann eine bezahlte, aber nicht abgeholte Generierung sein.

        Raises:
            FlowStoppedError: Flow hat nichts gestartet, Guthaben unberührt.
            FlowPendingError: Ergebnis unklar — in Flow nachsehen.
        """
        status = str(res.get("status") or "unknown")
        message = str(res.get("message") or "")[:300]
        if status in _STOPPED_STATUSES:
            raise FlowStoppedError(
                f"[GoogleFlow] {kind} not generated (status={status}): {message}",
                status=status,
            )
        raise FlowPendingError(
            f"[GoogleFlow] {kind} generation finished without downloadable file "
            f"(status={status}): {message}. In Flow nachsehen, nicht erneut abschicken.",
            status=status,
        )
