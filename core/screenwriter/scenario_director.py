"""core.screenwriter.scenario_director — Профессиональный режиссер сценариев (Scenario Director).

Интегрирует передовые индустриальные практики сценаристики (Studiovity, Sudowrite, LTX Studio):
1. 3-актная драматургическая структура (Beat Sheet: Hook, Exposition, Turning Point, Climax, Resolution).
2. Музыкальная синхронизация по тактам и BPM (точное распределение хронометража сцен).
3. Библия персонажа (Character Bible) с 50-словным якорным дескриптором (Anchor Token).
4. Профессиональная операторская экспликация (Cinematography & Camera Direction).
5. Генерация готовых промпт-карт для генераторов видео (Google Flow, Veo 3.1, Midjourney, Kling).
"""

import json
import logging
import math
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

from core.api.agnes_chat import AgnesChatAPI, strip_code_fence
from core.screenwriter.photorealism_engine import (
    PhotorealismEngine,
    LensPreset,
    IdentityTransferSpec,
    PhysicalRealityTokens,
    OpticalArtifacts,
)

logger = logging.getLogger(__name__)



@dataclass
class ContinuityLock:
    """Неизменяемая визуальная деталь, которая дословно переносится в каждый промпт кадра.

    Concept ported from ``drama-skills`` (MIT, see ``.agents/skills/THIRD_PARTY_NOTICES.md``):
    the lock face is written as a minimal noun phrase in the prompt language, so a
    deterministic checker can verify it inside generated prompt text (``review_project``).

    Attributes:
        key: Группа замка: ``identity``, ``wardrobe``, ``prop`` или ``grooming``.
        phrase: Минимальная именная группа на языке промпта, например
            ``short matte brown hair``. Копируется в промпт без изменений.
    """
    key: str
    phrase: str


@dataclass
class CharacterProfile:
    name: str
    age: int
    role: str  # Protagonist, Antagonist, Mentor, etc.
    gender: str
    appearance: str  # Волосы, лицо, рост, особые приметы (щетина, глаза)
    wardrobe: str  # Одежда от верха до обуви
    anchor_token: str  # 50+ слов якорного описания для промптов
    prop_anchor: str = ""  # Физический визуальный якорь (Prop Map Anchor: напр. старинные часы, красный шарф)
    turnaround_prompts: Dict[str, str] = field(default_factory=dict)  # front, 34, profile, back, fullbody
    # Идентичность против состояния (drama-skills): то, что делает персонажа собой,
    # отделено от того, что меняется по сюжету (мокрый плащ, ссадина, сумерки).
    identity_anchors: List[str] = field(default_factory=list)  # неизменяемые признаки
    state_variants: List[str] = field(default_factory=list)  # изменяемые состояния по сценам
    continuity_locks: List[ContinuityLock] = field(default_factory=list)  # дословные замки для промптов


@dataclass
class SceneShot:
    scene_number: int
    start_time_s: float
    end_time_s: float
    duration_s: float
    beat_type: str  # Hook, Exposition, Rising Action, Climax, Outro
    shot_size: str  # Extreme Wide, Wide, Medium, Close-Up, Extreme Close-Up
    camera_movement: str  # Static locked-off, Slow Push-In, Tracking, Dutch Angle, Dolly Pull
    lighting_and_color: str  # Hopper lighting, Golden Hour, Indigo Rain, Chiaroscuro
    environment: str  # Детали окружения
    action_description: str  # Что происходит в кадре
    character_action: str  # Поведение героя (рот закрыт, мимика, взгляд)
    symbolic_anchor: str  # Сквозной предмет (напр., жёлтый зонт, шар)
    video_prompt: str  # Готовый промпт для Veo / Flow / Kling
    emotion: str = ""  # Правило "1 Shot = 1 Emotion" (доминирующее эмоциональное состояние)
    transition: str = "Cut"  # Монтажный переход (Hard Cut, Match Cut, Whip Pan, Dissolve)
    narration_or_lyrics: str = ""  # Текст песни / закадровый голос
    audio_sfx: str = ""  # Звуковые эффекты / атмосфера
    tier3_prompt: str = ""  # Структурированный 3-Tier Anti-Plastic промпт
    five_element_prompt: str = ""  # 5-Element Prompt Formula [REF, SCENE, CAMERA, TONE, ACTION, TRANSITION]
    temporal_prompt: str = ""  # Посекундный таймлайн-промпт [0-1s, 1-3s, 3-5s] (SYNTX AI / LTX standard)


@dataclass
class ReviewIssue:
    """Одна находка детерминированной проверки сценария (не LLM-ревью).

    Attributes:
        rule_id: Идентификатор правила (``SCN-01`` … ``SCN-11``).
        severity: ``blocker`` — блокирует производство; ``warning`` — к сведению.
        location: Где найдено («Сцена 03», «Character Bible»).
        detail: Что именно не так, с фактом из данных.
        fix_hint: Какая правка требуется, чтобы правило прошло.
    """
    rule_id: str
    severity: str
    location: str
    detail: str
    fix_hint: str


@dataclass
class ScenarioProject:
    title: str
    logline: str
    genre: str
    visual_style: str  # Например: Vintage Gouache Cel Animation, Edward Hopper cinematic
    aspect_ratio: str = "16:9"
    bpm: Optional[int] = 120
    total_duration_s: float = 96.0
    character: Optional[CharacterProfile] = None
    shots: List[SceneShot] = field(default_factory=list)
    review: List[ReviewIssue] = field(default_factory=list)  # результат review_project()


class ScenarioDirector:
    """Генератор профессиональных сценариев и раскадровок."""

    # Слова, провоцирующие липсинк (железное правило: рот закрыт, дыхание и взгляд).
    _LIPSYNC_WORDS = (
        "speaking", "speaks", "talking", "talks", "shouting", "shouts",
        "mouth open", "lips moving", "saying", "reciting",
        "говорит", "кричит", "губы",
    )

    def __init__(self, chat_api: Optional[AgnesChatAPI] = None, api_key: Optional[str] = None):
        if chat_api:
            self.chat = chat_api
        else:
            try:
                from core.api.key_manager import get_key_ring
                effective_key = api_key or get_key_ring().current()
            except Exception:
                effective_key = api_key or os.environ.get("AGNES_API_KEY", "")
            self.chat = AgnesChatAPI(api_key=effective_key)
        self.photorealism = PhotorealismEngine()

    def format_scene_prompt_3tier(
        self,
        shot: SceneShot,
        character: Optional[CharacterProfile] = None,
        lens: Optional[LensPreset] = None
    ) -> str:
        """Формирует структурированный 3-Tier промпт (CHARACTERS, ENVIRONMENT, ACTION & CAMERA)."""
        char_desc = (
            f"{character.anchor_token}" if character and character.anchor_token
            else shot.character_action or "Cinematic subject"
        )
        if shot.character_action and character and character.anchor_token:
            char_desc += f" Action & emotion: {shot.character_action}."
            
        env_desc = f"{shot.environment}. Lighting & color: {shot.lighting_and_color}"
        action_cam = f"{shot.shot_size}, {shot.camera_movement}. Action: {shot.action_description}"
        if shot.symbolic_anchor:
            action_cam += f". Key anchor motif: {shot.symbolic_anchor}"
            
        return self.photorealism.format_three_tier_action_prompt(
            characters_desc=char_desc,
            environment_desc=env_desc,
            action_and_camera_desc=action_cam,
            duration_s=shot.duration_s,
            lens=lens
        )

    def format_identity_transfer(
        self,
        character: CharacterProfile,
        scene_style: str
    ) -> str:
        """Формирует промпт переноса личности по 2-референсному принципу (Multi-Reference)."""
        spec = IdentityTransferSpec(
            character_name=character.name,
            identity_features=f"{character.appearance}, wardrobe baseline: {character.wardrobe}",
            scene_costume_and_style=scene_style
        )
        return self.photorealism.format_identity_transfer_prompt(spec)

    def format_5element_prompt(
        self,
        shot: SceneShot,
        character: Optional[CharacterProfile] = None
    ) -> str:
        """Формирует 5-элементный промпт режиссуры (Reference, Scene, Camera, Tone, Transition).

        Основан на золотом стандарте структурированного промптинга (Seedance 2.0 / Veo 3.1 / Google Flow):
        - 1 кадр = 1 эмоция
        - Сквозной физический якорь (Prop Map Anchor)
        - Чёткое разделение параметров
        """
        char_anchor = character.anchor_token if character and character.anchor_token else ""
        prop_anchor = (character.prop_anchor if character and character.prop_anchor else "") or shot.symbolic_anchor or ""
        ref_tokens = []
        if char_anchor:
            ref_tokens.append(f"Subject: {char_anchor}")
        if prop_anchor:
            ref_tokens.append(f"Prop Anchor: {prop_anchor}")
        ref_part = f"[REFERENCE: {'; '.join(ref_tokens)}]" if ref_tokens else "[REFERENCE: Cinematic subject]"

        scene_part = f"[SCENE: {shot.environment}, Lighting: {shot.lighting_and_color}]"
        camera_part = f"[CAMERA: {shot.shot_size}, Movement: {shot.camera_movement}]"
        tone_part = f"[TONE & EMOTION: {shot.emotion or 'Cinematic dramatic'}]"
        action_part = f"[ACTION: {shot.action_description}. Character Acting: {shot.character_action}]"
        transition_part = f"[TRANSITION: {shot.transition or 'Cut'}]"

        return f"{ref_part} {scene_part} {camera_part} {tone_part} {action_part} {transition_part}"

    def format_temporal_prompt(
        self,
        shot: SceneShot,
        character: Optional[CharacterProfile] = None
    ) -> str:
        """Формирует структурированный посекундный промпт (Temporal Timeline Prompt).

        Инспирировано методологией SYNTX AI и LTX Studio:
        Разбивает хронометраж кадра на 3 детерминированные фазы:
        [0.0-{t1}s]: Экспозиция кадра, окружение, свет, базовое состояние персонажа и замки непрерывности.
        [{t1}-{t2}s]: Динамическое действие, кинематографическое движение камеры и параллакс.
        [{t2}-{dur}s]: Эмоциональный пик (1 Shot = 1 Emotion), микромимика (рот закрыт), подготовка к склейке.
        """
        dur = round(shot.duration_s if shot.duration_s and shot.duration_s > 0 else 5.0, 1)
        t1 = round(max(0.8, min(1.5, dur * 0.25)), 1)
        t2 = round(max(t1 + 1.0, min(dur - 0.8, dur * 0.75)), 1)

        char_anchor = character.anchor_token if character and character.anchor_token else ""
        locks_block = self.format_continuity_lock_block(character)

        # Фаза 1: Экспозиция и установка кадра
        p1_parts = [f"Establishing frame in {shot.shot_size}."]
        if locks_block:
            p1_parts.append(locks_block)
        elif char_anchor:
            p1_parts.append(f"Subject: {char_anchor}.")
        if shot.environment:
            p1_parts.append(f"Setting: {shot.environment}.")
        if shot.lighting_and_color:
            p1_parts.append(f"Lighting & Palette: {shot.lighting_and_color}.")
        p1_parts.append("Atmospheric micro-motion, gentle breathing, mouth firmly closed, no speaking.")
        p1_parts.append("Preserve exact facial bone structure and likeness throughout, zero facial morphing, no beautification filters.")
        p1_text = " ".join(p1_parts)

        # Фаза 2: Действие и движение камеры
        p2_parts = []
        if shot.action_description:
            p2_parts.append(f"Dynamic narrative progression: {shot.action_description}.")
        if shot.camera_movement:
            p2_parts.append(f"Camera execution: {shot.camera_movement}.")
        p2_parts.append("Consistent physical momentum, natural foreground-to-background parallax, cinematic motion blur.")
        p2_parts.append("Maintain steady linear velocity and constant speed throughout the shot with zero sudden acceleration drops.")
        p2_text = " ".join(p2_parts)

        # Фаза 3: Эмоциональный акцент и стабилизация кадра под монтаж
        emotion_str = shot.emotion or "Cinematic dramatic focus"
        p3_parts = [f"Emotional resolution: {emotion_str}."]
        if shot.character_action:
            p3_parts.append(f"Actor micro-expression: {shot.character_action}.")
        else:
            p3_parts.append("Actor micro-expression: intense focused gaze, subtle breath, motionless lips.")
        p3_parts.append(f"Framing stabilizes cleanly, preparing seamless cut for transition: {shot.transition or 'Cut'}.")
        p3_text = " ".join(p3_parts)

        return f"[0.0-{t1:.1f}s]: {p1_text}\n[{t1:.1f}-{t2:.1f}s]: {p2_text}\n[{t2:.1f}-{dur:.1f}s]: {p3_text}"

    def calculate_scene_durations(self, total_seconds: float, bpm: Optional[int] = None, target_scenes: int = 12) -> List[float]:
        """Рассчитывает точный хронометраж сцен по тактам BPM или равномерным долям."""
        if bpm and bpm > 0:
            beat_duration = 60.0 / bpm
            bar_duration = beat_duration * 4.0  # 4/4 такт
            # Сколько тактов на сцену
            bars_per_scene = max(1, round((total_seconds / target_scenes) / bar_duration))
            scene_dur = round(bars_per_scene * bar_duration, 2)
            durations = [scene_dur] * target_scenes
            # Корректируем последнюю сцену под общий хронометраж
            diff = round(total_seconds - sum(durations), 2)
            if durations:
                durations[-1] += diff
            return durations
        else:
            uniform = round(total_seconds / target_scenes, 2)
            durations = [uniform] * target_scenes
            diff = round(total_seconds - sum(durations), 2)
            if durations:
                durations[-1] += diff
            return durations

    def build_character_bible(self, character_idea: str, visual_style: str) -> CharacterProfile:
        """Создает полную Библию персонажа с 50-словным якорным токеном и физическим реквизитом (Prop Anchor).

        Дополнительно разделяет идентичность и состояние (concept from ``drama-skills``, MIT):
        ``identity_anchors`` — то, что делает персонажа собой и не меняется;
        ``state_variants`` — то, что меняется по сюжету (мокрый плащ, ссадина, сумерки);
        ``continuity_locks`` — минимальные именные группы на языке промпта, которые
        копируются в каждый кадр дословно и проверяются ``review_project``.
        """
        system_prompt = (
            "You are a lead character designer and Hollywood continuity supervisor. "
            "Your job is to create an immutable Character Bible that guarantees 100% visual consistency "
            "across multi-shot AI video pipelines (Veo, Midjourney, Google Flow). "
            "Output strictly a JSON object with no markdown fences:\n"
            "{\n"
            '  "name": "...",\n'
            '  "age": 32,\n'
            '  "role": "Protagonist",\n'
            '  "gender": "male|female",\n'
            '  "appearance": "facial features, jawline, eye color, hair texture, stubble",\n'
            '  "wardrobe": "exact upper clothing, coat material, trousers, footwear, textures",\n'
            '  "anchor_token": "A dense 50+ word paragraph describing the person from head to toe. Every scene prompt will copy this verbatim.",\n'
            '  "prop_anchor": "One distinct, high-contrast physical prop or accessory carried/worn in every shot (e.g. vintage bronze wristwatch, red wool scarf, worn aviator goggles)",\n'
            '  "identity_anchors": ["face shape and jawline", "eye colour", "hair colour and texture"],\n'
            '  "state_variants": ["wardrobe state that changes with the story, e.g. soaked coat in act 2"],\n'
            '  "continuity_locks": [\n'
            '    {"key": "identity", "phrase": "minimal noun phrase in the prompt language, e.g. grey-green eyes"},\n'
            '    {"key": "grooming", "phrase": "short matte brown hair"},\n'
            '    {"key": "wardrobe", "phrase": "indigo wool overcoat"},\n'
            '    {"key": "prop", "phrase": "bronze wristwatch with cracked glass"}\n'
            '  ],\n'
            '  "turnaround_prompts": {\n'
            '    "front": "front face close-up...",\n'
            '    "three_quarter": "three quarter portrait...",\n'
            '    "profile": "side profile silhouette...",\n'
            '    "back": "back view showing shoulders and hair...",\n'
            '    "fullbody": "full body standing pose..."\n'
            '  }\n'
            "}\n\n"
            "Rules:\n"
            "1. Separate IDENTITY from STATE. An identity anchor is something that, if changed, "
            "means this is no longer the same person (bone structure, eye colour, hair colour, scars). "
            "A state variant keeps the same identity but changes appearance (wet clothes, injury, dusk). "
            "Never put a state change into identity_anchors.\n"
            "2. continuity_locks hold ONLY facts that must not drift across shots. Write each phrase as a "
            "minimal noun phrase in English, lowercase, no punctuation, 2-6 words, and use the SAME "
            "spelling everywhere. These phrases are copied verbatim into every shot prompt.\n"
            "3. Do not invent brands, logos, readable text or sensitive attributes not present in the concept.\n"
            "4. Exactly one prop_anchor. It appears in every shot; never add a second hero prop."
        )
        user_prompt = f"Character Concept: {character_idea}\nVisual Art Style: {visual_style}"
        data = self.chat.chat_json(system_prompt, user_prompt)
        return CharacterProfile(
            name=data.get("name", "Protagonist"),
            age=data.get("age", 30),
            role=data.get("role", "Protagonist"),
            gender=data.get("gender", "male"),
            appearance=data.get("appearance", ""),
            wardrobe=data.get("wardrobe", ""),
            anchor_token=data.get("anchor_token", ""),
            prop_anchor=data.get("prop_anchor", ""),
            turnaround_prompts=data.get("turnaround_prompts", {}) or {},
            identity_anchors=[str(a) for a in (data.get("identity_anchors") or []) if str(a).strip()],
            state_variants=[str(v) for v in (data.get("state_variants") or []) if str(v).strip()],
            continuity_locks=[
                ContinuityLock(key=str(l.get("key", "identity")), phrase=str(l.get("phrase", "")).strip())
                for l in (data.get("continuity_locks") or [])
                if isinstance(l, dict) and str(l.get("phrase", "")).strip()
            ],
        )

    def format_continuity_lock_block(self, character: Optional[CharacterProfile]) -> str:
        """Собирает дословный блок замков непрерывности для вставки в промпт кадра.

        Args:
            character: Профиль персонажа (может быть ``None``).

        Returns:
            Готовая строка для промпта или пустая строка, если замков нет.
        """
        if not character or not character.continuity_locks:
            return ""
        phrases = [lock.phrase.strip() for lock in character.continuity_locks if lock.phrase and lock.phrase.strip()]
        if not phrases:
            return ""
        return "Continuity locks (copy verbatim, never rephrase): " + "; ".join(phrases) + "."

    def review_project(self, project: ScenarioProject, requested_scenes: Optional[int] = None) -> List[ReviewIssue]:
        """Детерминированная проверка сценария перед производством — без вызовов LLM.

        Проверяет ровно то, что можно проверить фактами, не спрашивая модель: наличие
        замков непрерывности в каждом промпте, полноту Character Bible, дубли сквозного
        реквизита, запрет липсинка, согласованность хронометража. Формулировки уровня
        «убедительно ли это» остаются человеку.

        Args:
            project: Проверяемый проект.
            requested_scenes: Ожидаемое число сцен (для сверки факта с запросом).

        Returns:
            Список находок; ``blocker`` блокирует производство, ``warning`` — к сведению.
        """
        issues: List[ReviewIssue] = []
        character = project.character

        if not project.shots:
            issues.append(ReviewIssue(
                "SCN-00", "blocker", "Раскадровка",
                "Проект не содержит кадров.",
                "Повторить генерацию сцен.",
            ))
            return issues

        # SCN-09 / SCN-10: полнота Character Bible (железное правило — карточка персонажа)
        if not character or not (character.anchor_token or "").strip():
            issues.append(ReviewIssue(
                "SCN-09", "blocker", "Character Bible",
                "Отсутствует anchor_token — персонаж не зафиксирован.",
                "Перегенерировать Character Bible с якорным описанием.",
            ))
        if character:
            required_views = ("front", "three_quarter", "profile", "back", "fullbody")
            missing_views = [v for v in required_views if not (character.turnaround_prompts or {}).get(v)]
            if missing_views:
                issues.append(ReviewIssue(
                    "SCN-10", "blocker", "Character Bible",
                    "Неполная карточка персонажа, нет ракурсов: " + ", ".join(missing_views),
                    "Достроить turnaround по всем пяти ракурсам — без него кадры нельзя привязывать к референсу.",
                ))
            if not character.continuity_locks:
                issues.append(ReviewIssue(
                    "SCN-11", "warning", "Character Bible",
                    "Не заданы continuity_locks — дрейф внешности не проверяется механически.",
                    "Задать 3–5 минимальных именных групп (лицо, глаза, волосы, одежда, реквизит).",
                ))

        lock_phrases = [l.phrase.lower() for l in (character.continuity_locks if character else []) if l.phrase]
        anchor = (project.shots[0].symbolic_anchor or "").strip()
        anchor_lc = anchor.lower()

        for shot in project.shots:
            loc = f"Сцена {shot.scene_number:02d}"
            prompt_lc = (shot.video_prompt or "").lower()

            # SCN-02: пустой промпт — кадр нечем генерировать
            if not prompt_lc.strip():
                issues.append(ReviewIssue(
                    "SCN-02", "blocker", loc,
                    "Пустой video_prompt.",
                    "Сгенерировать производственный промпт для кадра.",
                ))
                continue

            # SCN-01: замки непрерывности должны стоять в промпте дословно
            missing_locks = [p for p in lock_phrases if p not in prompt_lc]
            if missing_locks:
                issues.append(ReviewIssue(
                    "SCN-01", "blocker", loc,
                    "В промпте отсутствуют continuity locks: " + ", ".join(missing_locks),
                    "Дословно вставить Continuity-Lock-Block в промпт кадра.",
                ))

            # SCN-03: 1 Shot = 1 Emotion
            if not (shot.emotion or "").strip():
                issues.append(ReviewIssue(
                    "SCN-03", "blocker", loc,
                    "Не задана доминирующая эмоция кадра.",
                    "Проставить одну эмоцию на кадр (правило 1 Shot = 1 Emotion).",
                ))

            # SCN-04: монтажный переход
            if not (shot.transition or "").strip():
                issues.append(ReviewIssue(
                    "SCN-04", "warning", loc,
                    "Не указан монтажный переход.",
                    "Указать Cut / Match Cut / Whip Pan / Cross-Dissolve.",
                ))

            # SCN-07: железное правило «рот закрыт» — слова, провоцирующие липсинк
            acting_lc = f"{shot.character_action or ''} {shot.action_description or ''}".lower()
            lip_hits = [w for w in self._LIPSYNC_WORDS if w in acting_lc]
            if lip_hits:
                issues.append(ReviewIssue(
                    "SCN-07", "blocker", loc,
                    "В описании действия есть речь/артикуляция: " + ", ".join(lip_hits),
                    "Переписать на дыхание и взгляд; рот остаётся закрытым.",
                ))

            # SCN-08: сквозной реквизит не должен дублироваться внутри кадра
            if anchor_lc and prompt_lc.count(anchor_lc) > 1:
                issues.append(ReviewIssue(
                    "SCN-08", "warning", loc,
                    f"Сквозной реквизит «{anchor}» упомянут {prompt_lc.count(anchor_lc)} раза в одном промпте.",
                    "Оставить одно упоминание — иначе модель размножит предмет.",
                ))

        # SCN-05: хронометраж
        total_actual = round(sum(s.duration_s for s in project.shots), 2)
        if abs(total_actual - project.total_duration_s) > 0.5:
            issues.append(ReviewIssue(
                "SCN-05", "warning", "Хронометраж",
                f"Сумма кадров {total_actual}s расходится с целевой {project.total_duration_s}s.",
                "Пересчитать длительности по BPM-тактам.",
            ))

        # SCN-06: число сцен
        if requested_scenes is not None and len(project.shots) != requested_scenes:
            issues.append(ReviewIssue(
                "SCN-06", "warning", "Раскадровка",
                f"Сцен {len(project.shots)}, запрошено {requested_scenes}.",
                "Перегенерировать раскадровку или скорректировать запрос.",
            ))

        return issues

    def generate_scenario(
        self,
        story_idea: str,
        visual_style: str,
        total_duration_s: float = 96.0,
        bpm: Optional[int] = 120,
        num_scenes: int = 12,
        symbolic_anchor: str = "A vibrant canary-yellow umbrella"
    ) -> ScenarioProject:
        """Создает полный режиссерский проект сценария с раскадровкой и промптами."""
        durations = self.calculate_scene_durations(total_duration_s, bpm, num_scenes)

        # 1. Библия персонажа
        char_profile = self.build_character_bible(story_idea, visual_style)

        # 2. Драматургическая раскладка сцен
        system_prompt = (
            "You are an acclaimed film director and storyboard master combining the discipline of "
            "WriterDuet screenplay structure, LTX Studio shot breakdowns, and Edward Hopper cinematography. "
            "You write a master video shotlist strictly timed to music beats.\n\n"
            "Rules:\n"
            "1. Exactly ONE single symbolic anchor object throughout the entire story (e.g. exactly one umbrella). Never duplicate it.\n"
            "2. Scene 01 must be an atmospheric intro / exposition where the symbolic item is introduced.\n"
            "3. Pacing follows a classic 3-act emotional arc:\n"
            "   - Act I (Scenes 1-4): Loneliness/Gloomy reality, discovery of hope\n"
            "   - Act II (Scenes 5-8): Journey through rain/obstacles, golden beams piercing darkness\n"
            "   - Act III (Scenes 9-12): Triumph, rising dawn, returning to the origin transformed\n"
            "4. Character behavior: mouth closed, subtle breathing/eye acting, NO distorted lip movements.\n"
            "5. Video prompts MUST be in English, incorporating the character's anchor token, art style, "
            "lighting, camera movement, and explicit negative constraints.\n"
            "6. 1 Shot = 1 Emotion: Each scene MUST express one single clear emotional state (e.g. 'Melancholic longing', 'Sudden terror', 'Quiet awe'). Never mix conflicting emotions within a single cut.\n"
            "7. Transitions: Specify a precise cinematic transition for the cut (e.g. 'Match Cut on motion', 'Hard Cut', 'Slow Cross-Dissolve', 'Whip Pan').\n"
            "8. Every video_prompt MUST contain every continuity lock phrase VERBATIM, character-for-character, "
            "lowercase as given. Do not paraphrase, translate, reorder or abbreviate them.\n"
            "9. Never describe speaking, talking, shouting or moving lips. Acting is breath, gaze and micro-motion only.\n"
            "Output strictly a JSON object with key 'scenes': a list of objects matching the requested schema."
        )

        lock_block = self.format_continuity_lock_block(char_profile)
        user_prompt = f"""\
Project Concept: {story_idea}
Art Style: {visual_style}
Symbolic Leitmotif Anchor: {symbolic_anchor}
Character Anchor Token: {char_profile.anchor_token}
Character Prop Anchor: {char_profile.prop_anchor}
{lock_block}
Total Scenes: {num_scenes}
Scene Durations in seconds: {durations}

For each scene, output:
{{
  "scene_number": 1,
  "beat_type": "Hook / Exposition / Rising Action / Midpoint / Climax / Resolution",
  "shot_size": "Extreme Wide / Wide / Medium / Close-Up",
  "camera_movement": "Static locked-off / Slow Push-In / Tracking / Dutch Angle",
  "lighting_and_color": "Lighting and color palette description",
  "environment": "Environment details",
  "action_description": "Narrative action",
  "character_action": "Actor expressions and subtle gestures",
  "emotion": "Single dominant emotion (e.g. Quiet contemplation)",
  "transition": "Cut / Match Cut on motion / Whip Pan / Slow Cross-Dissolve",
  "video_prompt": "Production-ready prompt for Veo 3.1 / Google Flow / Midjourney, containing all continuity locks verbatim"
}}
"""

        data = self.chat.chat_json(system_prompt, user_prompt)
        scenes_data = data.get("scenes", [])

        shots: List[SceneShot] = []
        cur_time = 0.0
        for i, s_data in enumerate(scenes_data):
            dur = durations[i] if i < len(durations) else 8.0
            shot = SceneShot(
                scene_number=i + 1,
                start_time_s=round(cur_time, 2),
                end_time_s=round(cur_time + dur, 2),
                duration_s=round(dur, 2),
                beat_type=s_data.get("beat_type", "Narrative Beat"),
                shot_size=s_data.get("shot_size", "Medium Shot"),
                camera_movement=s_data.get("camera_movement", "Static locked-off"),
                lighting_and_color=s_data.get("lighting_and_color", "Cinematic"),
                environment=s_data.get("environment", ""),
                action_description=s_data.get("action_description", ""),
                character_action=s_data.get("character_action", ""),
                symbolic_anchor=symbolic_anchor,
                video_prompt=s_data.get("video_prompt", ""),
                emotion=s_data.get("emotion", "Cinematic dramatic"),
                transition=s_data.get("transition", "Cut")
            )
            shot.tier3_prompt = self.format_scene_prompt_3tier(shot, char_profile)
            shot.five_element_prompt = self.format_5element_prompt(shot, char_profile)
            shot.temporal_prompt = self.format_temporal_prompt(shot, char_profile)
            shots.append(shot)
            cur_time += dur


        project = ScenarioProject(
            title=story_idea.split("\n")[0][:60],
            logline=story_idea.replace("\n", " ")[:200],
            genre="Animated Cinematic Music Video",
            visual_style=visual_style,
            bpm=bpm,
            total_duration_s=total_duration_s,
            character=char_profile,
            shots=shots,
        )
        project.review = self.review_project(project, requested_scenes=num_scenes)
        return project

    def export_to_markdown(self, proj: ScenarioProject) -> str:
        """Экспортирует проект сценария в структурированный Markdown-формат (Screenplay + Shotlist)."""
        lines = [
            f"# 🎬 Режиссёрский сценарий и раскадровка: {proj.title}",
            "",
            f"**Жанр:** {proj.genre} | **Хронометраж:** {proj.total_duration_s} сек | **Темп:** {proj.bpm} BPM",
            f"**Стиль:** {proj.visual_style} | **Формат кадра:** {proj.aspect_ratio}",
        ]
        if proj.shots and proj.shots[0].symbolic_anchor:
            lines.append(f"**Сквозной символ (Лейтмотив):** {proj.shots[0].symbolic_anchor}")
        lines.extend([
            "",
            "---",
            "",
            "## 👤 Библия персонажа (Character Bible & Consistency Anchor)",
            "",
            f"- **Имя/Роль:** {proj.character.name} ({proj.character.role}, ~{proj.character.age} лет)",
            f"- **Внешность:** {proj.character.appearance}",
            f"- **Костюм:** {proj.character.wardrobe}",
            f"- **Физический якорь реквизита (Prop Anchor):** {proj.character.prop_anchor or 'N/A'}",
            "",
            "> 🔒 **Якорный токен персонажа (Anchor Token):**",
            f"> *{proj.character.anchor_token}*",
            "",
        ])

        # Замки непрерывности и разделение «идентичность / состояние»
        if proj.character.continuity_locks:
            lines.append("> 📌 **Замки непрерывности (Continuity Locks — копировать дословно в каждый промпт):**")
            for lock in proj.character.continuity_locks:
                lines.append(f"> - `{lock.key}` → {lock.phrase}")
            lines.append("")
        if proj.character.identity_anchors:
            lines.append("- **Идентичность (не меняется):** " + "; ".join(proj.character.identity_anchors))
        if proj.character.state_variants:
            lines.append("- **Состояния по сюжету (меняются):** " + "; ".join(proj.character.state_variants))

        lines.extend([
            "",
            "> 🎭 **Шаблон Multi-Reference Identity Transfer (2-Reference Blueprint):**",
            f"> `{self.format_identity_transfer(proj.character, proj.visual_style)}`",
            "",
            "---",
            "",
            "## 🎞️ Поэпизодная раскадровка и производственный план (Shotlist)",
            "",
            "| № | Таймкод | План (Shot) | Движение камеры | Свет и колорит | Эмоция (1-Shot-1-Emotion) | Переход | Драматургическое действие |",
            "|---|---|---|---|---|---|---|---|",
        ])

        for s in proj.shots:
            tc = f"{int(s.start_time_s//60):02d}:{int(s.start_time_s%60):02d} – {int(s.end_time_s//60):02d}:{int(s.end_time_s%60):02d}"
            lines.append(f"| **{s.scene_number:02d}** | `{tc}` ({s.duration_s}s) | {s.shot_size} | {s.camera_movement} | {s.lighting_and_color} | *{s.emotion or 'Dramatic'}* | `{s.transition or 'Cut'}` | {s.action_description} |")

        lines.extend([
            "",
            "---",
            "",
            "## 🎯 Производственные промпт-карты (Production Prompt Cards for Veo / Flow / Seedance)",
            ""
        ])

        for s in proj.shots:
            tc = f"{int(s.start_time_s//60):02d}:{int(s.start_time_s%60):02d} – {int(s.end_time_s//60):02d}:{int(s.end_time_s%60):02d}"
            lines.extend([
                f"### Сцена {s.scene_number:02d} [{tc}] — {s.beat_type}",
                f"- **Операторское решение:** {s.shot_size}, {s.camera_movement} | **Переход:** `{s.transition or 'Cut'}`",
                f"- **Свет и атмосфера:** {s.lighting_and_color} | **Эмоция:** *{s.emotion or 'Dramatic'}*",
                f"- **Поведение героя:** {s.character_action}",
                "**Стандартный промпт:**",
                "```text",
                s.video_prompt,
                "```",
            ])
            if s.tier3_prompt:
                lines.extend([
                    "**3-Tier Anti-Plastic Production Prompt:**",
                    "```text",
                    s.tier3_prompt,
                    "```"
                ])
            if s.five_element_prompt:
                lines.extend([
                    "**5-Element Master Director Prompt [REF, SCENE, CAMERA, TONE, ACTION, TRANSITION]:**",
                    "```text",
                    s.five_element_prompt,
                    "```"
                ])
            if s.temporal_prompt:
                lines.extend([
                    "**Temporal Timeline Prompt [Second-by-Second Cinematic]:**",
                    "```text",
                    s.temporal_prompt,
                    "```"
                ])
            lines.append("")

        # Итог детерминированной проверки (rule ids как в short-drama-review)
        if proj.review:
            blockers = [i for i in proj.review if i.severity == "blocker"]
            warnings = [i for i in proj.review if i.severity != "blocker"]
            lines.extend([
                "---",
                "",
                "## ✅ Проверка сценария (Review)",
                "",
                f"**Вердикт:** {'REVISE — есть блокеры' if blockers else 'OK — блокеров нет'} "
                f"({len(blockers)} blocker, {len(warnings)} warning)",
                "",
            ])
            for issue in blockers + warnings:
                lines.extend([
                    f"- **{issue.rule_id}** · `{issue.severity}` · {issue.location}",
                    f"  - Найдено: {issue.detail}",
                    f"  - Требуется: {issue.fix_hint}",
                ])
            lines.append("")

        return "\n".join(lines)

