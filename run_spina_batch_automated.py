import json, asyncio, websockets, urllib.request, os, time, subprocess, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath('d:/Projects/VideoGenerator')
FRAMES_DIR = os.path.join(PROJECT_ROOT, 'kuda_idu_frames')
CLIPS_DIR = os.path.join(FRAMES_DIR, 'clips')
DOWNLOADS_DIR = os.path.abspath('C:/Users/Valeri/Downloads')

# Read motion prompts
prompts_file = os.path.join(FRAMES_DIR, 'motion_prompts.txt')
with open(prompts_file, 'r', encoding='utf-8') as f:
    prompt_lines = [line.strip() for line in f if line.strip()]

MOTION_PROMPTS = {}
for line in prompt_lines:
    parts = line.split('|')
    MOTION_PROMPTS[parts[0]] = parts[2]

def get_flow_ws():
    req = urllib.request.Request('http://127.0.0.1:9222/json/list')
    with urllib.request.urlopen(req, timeout=3) as resp:
        tabs = json.loads(resp.read().decode('utf-8'))
    for t in tabs:
        if 'flow.google.com' in t.get('url', ''):
            return t['webSocketDebuggerUrl']
    for t in tabs:
        if t.get('type') == 'page':
            return t['webSocketDebuggerUrl']
    raise RuntimeError('Flow page not found')

async def send_cmd(ws, msg_id, method, params=None):
    payload = {'id': msg_id, 'method': method}
    if params:
        payload['params'] = params
    await ws.send(json.dumps(payload))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=20)
        data = json.loads(raw)
        if data.get('id') == msg_id:
            return data.get('result', {})

async def run_scene(ws, scene_num_str):
    print(f"\n=======================================================", flush=True)
    print(f"🎬 PROCESSING SCENE {scene_num_str}", flush=True)
    print(f"=======================================================", flush=True)

    final_clip = os.path.join(CLIPS_DIR, f"clip_{scene_num_str}.mp4")
    if os.path.exists(final_clip) and os.path.getsize(final_clip) > 500000:
        print(f"Clip for scene {scene_num_str} already exists ({os.path.getsize(final_clip)} bytes). Skipping.", flush=True)
        return True

    ref_img_name = f"spina_{scene_num_str}.png"
    ref_img_path = os.path.join(FRAMES_DIR, ref_img_name)
    motion_prompt = MOTION_PROMPTS.get(scene_num_str, '')
    full_prompt = f"Generate video with Veo: {motion_prompt}. Authentic 35mm film still, Kodak Portra 400 grain, Roger Deakins natural lighting, human documentary realism, quiet emotion, 16:9 widescreen"

    msg_id = int(time.time() * 1000) % 100000

    # 1. Open Add Media dialog
    print(f"1. Opening Add Media dialog for {ref_img_name}...", flush=True)
    open_add_script = """(() => {
        const addBtn = document.querySelector('button[aria-label*="Bildelemente"], button[aria-label*="hinzufügen"]');
        if (addBtn) { addBtn.click(); return true; }
        return false;
    })()"""
    msg_id += 1
    await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': open_add_script, 'returnByValue': True})
    await asyncio.sleep(1.5)

    # 2. Check if asset already exists in assets list
    check_asset_script = f"""(() => {{
        const items = Array.from(document.querySelectorAll('*'));
        const found = items.find(el => el.innerText && el.innerText.trim() === '{ref_img_name}');
        if (found) {{
            found.click();
            return {{ present: true }};
        }}
        return {{ present: false }};
    }})()"""
    msg_id += 1
    res_asset = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': check_asset_script, 'returnByValue': True})
    val_asset = res_asset.get('result', {}).get('value', {})

    if not val_asset.get('present'):
        print(f"Uploading {ref_img_name} from disk...", flush=True)
        # We need Playwright or native file upload for filechooser if not present
        # In Node.js, run small upload helper
        upload_cmd = f'node tools/google-flow-browser-mcp/scripts/test_upload_spina01.mjs "{ref_img_path}"'
        # Let's handle upload via small node snippet
        node_upload = f"""
import {{ chromium }} from 'playwright';
async function up() {{
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const p = b.contexts()[0].pages()[0];
  const u = p.locator('button:has-text("Medien hoch"), [aria-label*="hochladen"]').first();
  const [fc] = await Promise.all([ p.waitForEvent('filechooser', {{ timeout: 15000 }}), u.click() ]);
  await fc.setFiles('{ref_img_path.replace(os.sep, "/")}');
  await p.waitForTimeout(6000);
  const target = p.locator('text="{ref_img_name}"').first();
  if (await target.isVisible()) await target.click();
  const add = p.locator('button:has-text("Zum Prompt hinzufügen")').first();
  if (await add.isVisible()) await add.click();
  await p.keyboard.press('Escape');
}}
up().catch(console.error);
"""
        with open('temp_upload.mjs', 'w', encoding='utf-8') as uf:
            uf.write(node_upload)
        subprocess.run('node temp_upload.mjs', shell=True, cwd=PROJECT_ROOT)
        if os.path.exists('temp_upload.mjs'):
            os.remove('temp_upload.mjs')
    else:
        print(f"Asset {ref_img_name} clicked! Adding to prompt...", flush=True)
        add_prompt_script = """(() => {
            const addBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Zum Prompt hinzufügen'));
            if (addBtn) { addBtn.click(); return true; }
            return false;
        })()"""
        msg_id += 1
        await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': add_prompt_script, 'returnByValue': True})
        await asyncio.sleep(1)
        # Close modal
        close_modal_script = """(() => {
            const closeBtn = document.querySelector('[role="dialog"] button[aria-label*="Schließen"], [role="dialog"] button:has-text("close")');
            if (closeBtn) closeBtn.click();
        })()"""
        msg_id += 1
        await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': close_modal_script, 'returnByValue': True})

    await asyncio.sleep(1)

    # 3. Insert prompt text
    print(f"3. Inserting prompt text...", flush=True)
    escaped_prompt = full_prompt.replace('"', '\\"').replace('\n', ' ')
    insert_prompt_script = f"""(() => {{
        const pm = document.querySelector('.ProseMirror');
        if (pm) {{
            pm.focus();
            pm.innerText = "{escaped_prompt}";
            pm.dispatchEvent(new Event('input', {{ bubbles: true }}));
            return true;
        }}
        return false;
    }})()"""
    msg_id += 1
    await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': insert_prompt_script, 'returnByValue': True})
    await asyncio.sleep(1)

    # 4. Click Submit
    print("4. Submitting video generation to Veo...", flush=True)
    initial_dl_count_script = """(() => document.querySelectorAll('[aria-label*="Herunterladen"], [aria-label*="Download"]').length)()"""
    msg_id += 1
    res_cnt = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': initial_dl_count_script, 'returnByValue': True})
    initial_dl_count = res_cnt.get('result', {}).get('value', 0)

    submit_script = """(() => {
        const btn = document.querySelector('button[aria-label*="Generierung starten"], button:has-text("arrow_forward")');
        if (btn) { btn.click(); return true; }
        return false;
    })()"""
    msg_id += 1
    await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': submit_script, 'returnByValue': True})
    await asyncio.sleep(3)

    # 5. Monitor generation loop until a new download button appears
    print(f"5. Monitoring generation (initial download buttons: {initial_dl_count})...", flush=True)
    before_downloads = set(os.listdir(DOWNLOADS_DIR))
    start_time = time.time()

    for poll_idx in range(45): # max 45 * 4s = 180s
        await asyncio.sleep(4)
        elapsed = int(time.time() - start_time)

        status_script = """(() => {
            const body = document.body.innerText || '';
            const match = body.match(/(\\d+)\\s*%/);
            const dlCount = document.querySelectorAll('[aria-label*="Herunterladen"], [aria-label*="Download"]').length;
            return {
                pct: match ? match[1] : null,
                dlCount,
                isGenerating: body.includes('Beenden') || body.includes('Generierung')
            };
        })()"""
        msg_id += 1
        st_res = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': status_script, 'returnByValue': True})
        st_val = st_res.get('result', {}).get('value', {})
        dl_now = st_val.get('dlCount', 0)
        pct = st_val.get('pct')

        if dl_now > initial_dl_count and elapsed > 25:
            print(f"[+{elapsed}s] New video card ready! Download button count: {dl_now}", flush=True)
            break
        elif pct:
            print(f"[+{elapsed}s] Progress: {pct}%", flush=True)
        else:
            print(f"[+{elapsed}s] Generating in Flow queue...", flush=True)

    await asyncio.sleep(2)

    # 6. Click download -> 720p
    print("6. Clicking download -> 720p...", flush=True)
    click_last_dl = """(() => {
        const btns = Array.from(document.querySelectorAll('[aria-label*="Herunterladen"], [aria-label*="Download"]'));
        if (btns.length > 0) {
            btns[btns.length - 1].click();
            return true;
        }
        return false;
    })()"""
    msg_id += 1
    await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': click_last_dl, 'returnByValue': True})
    await asyncio.sleep(1)

    click_720p = """(() => {
        const items = Array.from(document.querySelectorAll('[role="menuitem"], mat-option, .mat-mdc-menu-item, button'));
        const item720 = items.find(i => i.innerText && i.innerText.includes('720p'));
        if (item720) {
            item720.click();
            return true;
        }
        return false;
    })()"""
    msg_id += 1
    await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': click_720p, 'returnByValue': True})

    # 7. Wait for download in C:\Users\Valeri\Downloads
    print("7. Waiting for file to land in Downloads folder...", flush=True)
    downloaded_file = None
    for _ in range(30):
        await asyncio.sleep(1)
        cur = set(os.listdir(DOWNLOADS_DIR))
        diff = [f for f in (cur - before_downloads) if f.endswith('.mp4') and not f.endswith('.crdownload') and not f.endswith('.tmp')]
        if diff:
            downloaded_file = os.path.join(DOWNLOADS_DIR, diff[0])
            print(f"Downloaded: {downloaded_file} ({os.path.getsize(downloaded_file)} bytes)", flush=True)
            break

    if downloaded_file:
        if os.path.exists(final_clip):
            os.remove(final_clip)
        shutil.move(downloaded_file, final_clip)
        print(f"Moved to: {final_clip} ({os.path.getsize(final_clip)} bytes)", flush=True)

        # 8. QA verification frames
        print("8. Extracting QA verification frames (25%, 50%, 75%)...", flush=True)
        dur_out = subprocess.check_output(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{final_clip}"', shell=True, text=True).strip()
        dur = float(dur_out) if dur_out else 8.0

        qa25 = os.path.join(CLIPS_DIR, f"clip_{scene_num_str}_qa25.png")
        qa50 = os.path.join(CLIPS_DIR, f"clip_{scene_num_str}_qa50.png")
        qa75 = os.path.join(CLIPS_DIR, f"clip_{scene_num_str}_qa75.png")
        trio = os.path.join(CLIPS_DIR, f"clip_{scene_num_str}_qa_trio.png")

        t1 = round(dur * 0.25, 2)
        t2 = round(dur * 0.50, 2)
        t3 = round(dur * 0.75, 2)

        subprocess.run(f'ffmpeg -y -ss {t1} -i "{final_clip}" -frames:v 1 "{qa25}"', shell=True, capture_output=True)
        subprocess.run(f'ffmpeg -y -ss {t2} -i "{final_clip}" -frames:v 1 "{qa50}"', shell=True, capture_output=True)
        subprocess.run(f'ffmpeg -y -ss {t3} -i "{final_clip}" -frames:v 1 "{qa75}"', shell=True, capture_output=True)
        subprocess.run(f'ffmpeg -y -i "{qa25}" -i "{qa50}" -i "{qa75}" -filter_complex "[0:v][1:v][2:v]hstack=inputs=3[v]" -map "[v]" "{trio}"', shell=True, capture_output=True)

        print(f"QA contact sheet saved: {trio}", flush=True)
        print(f"✅ SCENE {scene_num_str} COMPLETE!\n", flush=True)
        return True
    else:
        print(f"❌ Failed to download video for scene {scene_num_str}!", flush=True)
        return False

async def main():
    start_scene = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    end_scene = int(sys.argv[2]) if len(sys.argv) > 2 else 16

    ws_url = get_flow_ws()
    print(f"Connected to Flow CDP: {ws_url}", flush=True)
    print(f"Batch generation starting for scenes {start_scene:02d} to {end_scene:02d}...", flush=True)

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        for num in range(start_scene, end_scene + 1):
            scene_str = f"{num:02d}"
            ok = await run_scene(ws, scene_str)
            if not ok:
                print(f"Warning: Scene {scene_str} encountered an issue. Pausing 5s before continuing...", flush=True)
            await asyncio.sleep(4)

    print("\n🎉 ALL TARGET SCENES IN BATCH PROCESSED!\n", flush=True)

if __name__ == '__main__':
    import sys
    asyncio.run(main())
