"""core.screenwriter.camera_presets — Каталог 20 кинематографических пресетов движения камеры.

Разработан на базе стандартов кинорежиссуры и методологии SYNTX AI / LTX Studio.
Предоставляет детерминированные модификаторы промптов, категории и описания для UI и LLM.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class CameraMovementPreset(BaseModel):
    id: str
    name_ru: str
    name_en: str
    category: str  # dramatic | dynamic | perspective | atmospheric
    category_ru: str
    prompt_modifier: str
    description_ru: str
    description_en: str
    icon: str


CAMERA_MOVEMENTS: List[CameraMovementPreset] = [
    # ── Dramatic / Эмоциональные и психологические ──
    CameraMovementPreset(
        id="dolly_in",
        name_ru="Dolly In (Плавный наезд)",
        name_en="Dolly In (Push In)",
        category="dramatic",
        category_ru="Драматические",
        prompt_modifier="Slow, deliberate dolly push-in camera movement towards the subject, mounting emotional intensity and focal intimacy.",
        description_ru="Постепенное приближение к герою, усиливающее драматическое напряжение и фокус на эмоции.",
        description_en="Gradual push-in towards the subject, heightening dramatic tension and intimacy.",
        icon="zoom-in",
    ),
    CameraMovementPreset(
        id="dolly_out",
        name_ru="Dolly Out (Плавный отъезд)",
        name_en="Dolly Out (Pull Back)",
        category="dramatic",
        category_ru="Драматические",
        prompt_modifier="Slow continuous dolly pull-back revealing surrounding environment, creating emotional solitude and narrative scale.",
        description_ru="Отъезд от персонажа, подчеркивающий его одиночество или масштаб окружающего мира.",
        description_en="Pulling away from subject, emphasizing isolation or expansive environment.",
        icon="zoom-out",
    ),
    CameraMovementPreset(
        id="vertigo_zoom",
        name_ru="Vertigo (Долли-зум / Контразум)",
        name_en="Vertigo (Dolly Zoom / Trombone Shot)",
        category="dramatic",
        category_ru="Драматические",
        prompt_modifier="Vertigo contra-zoom (dolly zoom), background perspective warps and stretches dramatically while subject size remains rock-solid in frame.",
        description_ru="Культовый эффект Хичкока: фон деформируется/растягивается, пока герой остается на месте (шок, прозрение).",
        description_en="Iconic Hitchcock effect: background warps while subject size stays locked.",
        icon="disc",
    ),
    CameraMovementPreset(
        id="snorricam",
        name_ru="Snorricam (Крепление к телу)",
        name_en="Snorricam (Body Rig)",
        category="dramatic",
        category_ru="Драматические",
        prompt_modifier="Snorricam chest-rig mounted to the actor, background twists and shifts frantically around the motionless face, conveying extreme anxiety.",
        description_ru="Камера жестко прикреплена к актеру: лицо статично, а весь мир вокруг бешено крутится.",
        description_en="Camera mounted to actor's chest, conveying disorientation and panic.",
        icon="user",
    ),
    CameraMovementPreset(
        id="crash_zoom",
        name_ru="Crash Zoom (Стремительный наезд)",
        name_en="Crash Zoom (Snap Zoom)",
        category="dramatic",
        category_ru="Драматические",
        prompt_modifier="Rapid aggressive crash zoom snapping instantly from wide view onto the subject's eyes, dramatic sudden reveal.",
        description_ru="Резкий ударный зум в лицо или глаза, эффект внезапной опасности или открытия.",
        description_en="Instant rapid zoom snapping onto subject, dramatic punch.",
        icon="zap",
    ),

    # ── Dynamic / Динамика и экшн ──
    CameraMovementPreset(
        id="orbital_pan_cw",
        name_ru="Orbital Pan (Облёт по часовой)",
        name_en="Orbital Arc Pan (Clockwise)",
        category="dynamic",
        category_ru="Динамические",
        prompt_modifier="Smooth 360-degree orbital arc shot circling clockwise around the subject at eye level with rich dynamic parallax.",
        description_ru="Плавный кинематографический облет вокруг персонажа с сильным параллаксом фона.",
        description_en="Smooth orbital rotation around subject with foreground/background parallax.",
        icon="rotate-cw",
    ),
    CameraMovementPreset(
        id="orbital_pan_ccw",
        name_ru="Orbital Pan (Облёт против часовой)",
        name_en="Orbital Arc Pan (Counter-Clockwise)",
        category="dynamic",
        category_ru="Динамические",
        prompt_modifier="Smooth orbital arc shot sweeping counter-clockwise around the subject, keeping face centered in cinematic frame.",
        description_ru="Круговой облет влево, идеален для кульминационных моментов и смены направления сюжета.",
        description_en="Smooth counter-clockwise orbit maintaining subject center.",
        icon="rotate-ccw",
    ),
    CameraMovementPreset(
        id="tracking_shot",
        name_ru="Tracking Shot (Боковое слежение)",
        name_en="Lateral Tracking (Truck Shot)",
        category="dynamic",
        category_ru="Динамические",
        prompt_modifier="Lateral tracking dolly shot moving parallel alongside the moving subject, strong foreground-to-background parallax.",
        description_ru="Движение камеры сбоку параллельно идущему или бегущему объекту.",
        description_en="Lateral camera movement travelling parallel to the moving subject.",
        icon="move",
    ),
    CameraMovementPreset(
        id="follow_cam",
        name_ru="Follow Cam (Следование за героем)",
        name_en="Steadicam Follow Shot",
        category="dynamic",
        category_ru="Динамические",
        prompt_modifier="Steadicam tracking shot smoothly following behind the protagonist, maintaining fluid forward momentum and depth.",
        description_ru="Камера мягко следует за спиной героя, вовлекая зрителя в исследование пространства.",
        description_en="Steadicam following behind protagonist, drawing viewer into the world.",
        icon="corner-up-right",
    ),
    CameraMovementPreset(
        id="whip_pan",
        name_ru="Whip Pan (Хлыстовая панорама)",
        name_en="Whip Pan (Swish Pan)",
        category="dynamic",
        category_ru="Динамические",
        prompt_modifier="Fast kinetic whip pan transition with high motion blur snapping rapidly across the scene, seamless visual cut.",
        description_ru="Молниеносный поворот камеры со смазом движения, используется для резких переходов.",
        description_en="Rapid horizontal pan with motion blur, ideal for energetic transitions.",
        icon="chevrons-right",
    ),

    # ── Perspective / Ракурсы и углы обзора ──
    CameraMovementPreset(
        id="crane_up",
        name_ru="Crane Up (Подъём краном)",
        name_en="Crane Shot (Jib Boom Up)",
        category="perspective",
        category_ru="Ракурсные",
        prompt_modifier="Sweeping crane jib arm ascending vertically from ground level up to high-angle vantage point, revealing cinematic grandeur.",
        description_ru="Величественный взлет камеры от земли к общему плану сверху.",
        description_en="Ascending crane movement revealing the broader landscape.",
        icon="arrow-up",
    ),
    CameraMovementPreset(
        id="crane_down",
        name_ru="Crane Down (Спуск краном)",
        name_en="Crane Shot (Jib Boom Down)",
        category="perspective",
        category_ru="Ракурсные",
        prompt_modifier="Majestic crane jib descent gliding smoothly from high sky down to intimate character eye level.",
        description_ru="Плавный спуск камеры с высоты птичьего полета прямо к лицу героя.",
        description_en="Descending crane movement from sky down to subject level.",
        icon="arrow-down",
    ),
    CameraMovementPreset(
        id="dutch_angle",
        name_ru="Dutch Angle (Голландский угол)",
        name_en="Dutch Angle (Canted Tilt)",
        category="perspective",
        category_ru="Ракурсные",
        prompt_modifier="Dutch angle tilted camera roll 25 degrees off the horizon, conveying disorientation, psychological tension, and unease.",
        description_ru="Заваленный горизонт (наклон на 25 градусов), создающий тревогу и психологический дискомфорт.",
        description_en="Tilted camera angle evoking psychological imbalance and tension.",
        icon="compass",
    ),
    CameraMovementPreset(
        id="low_angle_hero",
        name_ru="Low Angle (Героический нижний ракурс)",
        name_en="Low-Angle Hero Tilt",
        category="perspective",
        category_ru="Ракурсные",
        prompt_modifier="Low-angle upward-looking tilt framing the subject from below, conveying power, dominance, and monumental presence.",
        description_ru="Взгляд на героя снизу вверх, придающий монументальность, силу и превосходство.",
        description_en="Upward-looking angle emphasizing dominance and stature.",
        icon="shield",
    ),
    CameraMovementPreset(
        id="overhead_god_view",
        name_ru="Top-Down (Вид строго сверху / Птичий полёт)",
        name_en="Overhead Bird's Eye (Top-Down)",
        category="perspective",
        category_ru="Ракурсные",
        prompt_modifier="High-angle top-down 90-degree zenith bird's-eye view looking directly down from above onto the geometry of the scene.",
        description_ru="Строгий взгляд под углом 90 градусов вниз, раскрывающий геометрию пространства.",
        description_en="Perpendicular 90-degree overhead angle looking straight down.",
        icon="map",
    ),
    CameraMovementPreset(
        id="pedestal_up",
        name_ru="Pedestal Up (Вертикальный подъём лифтом)",
        name_en="Pedestal Up (Elevator Rise)",
        category="perspective",
        category_ru="Ракурсные",
        prompt_modifier="Smooth vertical pedestal camera elevation straight up without tilting, revealing vertical architectural scale.",
        description_ru="Подъем камеры строго по вертикали без наклона, раскрывающий рост объекта или высоту здания.",
        description_en="Vertical upward movement without angle change.",
        icon="chevrons-up",
    ),

    # ── Atmospheric / Атмосферные и медитативные ──
    CameraMovementPreset(
        id="tilt_down",
        name_ru="Tilt Down (Панорама сверху вниз)",
        name_en="Tilt Down (Sky to Subject)",
        category="atmospheric",
        category_ru="Атмосферные",
        prompt_modifier="Slow vertical tilt-down camera movement starting from sky/ceiling, smoothly settling onto the character's eye line.",
        description_ru="Медленный наклон камеры сверху вниз, переносящий внимание с неба на происходящее.",
        description_en="Vertical tilt movement from above settling onto subject.",
        icon="arrow-down-left",
    ),
    CameraMovementPreset(
        id="slow_pan",
        name_ru="Slow Pan (Широкая плавная панорама)",
        name_en="Slow Pan Across",
        category="atmospheric",
        category_ru="Атмосферные",
        prompt_modifier="Slow, lyrical horizontal panoramic pan sweeping smoothly across the environment, establishing rich atmospheric depth.",
        description_ru="Неспешное горизонтальное сканирование пространства, передающее покой или эпичность.",
        description_en="Gentle horizontal scan across landscape or room.",
        icon="maximize-2",
    ),
    CameraMovementPreset(
        id="handheld_documentary",
        name_ru="Handheld (Живая ручная камера)",
        name_en="Handheld Documentary (Organic Shake)",
        category="atmospheric",
        category_ru="Атмосферные",
        prompt_modifier="Organic handheld camera motion with subtle natural micro-shakes and human breathing rhythm, documentary realism.",
        description_ru="Живая съемка «с рук» с дыханием оператора, создающая эффект присутствия и документальности.",
        description_en="Organic handheld movement with natural micro-tremors and breathing.",
        icon="activity",
    ),
    CameraMovementPreset(
        id="static_locked",
        name_ru="Static (Фиксированная камера на штативе)",
        name_en="Static Locked-Off (Tripod Shot)",
        category="atmospheric",
        category_ru="Атмосферные",
        prompt_modifier="Static locked-off shot on heavy tripod, absolute stability, no camera drift, allowing pure character motion within frame.",
        description_ru="Неподвижная камера на тяжелом штативе: полный покой и акцент только на действии внутри кадра.",
        description_en="Rock-solid tripod shot with zero camera drift.",
        icon="camera",
    ),
]

_PRESET_MAP: Dict[str, CameraMovementPreset] = {p.id: p for p in CAMERA_MOVEMENTS}


def get_camera_preset(preset_id: str) -> Optional[CameraMovementPreset]:
    """Возвращает пресет по ID."""
    return _PRESET_MAP.get(preset_id.lower())


def get_all_camera_presets() -> List[CameraMovementPreset]:
    """Возвращает полный список всех 20 пресетов."""
    return list(CAMERA_MOVEMENTS)


def apply_camera_movement_to_prompt(prompt: str, preset_id: Optional[str]) -> str:
    """Внедряет модификатор движения камеры в текст промпта, если он еще не присутствует."""
    if not preset_id or not prompt:
        return prompt
    preset = get_camera_preset(preset_id)
    if not preset:
        return prompt
    # Если промпт уже содержит ключевую фразу модификатора — не дублируем
    if preset.prompt_modifier.lower() in prompt.lower():
        return prompt
    # Если промпт оформлен как [0.0-1.0s]:
    if "[0.0-" in prompt:
        return f"{prompt}\nCamera Movement Directive: {preset.prompt_modifier}"
    return f"{prompt.rstrip('. ')}. Camera execution: {preset.prompt_modifier}"


def build_stabilizer_clause() -> str:
    """Возвращает обязательный блок стабилизации внешности и костной структуры лица (SYNTX Likeness Standard)."""
    return "Preserve exact facial bone structure, geometry, and identity throughout. Zero facial morphing, no plastic smoothing, no beautification filters. Stable photorealistic skin microtexture."


def build_motion_inertia_clause() -> str:
    """Возвращает кинематографический модификатор сохранения физической инерции (SYNTX Motion Inertia)."""
    return "Maintain continuous physical momentum and constant linear velocity throughout the entire shot. Smooth natural motion blur with zero sudden acceleration drops."


def build_storyboard_grid_prompt(
    quadrant_prompts: List[str],
    global_style: str = "",
) -> str:
    """Формирует промпт для 2x2 сториборд-сетки ракурсов (SYNTX Continuous Storyboard Transformation).

    Используется для генерации квадранта (Top-Left, Top-Right, Bottom-Left, Bottom-Right),
    который затем трансформируется видеомоделью в непрерывную панорамную сцену.
    """
    labels = ["Top-Left (Phase 1)", "Top-Right (Phase 2)", "Bottom-Left (Phase 3)", "Bottom-Right (Phase 4)"]
    lines = ["2x2 storyboard collage grid displaying 4 continuous sequential cinematic shots:"]
    for i, p in enumerate(quadrant_prompts[:4]):
        lbl = labels[i] if i < len(labels) else f"Quadrant {i+1}"
        lines.append(f"- {lbl}: {p.strip()}")
    if global_style:
        lines.append(f"Global aesthetic & color grading: {global_style.strip()}")
    lines.append("Consistent character appearance, unified lighting continuity across all four panels.")
    return "\n".join(lines)
