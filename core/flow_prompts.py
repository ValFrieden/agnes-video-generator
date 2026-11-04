"""core/flow_prompts.py — Prompt-Vorlagen für den Flow-Agenten.

Flow entscheidet im Agenten-Chat selbst, ob es ein Bild (Nano Banana) oder ein
Video (Veo) erzeugt, und zwar aus dem Prompt-Text. Ein eindeutiger Anfang
(„Generate one image (not a video)“ bzw. „Generate a video with Veo 3.1 Fast, N
seconds, 16:9“) verhindert, dass der Agent die falsche Art wählt oder nachfragt.

Live gelernt (Konto-Tarif „Google AI Pro“): Veo 3.1 Fast erzeugt in 16:9 **nur
8 Sekunden**. Eine Anfrage über 6 s führte zu einer Rückfrage statt zur
Kostenkarte. ``normalize_duration`` biegt das vor dem Absenden gerade; die
Clips werden danach im Schnitt gekürzt (kein Beschleunigen).
"""

from __future__ import annotations

from typing import Optional

# Globaler Stil und Negativliste dieser Produktion (aus dem Drehbuch)
STYLE_BLOCK = (
    "Stylized 3D animated feature film look, soft rounded shapes, expressive large eyes, "
    "warm golden hour light, soft bloom, pastel spring palette of white birch, fresh green and lilac, "
    "consistent character design, high detail, no text, no watermark."
)
ONE_CHARACTER = "Only one character in the scene, no other people."
NEGATIVE = (
    "no other people, no crowd, no text, no letters, no watermark, no extra fingers, "
    "no face distortion, no fast camera spin"
)

# Dauer, die der Tarif für Veo 3.1 Fast in 16:9 erlaubt (live bestätigt)
VEO_FAST_16_9_SECONDS = 8


def normalize_duration(requested: float, allowed: int = VEO_FAST_16_9_SECONDS) -> int:
    """Gibt die buchbare Dauer zurück: der Tarif kennt nur ``allowed`` Sekunden.

    Kürzere Wünsche werden im Schnitt gekürzt (kein Beschleunigen); längere
    brauchen mehrere Clips (``clips_needed``).
    """
    if requested <= 0:
        raise ValueError("Dauer muss positiv sein")
    return allowed


def clips_needed(seconds: float, allowed: int = VEO_FAST_16_9_SECONDS) -> int:
    """Wie viele Clips für ``seconds`` Länge gebucht werden müssen."""
    if seconds <= 0:
        raise ValueError("Dauer muss positiv sein")
    return -(-int(round(seconds * 1000)) // (allowed * 1000))


def image_prompt(
    description: str,
    same_composition_as_reference: bool = False,
    character: Optional[str] = None,
) -> str:
    """Bild-Prompt mit eindeutigem Anfang.

    Args:
        description: Inhalt des Bildes.
        same_composition_as_reference: Für Morphing-Paare: nur der Stil darf sich
            ändern, Pose, Maßstab und Hintergrund bleiben (``flow_frames`` prüft das).
        character: Optionaler Flow-Charaktername für @Mention-Konsistenz.
    """
    parts = ["Generate one image (not a video), 16:9 landscape widescreen."]
    if character:
        parts.append(
            f"Featuring @{character}. Maintain @{character}'s exact facial identity, appearance, and signature styling."
        )
    if same_composition_as_reference:
        parts.append(
            "Keep the EXACT same composition as the attached reference: same position and scale in the frame, "
            "same head tilt and gaze direction, same pose, same background. Only the rendering style changes."
        )
    parts.append(description.strip())
    parts.append(f"{ONE_CHARACTER} {STYLE_BLOCK}")
    return " ".join(parts)


def video_prompt(
    motion: str,
    seconds: float = VEO_FAST_16_9_SECONDS,
    model: str = "Veo 3.1 Fast",
    start_frame_attached: bool = True,
    extra_refs: int = 0,
    character: Optional[str] = None,
) -> str:
    """Video-Prompt: beschreibt nur Bewegung, Kamera, Licht (Regel aus dem Drehbuch)."""
    secs = normalize_duration(seconds)
    parts = [f"Generate a video with {model}, {secs} seconds, 16:9 landscape."]
    if start_frame_attached:
        parts.append("Use the FIRST attached image as the start frame.")
    if character:
        parts.append(
            f"Featuring @{character}. Maintain @{character}'s exact facial identity, appearance, and signature styling throughout the scene."
        )
    elif extra_refs:
        parts.append(
            "The other attached image(s) are character/props reference sheets: keep her full outfit "
            "(light sky-blue button-up shirt with rolled sleeves, jeans, white sneakers), body proportions "
            "and every prop exactly as on the sheet, in every part of the clip, also below the waist and from behind."
        )
    parts.append(motion.strip())
    parts.append("Keep her face and proportions natural, no distortion.")
    parts.append(f"{STYLE_BLOCK} {ONE_CHARACTER}")
    return " ".join(parts)


def is_video_prompt(prompt: str) -> bool:
    return prompt.lstrip().lower().startswith("generate a video")


def is_image_prompt(prompt: str) -> bool:
    return prompt.lstrip().lower().startswith("generate one image")


def validate_prompt(prompt: str, kind: Optional[str] = None) -> Optional[str]:
    """Gibt einen Hinweis zurück, wenn der Prompt den Agenten verwirren kann, sonst ``None``."""
    if not (is_video_prompt(prompt) or is_image_prompt(prompt)):
        return "Prompt beginnt weder mit 'Generate a video…' noch mit 'Generate one image…'"
    if kind == "video" and not is_video_prompt(prompt):
        return "erwartet Video-Prompt"
    if kind == "image" and not is_image_prompt(prompt):
        return "erwartet Bild-Prompt"
    return None
