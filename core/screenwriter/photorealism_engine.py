"""core.screenwriter.photorealism_engine — Photorealism & Multi-Reference Anti-Plastic Engine.

Inspiriert durch die kuratierte KI-Wissensdatenbank (D:\\SD\\My\\AI):
- "Оживить картину и себя в ней" (Multi-Reference Identity & Scene Transfer Blueprint)
- "Реализм в фэнтези / Nano Banana 2" (Anti-Plastik & Kamera-Optik-Parameter)
- "Улучшатель промптов" (Strukturierte 3-Tier Video Action Schemata)

Bietet produktionsreife Prompt-Kompilierung für Video- und Bildmodelle (Veo 3.1, Google Flow,
Seedance 2.0, Midjourney, Kling, Agnes Image 2.5).
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LensPreset(str, Enum):
    CINEMATIC_35MM = "shot on ARRI Alexa 35, 35mm anamorphic prime lens, f/1.8, ISO 400, cinematic depth of field"
    PORTRAIT_50MM = "shot on Hasselblad H6D-100c, 50mm f/2.0 portrait prime lens, natural bokeh, ISO 200"
    TELEPHOTO_85MM = "shot on RED V-Raptor XL, 85mm f/1.4 cine lens, subtle background compression, ISO 800"
    DOCUMENTARY_RAW = "shot on Sony FX6, 24-70mm GM II lens, natural handheld documentary framing, ISO 640"
    VINTAGE_ANAMORPHIC = "shot on Panavision C-Series anamorphic lens, subtle horizontal streak, vintage amber warmth, ISO 500"


class OpticalArtifacts:
    SUBTLE_CINE = "subtle lens flare, gentle natural vignetting, minimal chromatic aberration, unretouched raw footage, zero digital plastic smoothing"
    HARSH_LIGHT = "hard flash illumination, sharp dramatic shadows, rim light separation, high dynamic range highlights"
    FILM_TEXTURE = "organic 35mm film grain, fine sensory texture, no synthetic AI gloss, unsharpened authentic sensor noise"


class PhysicalRealityTokens:
    HUMAN_DETAILS = (
        "authentic skin pores, natural facial texture, subtle sweat sheen, fine peach fuzz, "
        "uneven natural tan, micro-wrinkles around eyes, natural lip texture, closed mouth"
    )
    ENVIRONMENT_PHYSICS = (
        "floating micro dust motes drifting in light beams, natural fabric tension and crumpling "
        "under gravity, subtle wind-blown hair strands, atmospheric depth, realistic light falloff"
    )
    ACTOR_ON_SET_FRAMING = (
        "actor in authentic practical costume on real physical movie set, candid cinematic "
        "backstage perspective, naturalistic blocking, no stylized illustration"
    )


@dataclass
class IdentityTransferSpec:
    """Spezifikation für Multi-Reference Face/Identity Transfer (2-Referenz-Prinzip)."""
    character_name: str
    identity_features: str  # Gesicht, Augenfarbe, Haarstruktur, Bart, Muttermale
    scene_costume_and_style: str  # Kostüm, Beleuchtung, Farbstil aus Referenz 1
    shot_types: List[str] = field(default_factory=lambda: [
        "Shot 1: close-up of the face, front view (anfas)",
        "Shot 2: close-up of the face, three-quarter view",
        "Shot 3: full body view, front pose",
        "Shot 4: full body view, dynamic profile"
    ])


class PhotorealismEngine:
    """Zentrale Engine für konsistente, fotorealistische und anti-plastische Prompts."""

    def __init__(self, default_lens: LensPreset = LensPreset.CINEMATIC_35MM):
        self.default_lens = default_lens

    @staticmethod
    def format_identity_transfer_prompt(spec: IdentityTransferSpec) -> str:
        """Kompiliert den bewährten Multi-Reference Identity Transfer Blueprint.
        
        Referenz 1 = Gemälde / Szene / Beleuchtungs- und Kostümstil
        Referenz 2 = Charakter-Identität (Gesichtsmerkmale, Proportionen)
        """
        shots_formatted = ". ".join(spec.shot_types)
        prompt = (
            f"Keep the exact face, facial structure and immutable identity of {spec.character_name} "
            f"from Reference 2 ({spec.identity_features}). "
            f"Transfer onto them the costume, environmental lighting, texture and visual style from Reference 1 "
            f"({spec.scene_costume_and_style}). "
            f"Strict photorealism, high detail, {PhysicalRealityTokens.HUMAN_DETAILS}. "
            f"{shots_formatted}."
        )
        return prompt.strip()

    @staticmethod
    def format_three_tier_action_prompt(
        characters_desc: str,
        environment_desc: str,
        action_and_camera_desc: str,
        duration_s: float = 5.0,
        subtle_micro_motion: Optional[str] = None,
        lens: Optional[LensPreset] = None
    ) -> str:
        """Kompiliert das strukturierte 3-Tier Video Action Prompt Schema.
        
        Aufteilung in CHARACTERS, ENVIRONMENT und ACTION & CAMERA garantiert
        stabile Interpretation durch Videomodelle (Veo, Flow, Kling, Wan).
        """
        lens_text = (lens or LensPreset.CINEMATIC_35MM).value
        motion_default = (
            subtle_micro_motion or 
            "subtle fabric sway, fine hair drift, natural slow breathing, drifting atmospheric dust motes"
        )
        
        prompt = (
            f"CHARACTERS:\n"
            f"{characters_desc.strip()}\n"
            f"Skin & features: {PhysicalRealityTokens.HUMAN_DETAILS}.\n\n"
            f"ENVIRONMENT (recreate precisely, cinematic set lighting):\n"
            f"{environment_desc.strip()}.\n"
            f"Optics & atmosphere: {lens_text}. {PhysicalRealityTokens.ENVIRONMENT_PHYSICS}.\n\n"
            f"ACTION & CAMERA ({duration_s:.1f} seconds):\n"
            f"Camera & framing: {action_and_camera_desc.strip()}.\n"
            f"Micro-motion cues: {motion_default}.\n"
            f"Style & anti-plastic constraints: {OpticalArtifacts.SUBTLE_CINE}. "
            f"{PhysicalRealityTokens.ACTOR_ON_SET_FRAMING}."
        )
        return prompt.strip()

    def enhance_cinematic_prompt(
        self,
        base_prompt: str,
        lens: Optional[LensPreset] = None,
        include_skin: bool = True,
        include_physics: bool = True,
        actor_framing: bool = True
    ) -> str:
        """Reichert einen beliebigen Basis-Prompt mit Anti-Plastik-Tokens an."""
        parts = [base_prompt.strip()]
        lens_text = (lens or self.default_lens).value
        parts.append(lens_text)
        parts.append(OpticalArtifacts.SUBTLE_CINE)
        
        if include_skin:
            parts.append(PhysicalRealityTokens.HUMAN_DETAILS)
        if include_physics:
            parts.append(PhysicalRealityTokens.ENVIRONMENT_PHYSICS)
        if actor_framing:
            parts.append(PhysicalRealityTokens.ACTOR_ON_SET_FRAMING)
            
        return ", ".join(parts)
