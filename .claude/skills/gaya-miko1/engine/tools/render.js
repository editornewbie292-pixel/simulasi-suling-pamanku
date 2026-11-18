// Render a /gaya-miko1 reel. Run from the reel folder:
//   node <engine>/tools/render.js stills 1.5,3.2      -> stills/s_1.50.jpg ...
//   node <engine>/tools/render.js segments 0,4,8      -> seg/shot_00.mp4 ...
// Env: FPS (30 default, 60 for extra smooth), CHROME (browser binary), KIT (kit folder; found from the engine otherwise)
// The page is served over a tiny local web server so three.js ES modules load from kit/node_modules/three.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const ENGINE = path.resolve(__dirname, '..');
let KIT = process.env.KIT || path.resolve(ENGINE, '../../../kit');
if (!fs.existsSync(path.join(KIT, 'node_modules')) && fs.existsSync(path.join(ENGINE, 'kitpath.txt'))) KIT = fs.readFileSync(path.join(ENGINE, 'kitpath.txt'), 'utf8').trim();
const THREE_DIR = path.join(KIT, 'node_modules', 'three');
const FPS = Number(process.env.FPS || 30);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.png': 'image/png', '.jpg': 'image/jpeg' };

function serve(root) {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const u = decodeURIComponent(req.url.split('?')[0]);
      const f = u.startsWith('/three/') ? path.join(THREE_DIR, u.slice(7)) : path.join(root, u);
      fs.readFile(f, (err, buf) => {
        if (err) { rsp.writeHead(404); rsp.end(); return; }
        rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); rsp.end(buf);
      });
    }).listen(0, '127.0.0.1', () => res(srv));
  });
}

(async () => {
  const mode = process.argv[2];
  const srv = await serve(process.cwd());
  const browser = await chromium.launch({ ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}),
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { const s = m.text(); if (!/GPU stall|GL Driver/.test(s)) console.log('[page]', s); });
  page.on('pageerror', e => console.log('[err]', e.message));
  await page.goto(`http://127.0.0.1:${srv.address().port}/web/index.html?fps=${FPS}`);
  await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  const total = await page.evaluate(() => window.TOTAL_FRAMES);
  if (mode === 'stills') {
    const times = process.argv[3].split(',').map(Number);
    fs.mkdirSync('stills', { recursive: true });
    for (const t of times) {
      const d = await page.evaluate(f => { renderFrame(f); return grab(.92); }, Math.round(t * FPS));
      fs.writeFileSync(`stills/s_${t.toFixed(2)}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
    }
  } else if (mode === 'segments') {
    const ids = process.argv[3].split(',').map(Number);
    const spans = await page.evaluate(() => window.SHOT_SPANS);
    fs.mkdirSync('seg', { recursive: true });
    for (const id of ids) {
      const f0 = Math.round(spans[id][0] * FPS), f1 = id === spans.length - 1 ? total : Math.round(spans[id][1] * FPS);
      const tmp = `seg/shot_${String(id).padStart(2, '0')}.part.mp4`, fin = tmp.replace('.part', '');
      const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
      const t0 = Date.now();
      for (let f = f0; f < f1; f++) {
        const d = await page.evaluate(f => { renderFrame(f); return grab(.95); }, f);
        if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
      }
      ff.stdin.end(); const code = await new Promise(r => ff.on('close', r));
      if (code === 0) fs.renameSync(tmp, fin); else console.log('ffmpeg failed', id);
      console.log('done shot', id, f1 - f0, 'frames', ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
  }
  await browser.close(); srv.close();
})();
