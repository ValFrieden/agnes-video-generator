"""
build_canonical_reference_sheets.py — Сборка детальных карт героев, дома, природы и предметов
на основе утвержденных мастер-кадров.
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_COLOR = (240, 240, 245)
ACCENT_COLOR = (245, 180, 50)
BG_COLOR = (15, 16, 20)
PANEL_BG = (25, 27, 34)
BORDER_COLOR = (45, 48, 60)

def draw_header(draw, title, subtitle, width, height=80):
    draw.rectangle([0, 0, width, height], fill=(20, 22, 28))
    draw.rectangle([0, height-2, width, height], fill=ACCENT_COLOR)
    draw.text((24, 18), title, fill=ACCENT_COLOR)
    draw.text((24, 46), subtitle, fill=(180, 185, 195))

# ─────────────────────────────────────────────────────────────
# 1. КАРТА ГЛАВНОГО ГЕРОЯ (МУЖЧИНА): МОЛОДОСТЬ VS СТАРОСТЬ + РАКУРСЫ
# ─────────────────────────────────────────────────────────────
def build_man_sheet():
    w, h = 1920, 1080
    sheet = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(sheet)
    draw_header(draw, "КАРТА ПЕРСОНАЖА: ГЛАВНЫЙ ГЕРОЙ (ОН / ОДИН ЧЕЛОВЕК СКВОЗЬ ВРЕМЯ)",
                "Фиксация анатомии, черт лица, формы носа, взгляда, роста (~182 см) и одежды: Молодость (1930-е, ~25 лет) ➔ Старость (Наши дни, ~68 лет)",
                w, 80)
    
    # 4 панели:
    # 1. Молодой (Анфас/3-4) из scene_02
    # 2. Молодой (Профиль в семье) из door_notches_family
    # 3. Пожилой (Анфас/3-4) из scene_06
    # 4. Пожилой (Профиль на свет) из scene_08
    # 5. Вид со спины / Полный рост из scene_09
    
    s02 = Image.open("door_frames/scene_02_newlyweds.jpg").convert("RGB")
    s03 = Image.open("door_frames/door_notches_family.jpg").convert("RGB")
    s06 = Image.open("door_frames/scene_06_golden_autumn.jpg").convert("RGB")
    s08 = Image.open("door_frames/scene_08_golden_beam.jpg").convert("RGB")
    s09 = Image.open("door_frames/scene_09_stepping_through.jpg").convert("RGB")

    # Crops
    # s02 man: around center-right
    man_young_face = s02.crop((780, 150, 1150, 560)).resize((350, 390))
    # s03 man profile: right side
    man_young_profile = s03.crop((1350, 40, 1880, 600)).resize((350, 390))
    # s06 man elderly face: center-left
    man_old_face = s06.crop((550, 160, 950, 580)).resize((350, 390))
    # s08 man elderly profile: left side
    man_old_profile = s08.crop((560, 140, 960, 560)).resize((350, 390))
    # s09 man back/full body: center
    man_old_back = s09.crop((750, 240, 1150, 950)).resize((340, 600))
    
    # Paste top row: Portraits
    # Col 1: Young Face
    sheet.paste(man_young_face, (40, 120))
    draw.rectangle([40, 120, 390, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 510, 390, 560], fill=PANEL_BG)
    draw.text((50, 525), "МОЛОДОСТЬ (~25 лет) · Анфас / 3/4", fill=ACCENT_COLOR)

    # Col 2: Young Profile
    sheet.paste(man_young_profile, (420, 120))
    draw.rectangle([420, 120, 770, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([420, 510, 770, 560], fill=PANEL_BG)
    draw.text((430, 525), "МОЛОДОСТЬ (~25 лет) · Профиль", fill=FONT_COLOR)

    # Col 3: Elderly Face
    sheet.paste(man_old_face, (800, 120))
    draw.rectangle([800, 120, 1150, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([800, 510, 1150, 560], fill=PANEL_BG)
    draw.text((810, 525), "СТАРОСТЬ (~68 лет) · Анфас / 3/4", fill=ACCENT_COLOR)

    # Col 4: Elderly Profile
    sheet.paste(man_old_profile, (1180, 120))
    draw.rectangle([1180, 120, 1530, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([1180, 510, 1530, 560], fill=PANEL_BG)
    draw.text((1190, 525), "СТАРОСТЬ (~68 лет) · Профиль / Взгляд", fill=FONT_COLOR)

    # Col 5 (Tall): Back & Full Body
    sheet.paste(man_old_back, (1560, 120))
    draw.rectangle([1560, 120, 1900, 720], outline=BORDER_COLOR, width=2)
    draw.rectangle([1560, 720, 1900, 770], fill=PANEL_BG)
    draw.text((1570, 735), "ВИД СО СПИНЫ / СИЛУЭТ", fill=FONT_COLOR)

    # Bottom area: Full body молодость vs старость + ДНК персонажа
    s02_full = s02.crop((700, 140, 1450, 1050)).resize((350, 420))
    sheet.paste(s02_full, (40, 600))
    draw.rectangle([40, 600, 390, 1020], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 1020, 390, 1060], fill=PANEL_BG)
    draw.text((50, 1032), "КОСТЮМ 1930-х · Полный рост", fill=FONT_COLOR)

    s06_full = s06.crop((400, 140, 1150, 1050)).resize((350, 420))
    sheet.paste(s06_full, (420, 600))
    draw.rectangle([420, 600, 770, 1020], outline=BORDER_COLOR, width=2)
    draw.rectangle([420, 1020, 770, 1060], fill=PANEL_BG)
    draw.text((430, 1032), "КАРДИГАН ОВСЯНКИ · Полный рост", fill=FONT_COLOR)

    # DNA Text Box
    draw.rectangle([800, 600, 1530, 1060], fill=PANEL_BG, outline=BORDER_COLOR, width=2)
    dna_lines = [
        "ФИКСИРОВАННЫЙ ДНК ГЕРОЯ (НЕ МЕНЯЕТСЯ ВО ВСЕХ СЦЕНАХ):",
        "",
        "• ЛИЦО: Прямой благородный нос, мягкие серо-карие глаза, добрые лучики морщин.",
        "• ВОЛОСЫ: Густые каштановые волнистые (в 25 лет) ➔ Аккуратные седые с зачесом (в 68 лет).",
        "• РОСТ И СТАТЬ: ~182 см, широкоплечий, спокойная уверенная осанка.",
        "• ОДЕЖДА МОЛОДОСТИ: Льняная светлая рубашка, винтажные шерстяные брюки, подтяжки.",
        "• ОДЕЖДА СТАРОСТИ: Вязаный уютный кардиган цвета овсянки (крупная вязка, шалевый воротник).",
        "• СКВОЗНОЙ ЯКОРЬ: Простое гладкое золотое обручальное кольцо на безымянном пальце правой руки.",
        "• ТАБУ: Никаких очков, никаких усов/бород лопатой (только легкая благородная щетина)."
    ]
    y_text = 620
    for line in dna_lines:
        col = ACCENT_COLOR if "ФИКСИРОВАННЫЙ" in line or "•" in line[:2] else FONT_COLOR
        draw.text((820, y_text), line, fill=col)
        y_text += 26

    sheet.save("door_frames/MAP_CHARACTER_MAN.jpg", quality=95)
    print("Saved door_frames/MAP_CHARACTER_MAN.jpg")

# ─────────────────────────────────────────────────────────────
# 2. КАРТА ГЛАВНОЙ ГЕРОИНИ (ЖЕНЩИНА): МОЛОДОСТЬ VS СТАРОСТЬ
# ─────────────────────────────────────────────────────────────
def build_woman_sheet():
    w, h = 1920, 1080
    sheet = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(sheet)
    draw_header(draw, "КАРТА ПЕРСОНАЖА: ГЛАВНАЯ ГЕРОИНЯ (ОНА / ОДНА ЖЕНЩИНА СКВОЗЬ ВРЕМЯ)",
                "Фиксация черт лица, мягкой улыбки, ямочек, светлых волнистых волос, роста (~168 см, до плеча мужа) и одежды",
                w, 80)

    s02 = Image.open("door_frames/scene_02_newlyweds.jpg").convert("RGB")
    s03 = Image.open("door_frames/door_notches_family.jpg").convert("RGB")
    s04 = Image.open("door_frames/scene_04_rain_return.jpg").convert("RGB")
    s06 = Image.open("door_frames/scene_06_golden_autumn.jpg").convert("RGB")
    s10 = Image.open("door_frames/scene_10_reunion_rejuvenation.jpg").convert("RGB")

    # Crops
    w_young_face = s02.crop((650, 210, 980, 580)).resize((350, 390))
    w_young_profile = s03.crop((420, 120, 850, 560)).resize((350, 390))
    w_mid_face = s04.crop((580, 130, 920, 500)).resize((350, 390))
    w_old_face = s06.crop((1050, 190, 1420, 580)).resize((350, 390))
    w_reunion = s10.crop((850, 200, 1350, 800)).resize((340, 600))

    # Row 1
    sheet.paste(w_young_face, (40, 120))
    draw.rectangle([40, 120, 390, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 510, 390, 560], fill=PANEL_BG)
    draw.text((50, 525), "МОЛОДОСТЬ (~23 года) · Невеста", fill=ACCENT_COLOR)

    sheet.paste(w_young_profile, (420, 120))
    draw.rectangle([420, 120, 770, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([420, 510, 770, 560], fill=PANEL_BG)
    draw.text((430, 525), "МОЛОДОСТЬ · Мать в семье", fill=FONT_COLOR)

    sheet.paste(w_mid_face, (800, 120))
    draw.rectangle([800, 120, 1150, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([800, 510, 1150, 560], fill=PANEL_BG)
    draw.text((810, 525), "ЗРЕЛОСТЬ (~38 лет) · Встреча в дождь", fill=FONT_COLOR)

    sheet.paste(w_old_face, (1180, 120))
    draw.rectangle([1180, 120, 1530, 510], outline=BORDER_COLOR, width=2)
    draw.rectangle([1180, 510, 1530, 560], fill=PANEL_BG)
    draw.text((1190, 525), "СТАРОСТЬ (~65 лет) · Осень, шаль", fill=ACCENT_COLOR)

    sheet.paste(w_reunion, (1560, 120))
    draw.rectangle([1560, 120, 1900, 720], outline=BORDER_COLOR, width=2)
    draw.rectangle([1560, 720, 1900, 770], fill=PANEL_BG)
    draw.text((1570, 735), "ОМОЛОЖЕНИЕ В ВЕЧНОСТИ", fill=FONT_COLOR)

    # Row 2: Full figures and DNA
    s02_fig = s02.crop((580, 200, 1350, 950)).resize((350, 420))
    sheet.paste(s02_fig, (40, 600))
    draw.rectangle([40, 600, 390, 1020], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 1020, 390, 1060], fill=PANEL_BG)
    draw.text((50, 1032), "СВАДЕБНЫЙ ОБРАЗ (1930-е)", fill=FONT_COLOR)

    s06_fig = s06.crop((950, 190, 1550, 1000)).resize((350, 420))
    sheet.paste(s06_fig, (420, 600))
    draw.rectangle([420, 600, 770, 1020], outline=BORDER_COLOR, width=2)
    draw.rectangle([420, 1020, 770, 1060], fill=PANEL_BG)
    draw.text((430, 1032), "ОБРАЗ С ШАЛЬЮ (Старость)", fill=FONT_COLOR)

    # DNA Text Box
    draw.rectangle([800, 600, 1530, 1060], fill=PANEL_BG, outline=BORDER_COLOR, width=2)
    dna_w = [
        "ФИКСИРОВАННЫЙ ДНК ГЕРОИНИ (НЕ МЕНЯЕТСЯ ВО ВСЕХ СЦЕНАХ):",
        "",
        "• ЛИЦО: Тонкие нежные черты лица, сияющая добрая улыбка, теплый ясный взгляд.",
        "• ВОЛОСЫ: Волнистые золотисто-светлые (в юности) ➔ Серебристые пряди, уложенные назад.",
        "• РОСТ: ~168 см (всегда ниже мужа, достает ему точно до плеча в совместных сценах).",
        "• ОДЕЖДА МОЛОДОСТИ: Простое светлое хлопковое платье с кружевным воротничком.",
        "• ОДЕЖДА ЗРЕЛОСТИ И СТАРОСТИ: Вязаная шерстяная шаль лавандового оттенка поверх платья.",
        "• СКВОЗНОЙ ЯКОРЬ: Тонкое золотое обручальное кольцо, парное с кольцом мужа.",
        "• ЭМОЦИОНАЛЬНЫЙ СТИЛЬ: Безмятежность, тихая глубокая нежность, безусловное доверие."
    ]
    y_text = 620
    for line in dna_w:
        col = ACCENT_COLOR if "ФИКСИРОВАННЫЙ" in line or "•" in line[:2] else FONT_COLOR
        draw.text((820, y_text), line, fill=col)
        y_text += 26

    sheet.save("door_frames/MAP_CHARACTER_WOMAN.jpg", quality=95)
    print("Saved door_frames/MAP_CHARACTER_WOMAN.jpg")

# ─────────────────────────────────────────────────────────────
# 3. КАРТА ДОМА, ЛОКАЦИИ И ПРИРОДЫ (ЕДИНОЕ МЕСТО БЕЗ АРТЕФАКТОВ)
# ─────────────────────────────────────────────────────────────
def build_environment_sheet():
    w, h = 1920, 1080
    sheet = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(sheet)
    draw_header(draw, "КАРТА МЕСТНОСТИ, ДОМА И ПРИРОДЫ (ФИКСАЦИЯ ОДНОЙ ТОПОГРАФИИ)",
                "Закон единого ландшафта: старый дом на пологом зеленом холме, старая яблоня слева, луг с ромашками и люпинами. ЗАПРЕЩЕНЫ чужие горы и овраги!",
                w, 80)

    s01 = Image.open("door_frames/scene_01_intro.jpg").convert("RGB")
    s_anchor = Image.open("door_frames/door_master_anchor.jpg").convert("RGB")
    s03 = Image.open("door_frames/door_notches_family.jpg").convert("RGB")
    s05 = Image.open("door_frames/scene_05_summer_rain.jpg").convert("RGB")
    s12 = Image.open("door_frames/scene_12_light_remains.jpg").convert("RGB")

    # 1. Общий план природы и дома (Рассвет)
    panel1 = s01.resize((580, 330))
    sheet.paste(panel1, (40, 120))
    draw.rectangle([40, 120, 620, 450], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 450, 620, 500], fill=PANEL_BG)
    draw.text((50, 465), "1. ТОПОГРАФИЯ СНАРУЖИ: Пологий холм, яблоня слева, луг", fill=ACCENT_COLOR)

    # 2. Фасад дома и крыльцо крупно
    panel2 = s_anchor.crop((0, 0, 1920, 1080)).resize((580, 330))
    sheet.paste(panel2, (660, 120))
    draw.rectangle([660, 120, 1240, 450], outline=BORDER_COLOR, width=2)
    draw.rectangle([660, 450, 1240, 500], fill=PANEL_BG)
    draw.text((670, 465), "2. КРЫЛЬЦО И ДВЕРЬ: Дубовая дверь, каменные ступени, косяк", fill=ACCENT_COLOR)

    # 3. Крыльцо под летним дождем
    panel3 = s05.resize((580, 330))
    sheet.paste(panel3, (1280, 120))
    draw.rectangle([1280, 120, 1860, 450], outline=BORDER_COLOR, width=2)
    draw.rectangle([1280, 450, 1860, 500], fill=PANEL_BG)
    draw.text((1290, 465), "3. КРЫЛЬЦО В ДОЖДЬ: Дощатый настил, деревянные колонны", fill=FONT_COLOR)

    # 4. Интерьер прихожей и косяк
    panel4 = s03.resize((580, 330))
    sheet.paste(panel4, (40, 540))
    draw.rectangle([40, 540, 620, 870], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 870, 620, 920], fill=PANEL_BG)
    draw.text((50, 885), "4. ИНТЕРЬЕР И КОСЯК: Окно с занавесками, деревянный столб", fill=ACCENT_COLOR)

    # 5. Ночной дом и полоска света (Финал)
    panel5 = s12.resize((580, 330))
    sheet.paste(panel5, (660, 540))
    draw.rectangle([660, 540, 1240, 870], outline=BORDER_COLOR, width=2)
    draw.rectangle([660, 870, 1240, 920], fill=PANEL_BG)
    draw.text((670, 885), "5. НОЧНОЙ ДОМ (Финал): Полоска света из приоткрытой двери", fill=FONT_COLOR)

    # Rules Panel
    draw.rectangle([1280, 540, 1860, 1040], fill=PANEL_BG, outline=BORDER_COLOR, width=2)
    rules = [
        "СТРОГИЕ ЗАКОНЫ ЛОКАЦИИ И МЕСТНОСТИ:",
        "",
        "1. ЕДИНАЯ ТОПОГРАФИЯ (NO RANDOM MOUNTAINS):",
        "   Никаких острых скалистых гор или глубоких каньонов!",
        "   Только мягкие зеленые покатые холмы и луг с полевыми цветами.",
        "",
        "2. ДЕРЕВО СЛЕВА (THE APPLE TREE):",
        "   Слева от дома всегда стоит одна старая ветвистая яблоня.",
        "",
        "3. АРХИТЕКТУРА ДОМА (THE HOUSE):",
        "   • Материал: потемневший состаренный деревянный брус.",
        "   • Крыша: скатная металлическая крыша с кирпичной трубой.",
        "   • Крыльцо: крытая веранда с деревянными перилами и каменным цоколем.",
        "",
        "4. ДВЕРЬ (HERO OBJECT):",
        "   Массивная дубовая дверь с латунной резной ручкой.",
        "   Справа от входа — косяк с зарубками детского роста.",
        "",
        "5. ОСВЕЩЕНИЕ: Естественное солнце (рассвет / полдень / закат / ночь)."
    ]
    y_text = 560
    for line in rules:
        col = ACCENT_COLOR if any(k in line for k in ["ЗАКОНЫ", "1.", "2.", "3.", "4.", "5."]) else FONT_COLOR
        draw.text((1300, y_text), line, fill=col)
        y_text += 22

    sheet.save("door_frames/MAP_ENVIRONMENT_AND_HOUSE.jpg", quality=95)
    print("Saved door_frames/MAP_ENVIRONMENT_AND_HOUSE.jpg")

# ─────────────────────────────────────────────────────────────
# 4. КАРТА СКВОЗНЫХ ПРЕДМЕТОВ (PROPS & OBJECTS BIBLE)
# ─────────────────────────────────────────────────────────────
def build_props_sheet():
    w, h = 1920, 1080
    sheet = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(sheet)
    draw_header(draw, "КАРТА СКВОЗНЫХ ПРЕДМЕТОВ И МАТЕРИАЛЬНЫХ СИМВОЛОВ (PROPS MAP)",
                "Тактильные якоря, связывающие разные эпохи: Дверь, Зарубки роста, Золотое кольцо, Кардиган, Чайные чашки",
                w, 80)

    s_anchor = Image.open("door_frames/door_master_anchor.jpg").convert("RGB")
    s07 = Image.open("door_frames/scene_07_touching_notches.jpg").convert("RGB")
    s08 = Image.open("door_frames/scene_08_golden_beam.jpg").convert("RGB")
    s06 = Image.open("door_frames/scene_06_golden_autumn.jpg").convert("RGB")

    # Item 1: Косяк с зарубками крупно
    p1 = s07.crop((0, 0, 1920, 1080)).resize((580, 330))
    sheet.paste(p1, (40, 120))
    draw.rectangle([40, 120, 620, 450], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 450, 620, 500], fill=PANEL_BG)
    draw.text((50, 465), "1. КОСЯК С ЗАРУБКАМИ: Вырезанные даты и имена детей (1941-1985)", fill=ACCENT_COLOR)

    # Item 2: Латунная ручка двери и скважина
    p2 = s08.crop((1100, 300, 1850, 800)).resize((580, 330))
    sheet.paste(p2, (660, 120))
    draw.rectangle([660, 120, 1240, 450], outline=BORDER_COLOR, width=2)
    draw.rectangle([660, 450, 1240, 500], fill=PANEL_BG)
    draw.text((670, 465), "2. ЗАМОЧНАЯ СКВАЖИНА: Латунная старинная накладка и ручка", fill=ACCENT_COLOR)

    # Item 3: Фарфоровые чашки и яблоки
    p3 = s06.crop((0, 700, 550, 1080)).resize((580, 330))
    sheet.paste(p3, (1280, 120))
    draw.rectangle([1280, 120, 1860, 450], outline=BORDER_COLOR, width=2)
    draw.rectangle([1280, 450, 1860, 500], fill=PANEL_BG)
    draw.text((1290, 465), "3. ЧАЙНЫЙ СТОЛИК: Две фарфоровые чашки, тарелка с яблоками", fill=FONT_COLOR)

    # Item 4: Кардиган и обручальное кольцо
    p4 = s07.crop((1000, 300, 1850, 850)).resize((580, 330))
    sheet.paste(p4, (40, 540))
    draw.rectangle([40, 540, 620, 870], outline=BORDER_COLOR, width=2)
    draw.rectangle([40, 870, 620, 920], fill=PANEL_BG)
    draw.text((50, 885), "4. ВЯЗАНЫЙ КАРДИГАН И ЗОЛОТОЕ КОЛЬЦО: Шерстяная вязка цвета овсянки", fill=ACCENT_COLOR)

    # Item 5: Крыльцо и цветочные горшки
    p5 = s_anchor.crop((0, 400, 800, 1080)).resize((580, 330))
    sheet.paste(p5, (660, 540))
    draw.rectangle([660, 540, 1240, 870], outline=BORDER_COLOR, width=2)
    draw.rectangle([660, 870, 1240, 920], fill=PANEL_BG)
    draw.text((50, 885), "5. ВЕРАНДА: Глиняные горшки с полевыми цветами, плетеное кресло", fill=FONT_COLOR)

    # Description Box
    draw.rectangle([1280, 540, 1860, 1040], fill=PANEL_BG, outline=BORDER_COLOR, width=2)
    props_desc = [
        "ОПИСАНИЕ СКВОЗНЫХ ПРЕДМЕТОВ КЛИПА:",
        "",
        "• КОСЯК С ЗАРУБКАМИ (Main Prop):",
        "  Вертикальный дубовый брус справа от входа.",
        "  На нем ножом вырезаны насечки роста и даты:",
        "  '1944 Arthur', '1945', '1969', '1981 Sarah', 'Tommy'.",
        "  Дерево потемнело от сотен прикосновений рук.",
        "",
        "• ДВЕРЬ ДОМА (Hero Door):",
        "  Тяжелая входная дверь из массива дуба, темный лак,",
        "  старинная латунная фигурная ручка и скважина.",
        "",
        "• ОБРУЧАЛЬНЫЕ КОЛЬЦА:",
        "  Простые гладкие кольца из желтого золота без камней.",
        "  На пальце героя и героини на протяжении всей жизни.",
        "",
        "• ОДЕЖДА:",
        "  Кардиган цвета овсянки крупной вязки (Он).",
        "  Лавандовая вязаная шерстяная шаль (Она)."
    ]
    y_text = 560
    for line in props_desc:
        col = ACCENT_COLOR if "•" in line[:2] or "ОПИСАНИЕ" in line else FONT_COLOR
        draw.text((1300, y_text), line, fill=col)
        y_text += 22

    sheet.save("door_frames/MAP_KEY_PROPS.jpg", quality=95)
    print("Saved door_frames/MAP_KEY_PROPS.jpg")

if __name__ == "__main__":
    build_man_sheet()
    build_woman_sheet()
    build_environment_sheet()
    build_props_sheet()
    print("All 4 Reference Bibles successfully built!")
