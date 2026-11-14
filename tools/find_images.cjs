const fs = require('fs');
const path = require('path');

function walk(dir, list = []) {
  for (const f of fs.readdirSync(dir)) {
    if (f === 'node_modules' || f === '.git' || f === '.venv') continue;
    const full = path.join(dir, f);
    try {
      const st = fs.statSync(full);
      if (st.isDirectory()) walk(full, list);
      else if (/\.(png|jpg|jpeg|webp)$/i.test(f) && st.mtimeMs > Date.now() - 4 * 3600 * 1000) {
        list.push({ path: full, size: st.size, time: new Date(st.mtimeMs).toISOString() });
      }
    } catch {}
  }
  return list;
}

const res = walk('d:/Projects/VideoGenerator').sort((a, b) => b.time.localeCompare(a.time));
console.log(JSON.stringify(res.slice(0, 25), null, 2));
