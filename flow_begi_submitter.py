"""flow_begi_submitter.py — Generiert Szenen fuer 'Беги за солнцем' mit Google Flow & Veo 3.1.
Alle Prompts basieren auf dem genehmigten, vermenschlichten Drehbuch und nutzen die konsistente Stil- und Charakter-DNA:
- Stil: Vintage hand-painted cel animation style, Edward Hopper lighting, gouache textures
- Charakter: Solitary traveler in dark slate coat, canary-yellow umbrella, bare face, no eyeglasses
- Bewegung: Subtile organische Kamera, Regen, Atmung, Lichtpulsieren (Zero-Distortion)
"""

import json
import asyncio
import websockets
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


WS_URI = 'ws://127.0.0.1:9222/devtools/page/AD5A6E3BE8C8038933692DF3BD5550E3'

STYLE_DNA = (
    "Vintage hand-painted cel animation style, gouache painted backgrounds, 16:9 widescreen, "
    "cinematic Edward Hopper lighting, slate blue and glowing warm amber gold palette, "
    "atmospheric film grain, wet reflections. "
    "Solitary traveler in dark slate coat, vibrant glowing canary-yellow umbrella, bare face, no eyeglasses. "
    "Consistent character across all scenes."
)

BEGI_FLOW_SCENES = [
    {
        "scene": 2,
        "title": "Куплет 1: Путник берет зонт",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 02: Medium shot from behind of solitary traveler standing by a wet wooden park bench on an embankment, "
            "raising the open glowing canary-yellow umbrella against drifting misty rain. "
            "Warm amber light radiates from beneath the umbrella onto wet cobblestones, gentle coat breathing motion, "
            "subtle rain streaks, no walking, static stance."
        )
    },
    {
        "scene": 3,
        "title": "Куплет 1: Первые лучи в лужах",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 03: Low-angle close-up of wet cobblestone pavement with expanding puddle ripples reflecting dark indigo sky. "
            "A sharp diagonal shaft of warm golden morning sunlight pierces the mist, striking the water surface with golden amber ripples. "
            "Smooth water splashes, glistening droplets, cinematic lighting."
        )
    },
    {
        "scene": 5,
        "title": "Прехорус: Открыто окно",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 05: Historic brick townhouse facade in cool rain: third-floor round attic window swung open, "
            "sheer white curtains fluttering gently in warm window breeze, soft amber golden sunlight spilling outward into misty rain, "
            "below in the alley a yellow umbrella slowly moving past, atmospheric raindrops."
        )
    },
    {
        "scene": 6,
        "title": "Припев 1: Граница тьмы и света",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 06: Grand stone bridge across a misty river at dawn. Solitary traveler centered on the bridge holding the yellow umbrella, "
            "standing at the exact border where stormy indigo storm clouds break into brilliant golden sunrise rays. "
            "Wind gently ruffling coat hem, glowing light rays spreading across clouds, majestic stillness."
        )
    },
    {
        "scene": 7,
        "title": "Припев 1: Тепло на лице",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 07: Emotional close-up profile of the traveler's calm face under the yellow umbrella edge. "
            "Wet dark hair, determined gentle eyes reflecting golden dawn rays, a single rain droplet trickles down cheek, "
            "warm side-lighting illuminating skin, closed lips, subtle natural breathing, cinematic fine art portrait."
        )
    },
    {
        "scene": 8,
        "title": "Куплет 2: Преследование теней",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 08: Ancient arched stone colonnade in misty twilight. Traveler stands holding the glowing yellow umbrella, "
            "as deep blue evening shadows stretch across stone pillars. Warm amber light from the umbrella pushes back the cool gloom, "
            "swirling low ground fog, painterly textures."
        )
    },
    {
        "scene": 9,
        "title": "Куплет 2: Зонт закрывается",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 09: River overlook promenade. Rain has stopped, only sparkling sun mist remains. "
            "Traveler calmly lowers and folds the bright yellow umbrella, holding it resting against arm. "
            "Golden sunlight breaking over glistening wet balustrade, peaceful breathing motion."
        )
    },
    {
        "scene": 10,
        "title": "Припев 2: Золото над крышами",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 10: Low angle looking up toward old cathedral spires and slate rooftops. "
            "Golden morning light breaking through parting clouds, steam rising from wet roof tiles, "
            "warm golden bokeh dust floating through the air, magnificent painterly cel animation."
        )
    },
    {
        "scene": 11,
        "title": "Припев 2: Торжество утра",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 11: High panoramic rooftop view across the historic city. Traveler stands on rooftop terrace holding yellow umbrella, "
            "looking out at radiant golden sunrise sweeping across wet slate roofs, blue sky expanding, "
            "sparkling water gutters, gentle breeze."
        )
    },
    {
        "scene": 12,
        "title": "Финал: Солнечная скамья",
        "prompt": (
            f"Cinematic hand-painted cel animation video, {STYLE_DNA}. "
            "Scene 12: Returning to the park promenade bench from Scene 01. The wooden bench is now completely dry in warm bright summer sunlight. "
            "Wildflowers blooming in grass around bench, gentle sunny breeze swaying blossoms, serene triumphant peace, no people, purely warm summer light."
        )
    }
]

async def submit_prompt(ws, prompt_text):
    focus_script = """(() => {
        const pm = document.querySelector('div.ProseMirror');
        if (!pm) return false;
        pm.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        return true;
    })()"""
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': focus_script, 'returnByValue': True}}))
    await ws.recv()

    await ws.send(json.dumps({
        'id': 2,
        'method': 'Input.insertText',
        'params': {'text': prompt_text}
    }))
    await ws.recv()
    await asyncio.sleep(0.5)

    click_script = """(() => {
        const sendBtn = Array.from(document.querySelectorAll('button')).find(b => 
            b.innerHTML.includes('arrow_forward') || (b.innerText || '').includes('arrow_forward')
        );
        if (sendBtn && !sendBtn.disabled) {
            sendBtn.click();
            return { success: true };
        }
        return { success: false, disabled: sendBtn ? sendBtn.disabled : null };
    })()"""
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
    resp = await ws.recv()

    # Also send Enter to trigger assistant if sendBtn wasn't enough
    await ws.send(json.dumps({
        'id': 4,
        'method': 'Input.dispatchKeyEvent',
        'params': {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}
    }))
    await ws.recv()
    await ws.send(json.dumps({
        'id': 5,
        'method': 'Input.dispatchKeyEvent',
        'params': {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}
    }))
    await ws.recv()
    return resp

async def main():
    print(f"Connecting to Flow CDP: {WS_URI}...", flush=True)
    async with websockets.connect(WS_URI) as ws:
        for item in BEGI_FLOW_SCENES:
            s_num = item["scene"]
            print(f"\nSubmitting Scene {s_num:02d} [{item['title']}]...", flush=True)
            res = await submit_prompt(ws, item["prompt"])
            print(f"Scene {s_num:02d} submitted: {res}", flush=True)
            await asyncio.sleep(3)

if __name__ == '__main__':
    asyncio.run(main())
