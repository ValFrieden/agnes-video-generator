import json, asyncio, websockets, os, shutil, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')

async def download_current_scene(scene_num_str):
    uri = 'ws://127.0.0.1:9222/devtools/page/0E7BD9B8349EB35B98566144FF51F46A'
    downloads_dir = 'C:\\Users\\Valeri\\Downloads'
    final_clip = f'd:\\Projects\\VideoGenerator\\kuda_idu_frames\\clips\\clip_{scene_num_str}.mp4'

    async with websockets.connect(uri, max_size=50*1024*1024) as ws:
        msg_id = 200

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {'id': msg_id, 'method': method}
            if params:
                payload['params'] = params
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get('id') == msg_id:
                    return resp.get('result', {})

        # Allow downloads
        await send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': downloads_dir
        })

        initial_files = set(os.listdir(downloads_dir))

        # Click download button
        click_btn = """(() => {
            const btn = document.querySelector('button[aria-label="Medien herunterladen"]');
            if (btn) { btn.click(); return true; }
            return false;
        })()"""
        r1 = await send('Runtime.evaluate', {'expression': click_btn, 'returnByValue': True})
        print('Click download icon:', r1.get('result', {}).get('value'))
        await asyncio.sleep(1.2)

        # Click 720p option
        click_720 = """(() => {
            const items = Array.from(document.querySelectorAll('button, [role="menuitem"], flow-menu-item'));
            const item720 = items.find(el => (el.innerText || '').includes('720p'));
            if (item720) {
                const b = item720.tagName === 'BUTTON' ? item720 : (item720.querySelector('button') || item720);
                b.click();
                return true;
            }
            return false;
        })()"""
        r2 = await send('Runtime.evaluate', {'expression': click_720, 'returnByValue': True})
        print('Click 720p option:', r2.get('result', {}).get('value'))

        # Monitor downloads
        print('Waiting for new mp4 in Downloads...')
        downloaded = None
        for i in range(25):
            await asyncio.sleep(1)
            current = os.listdir(downloads_dir)
            new_mp4s = [f for f in current if f not in initial_files and f.endswith('.mp4') and not f.endswith('.crdownload')]
            if new_mp4s:
                downloaded = os.path.join(downloads_dir, new_mp4s[0])
                print(f'Found downloaded file: {downloaded} ({os.path.getsize(downloaded)} bytes)')
                break

        if downloaded:
            if os.path.exists(final_clip):
                os.remove(final_clip)
            shutil.copy2(downloaded, final_clip)
            try: os.remove(downloaded)
            except: pass
            print(f'SUCCESS: Saved to {final_clip}')

            # Extract QA trio
            dur_str = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', final_clip], text=True).strip()
            dur = float(dur_str)

            t1 = str(round(dur * 0.25, 2))
            t2 = str(round(dur * 0.50, 2))
            t3 = str(round(dur * 0.75, 2))

            clips_dir = 'd:\\Projects\\VideoGenerator\\kuda_idu_frames\\clips'
            qa25 = os.path.join(clips_dir, f'clip_{scene_num_str}_qa25.png')
            qa50 = os.path.join(clips_dir, f'clip_{scene_num_str}_qa50.png')
            qa75 = os.path.join(clips_dir, f'clip_{scene_num_str}_qa75.png')
            trio = os.path.join(clips_dir, f'clip_{scene_num_str}_qa_trio.png')

            subprocess.run(['ffmpeg', '-y', '-ss', t1, '-i', final_clip, '-frames:v', '1', qa25], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['ffmpeg', '-y', '-ss', t2, '-i', final_clip, '-frames:v', '1', qa50], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['ffmpeg', '-y', '-ss', t3, '-i', final_clip, '-frames:v', '1', qa75], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['ffmpeg', '-y', '-i', qa25, '-i', qa50, '-i', qa75, '-filter_complex', '[0:v][1:v][2:v]hstack=inputs=3[v]', '-map', '[v]', trio], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f'QA Trio saved: {trio}')

            # Click Fertig to return to canvas
            click_fertig = """(() => {
                const f = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'Fertig');
                if (f) { f.click(); return true; }
                return false;
            })()"""
            await send('Runtime.evaluate', {'expression': click_fertig, 'returnByValue': True})
            print('Returned to canvas via Fertig.')

scene = sys.argv[1] if len(sys.argv) > 1 else '04'
asyncio.run(download_current_scene(scene))
