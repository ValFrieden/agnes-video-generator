import os
import sys

def check_file(path):
    print("Checking:", path)
    if not os.path.exists(path):
        print("Not found")
        return
    size = os.path.getsize(path)
    print(f"Size: {size} bytes")
    # Read first 100KB to look for ID3 tags and lyrics
    with open(path, "rb") as f:
        data = f.read(min(size, 200000))
    
    # Simple search for text strings in ID3
    try:
        # Check ID3v2
        if data[:3] == b'ID3':
            print("ID3v2 tag present")
            # try to decode strings
            # search for common fields: USLT (lyrics), TIT2, TPE1, COMM
            import re
            strings = re.findall(rb'[\x20-\x7e\xd0-\xd1\x80-\xbf]{4,}', data)
            found = []
            for s in strings:
                try:
                    decoded = s.decode('utf-8')
                    if len(decoded.strip()) > 3:
                        found.append(decoded)
                except:
                    pass
            print("Text fragments in ID3:")
            for f in found[:30]:
                print("  -", f)
    except Exception as e:
        print("Error reading tags:", e)
target_path = "song_begi.mp3" if os.path.exists("song_begi.mp3") else r"C:\Users\Valeri\Downloads\Беги за солнцем.mp3"
check_file(target_path)
