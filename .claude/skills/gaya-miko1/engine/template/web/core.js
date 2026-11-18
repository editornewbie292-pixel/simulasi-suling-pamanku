// ---------- /gaya-miko1 core: renderer, shots, camera, light moods, captions, grade ----------
import * as THREE from 'three';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
export { THREE };

export const W = 1080, H = 1920;
export const FPS = Number(new URLSearchParams(location.search).get('fps') || 30);
export const INK = '#1e1021';
export const TAU = Math.PI * 2;
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const inv = (a, b, v) => clamp((v - a) / (b - a));
export const smooth = t => t * t * t * (t * (t * 6 - 15) + 10);          // smootherstep: the default for camera moves
export const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
export const easeOut = t => 1 - Math.pow(1 - t, 3);
export const easeIn = t => t * t * t;
export const backOut = t => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
// keyframes [[t, value(number|array), easing?], ...]
export function kf(t, keys, fn = smooth) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [t0, v0] = keys[i], [t1, v1] = keys[i + 1];
    if (t <= t1) { const e = (keys[i + 1][2] || fn)(inv(t0, t1, t)); return Array.isArray(v0) ? v0.map((x, j) => lerp(x, v1[j], e)) : lerp(v0, v1, e); }
  }
  return keys[keys.length - 1][1];
}
export function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 100000) / 100000; }; }
// smooth low-frequency wobble, for a living camera
export const wob = (t, seed = 0) => Math.sin(t * .53 + seed) * .55 + Math.sin(t * .31 + 1.7 + seed * 2) * .45;

// ---------- words: shots are timed by the voice ----------
export const WORDS = window.WORDS || [];
const normW = s => s.toLowerCase().replace(/[^0-9a-zà-ÿ]/g, '');
// T('hujan') = start of the first "hujan"; T('hujan', 2) = the second one; T(12) = word index 12. T.end(...) = its end.
export function T(w, n = 1) {
  if (typeof w === 'number') return WORDS[Math.min(w, WORDS.length - 1)].s;
  let k = 0; for (const x of WORDS) if (normW(x.w) === normW(w) && ++k === n) return x.s;
  console.log('T(): word not found: ' + w + ' #' + n); return 0;
}
T.end = (w, n = 1) => { if (typeof w === 'number') return WORDS[w].e; let k = 0; for (const x of WORDS) if (normW(x.w) === normW(w) && ++k === n) return x.e; return 0; };
// the start of script line i (shots usually begin a hair before the line)
export const L = (i, pre = .12) => { const x = WORDS.find(w => w.line === i); return x ? Math.max(0, x.s - pre) : 0; };
export const DUR = (window.VO_DUR || (WORDS.length ? WORDS[WORDS.length - 1].e : 10)) + .7;

// ---------- renderer ----------
const glc = document.createElement('canvas'); glc.width = W; glc.height = H;
export const renderer = new THREE.WebGLRenderer({ canvas: glc, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.0;
const rt = new THREE.WebGLRenderTarget(W, H, { samples: 4, type: THREE.HalfFloatType });
const composer = new EffectComposer(renderer, rt); composer.setPixelRatio(1); composer.setSize(W, H);
const renderPass = new RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera());
const bloomPass = new UnrealBloomPass(new THREE.Vector2(W, H), 1, .6, .7);
composer.addPass(renderPass); composer.addPass(bloomPass); composer.addPass(new OutputPass());

// ---------- materials, ink outlines ----------
const gradTex = (() => { const d = new Uint8Array([90, 170, 230, 255]); const t = new THREE.DataTexture(d, 4, 1, THREE.RedFormat); t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true; return t; })();
const matCache = new Map();
// soft cel material. opts: {map, emissive, emissiveIntensity, side, transparent, opacity}
export function mat(color, opts = {}) {
  const key = !opts.map && Object.keys(opts).length === 0 ? color : null;
  if (key && matCache.has(key)) return matCache.get(key);
  const m = new THREE.MeshToonMaterial(Object.assign({ color, gradientMap: gradTex }, opts));
  if (key) matCache.set(key, m); return m;
}
export const glowMat = (color, k = 2.2) => new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), toneMapped: false });
const lineMats = new Map();
function lineMat(w, col) { const k = w + col; if (!lineMats.has(k)) lineMats.set(k, new LineMaterial({ color: col, linewidth: w, resolution: new THREE.Vector2(W, H) })); return lineMats.get(k); }
// cartoon ink edges on a mesh (crease angle in degrees)
export function ink(mesh, w = 3, col = INK, angle = 30) {
  const g = new LineSegmentsGeometry().fromEdgesGeometry(new THREE.EdgesGeometry(mesh.geometry, angle));
  const l = new LineSegments2(g, lineMat(w, col)); l.raycast = () => {}; mesh.add(l); return mesh;
}
// silhouette-only ink for round shapes (leaves, rocks, caps): a slightly larger back-face shell
const hullMat = new THREE.MeshBasicMaterial({ color: INK, side: THREE.BackSide });
export function hull(mesh, k = 1.06) { const h = new THREE.Mesh(mesh.geometry, hullMat); h.scale.setScalar(k); h.raycast = () => {}; mesh.add(h); return mesh; }
// mesh helper: geometry + colour (+ ink) placed at [x,y,z]
export function M(geo, color, pos = [0, 0, 0], o = {}) {
  const m = new THREE.Mesh(geo, color instanceof THREE.Material ? color : mat(color, o.mat || {}));
  m.position.set(...pos); if (o.rot) m.rotation.set(...o.rot); if (o.scale) m.scale.set(...o.scale);
  m.castShadow = o.cast !== false; m.receiveShadow = o.receive !== false;
  if (o.hull) hull(m, o.hull === true ? 1.06 : o.hull);
  else if (o.ink !== false) ink(m, o.inkW || 3, INK, o.inkAngle || 30);
  return m;
}
// canvas texture helper
export function canvasTex(w, h, draw, repeat = [1, 1]) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); t.anisotropy = 4; return t;
}

// ---------- light moods (the "pencahayaan") ----------
export const MOODS = {
  day:    { sky: ['#3f8fe0', '#8cc4f0', '#e6f2f8'], fog: ['#d5e8f2', 30, 160], hemi: ['#e4f1ff', '#8a7a62', 1.7], sun: ['#fff2da', 2.6, [6, 12, 8]], tint: '#ffffff', exposure: 1.0 },
  morning:{ sky: ['#6aa8e8', '#f2d6b8', '#ffe9cc'], fog: ['#f2dcc4', 25, 140], hemi: ['#ffeedd', '#7a6a5a', 1.5], sun: ['#ffd9a8', 2.6, [-8, 6, 6]], tint: '#fff2e2', exposure: 1.0 },
  sunset: { sky: ['#5a4f98', '#ee8458', '#ffc27a'], fog: ['#f0a26e', 18, 110], hemi: ['#ffc9a0', '#4a3040', 1.15], sun: ['#ffae6a', 3.2, [-10, 3.5, -8]], tint: '#ffd6b2', exposure: 1.0 },
  storm:  { sky: ['#2a3040', '#4a5262', '#6a7180'], fog: ['#5a6170', 10, 70], hemi: ['#a0a8c0', '#2a2a30', 1.1], sun: ['#c8d0e0', 1.0, [4, 10, 6]], tint: '#b4bccc', exposure: 1.0 },
  night:  { sky: ['#070b22', '#18225a', '#2c3a78'], fog: ['#1a2452', 10, 80], hemi: ['#5a6cc0', '#0c0c1c', 1.0], sun: ['#a8bcff', 1.1, [-6, 10, 4]], tint: '#8e9fe0', exposure: 1.05, stars: true },
  glow:   { sky: ['#020a06', '#06180e', '#0c2a18'], fog: ['#0a2214', 6, 45], hemi: ['#3a7a55', '#040806', .8], sun: ['#7fd0a0', .6, [-4, 10, 4]], tint: '#9fdcae', exposure: 1.05, bloom: [.65, .4, .82] },
  indoor: { sky: ['#2a1c14', '#3a2a1e', '#4a3626'], fog: ['#3a2a20', 12, 60], hemi: ['#ffe2c0', '#3a2a20', 1.2], sun: ['#ffd8a0', 1.6, [3, 8, 6]], tint: '#ffe6c8', exposure: 1.0 },
};
function skyDome(cols) {
  const g = new THREE.SphereGeometry(450, 32, 16);
  const m = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { a: { value: new THREE.Color(cols[0]) }, b: { value: new THREE.Color(cols[1]) }, c: { value: new THREE.Color(cols[2]) } },
    vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }',
    fragmentShader: 'uniform vec3 a,b,c; varying vec3 vP; void main(){ float h = vP.y; vec3 col = h > .12 ? mix(b, a, smoothstep(.12,.7,h)) : mix(c, b, smoothstep(-.05,.12,h)); gl_FragColor = vec4(col,1.); \n#include <tonemapping_fragment>\n#include <colorspace_fragment>\n }' });
  const s = new THREE.Mesh(g, m); s.renderOrder = -1; return s;
}
// make a scene in a mood. Returns { scene, sun, hemi, mood }
export function makeScene(moodName = 'day', over = {}) {
  const mood = Object.assign({}, MOODS[moodName], over);
  const scene = new THREE.Scene();
  scene.add(skyDome(mood.sky));
  scene.fog = new THREE.Fog(mood.fog[0], mood.fog[1], mood.fog[2]);
  const hemi = new THREE.HemisphereLight(mood.hemi[0], mood.hemi[1], mood.hemi[2]); scene.add(hemi);
  const sun = new THREE.DirectionalLight(mood.sun[0], mood.sun[1]); sun.position.set(...mood.sun[2]).multiplyScalar(3);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); const sc = sun.shadow.camera; sc.left = sc.bottom = -28; sc.right = sc.top = 28; sc.near = 1; sc.far = 160;
  sun.shadow.bias = -.0004; sun.shadow.normalBias = .03; sun.shadow.radius = 4; scene.add(sun); scene.add(sun.target);
  if (mood.stars) {
    const R = rng(5), p = []; for (let i = 0; i < 700; i++) { const a = R() * TAU, h = .08 + R() * .9; p.push(Math.cos(a) * 420 * Math.cos(h), 420 * Math.sin(h), Math.sin(a) * 420 * Math.cos(h)); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: '#ffffff', size: 2.2, sizeAttenuation: false, fog: false })));
  }
  scene.userData = { mood, chars: [], tick: [] };
  return { scene, sun, hemi, mood };
}
// aim the sun's shadow box at a point of interest
export function focusSun(sun, x, z, size = 28) { const d = sun.position.clone().sub(sun.target.position); sun.target.position.set(x, 0, z); sun.position.copy(sun.target.position).add(d); const sc = sun.shadow.camera; sc.left = sc.bottom = -size; sc.right = sc.top = size; sc.updateProjectionMatrix(); }

// ---------- camera ----------
export function camera(fov = 38) { return new THREE.PerspectiveCamera(fov, W / H, .05, 900); }
// smooth dolly between keyframes: keys [[t, [x,y,z], [lookX,lookY,lookZ], fov?], ...]
// drift: gentle handheld float in world units (0 = locked off)
export function camMove(cam, lt, keys, drift = .025, seed = 1) {
  const p = kf(lt, keys.map(k => [k[0], k[1]])), l = kf(lt, keys.map(k => [k[0], k[2]]));
  const tt = lt + seed * 10;
  cam.position.set(p[0] + wob(tt, seed) * drift, p[1] + wob(tt * 1.1, seed + 3) * drift * .7, p[2]);
  cam.lookAt(l[0] + wob(tt * .9, seed + 5) * drift * .6, l[1] + wob(tt * .8, seed + 7) * drift * .4, l[2]);
  if (keys[0][3]) { cam.fov = kf(lt, keys.map(k => [k[0], k[3] || keys[0][3]])); cam.updateProjectionMatrix(); }
}

// ---------- shots ----------
export const SHOTS = [];
// shot(start, end, build, {tr:'cut'|'fade'})   build() -> { scene, cam, update(lt, t) }
export function shot(start, end, build, opt = {}) { SHOTS.push({ start, end, build, opt }); }
const built = new Map();
function getShot(i) { if (!built.has(i)) built.set(i, SHOTS[i].build()); return built.get(i); }
function renderShot(i, t) {
  const S = SHOTS[i], B = getShot(i), lt = t - S.start;
  B.update && B.update(lt, t);
  const ud = B.scene.userData; (ud.tick || []).forEach(f => f(lt, t));
  (ud.chars || []).forEach(c => c.face(B.cam));
  const mood = ud.mood || {};
  renderer.toneMappingExposure = mood.exposure || 1;
  const bl = B.bloom || mood.bloom;
  if (bl) { renderPass.scene = B.scene; renderPass.camera = B.cam; bloomPass.strength = bl[0]; bloomPass.radius = bl[1]; bloomPass.threshold = bl[2]; composer.render(); }
  else { renderer.setRenderTarget(null); renderer.render(B.scene, B.cam); }
}

// ---------- output: composite, captions, grade ----------
const out = document.getElementById('c'); out.width = W; out.height = H; const octx = out.getContext('2d');
const tmp = document.createElement('canvas'); tmp.width = W; tmp.height = H; const tctx = tmp.getContext('2d');
const grains = []; for (let k = 0; k < 4; k++) { const g = document.createElement('canvas'); g.width = g.height = 256; const gc = g.getContext('2d'); const id = gc.createImageData(256, 256); const R = rng(k + 11); for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (R() - .5) * 110; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } gc.putImageData(id, 0, 0); grains.push(g); }
const NAMES = (window.NAMES || []).map(normW);
const CHUNKS = (() => {
  const ch = []; let cur = null;
  WORDS.forEach((w, i) => {
    const prev = WORDS[i - 1];
    const brk = !cur || cur.words.length >= 2 || (cur.text + ' ' + w.w).length > 15 || /[.,?!;:]$/.test(prev ? prev.w : '') || (prev && prev.line !== w.line);
    if (brk) { cur = { words: [w], text: w.w, s: w.s, e: w.e }; ch.push(cur); } else { cur.words.push(w); cur.text += ' ' + w.w; cur.e = w.e; }
  });
  ch.forEach((c, i) => { const n = ch[i + 1]; c.e = n && n.s - c.e < .6 ? n.s : c.e + .3; });
  return ch;
})();
// sentence case kept, punctuation dropped except ! and ?; names in yellow
const capWord = s => s.replace(/[-–—]/g, ' ').replace(/[^\p{L}\p{N}%!? ]/gu, '').trim();
function drawCaption(ctx, t) {
  const c = CHUNKS.find(c => t >= c.s && t < c.e); if (!c) return;
  const k = clamp((t - c.s) / .12), sc = .9 + .1 * backOut(k);
  const parts = c.words.map(w => [capWord(w.w), NAMES.includes(normW(w.w))]).filter(p => p[0]);
  ctx.save(); ctx.translate(540, 1350); ctx.scale(sc, sc); ctx.globalAlpha = clamp(k * 2);
  ctx.font = '700 64px Poppins'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const sp = ctx.measureText(' ').width, widths = parts.map(p => ctx.measureText(p[0]).width);
  let x = -(widths.reduce((a, b) => a + b, 0) + sp * (parts.length - 1)) / 2;
  parts.forEach(([s, name], i) => {
    ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 4;
    ctx.lineWidth = 9; ctx.strokeStyle = 'rgba(20,12,24,.92)'; ctx.textAlign = 'left'; ctx.strokeText(s, x, 0);
    ctx.shadowColor = 'transparent'; ctx.fillStyle = name ? '#ffd23a' : '#ffffff'; ctx.fillText(s, x, 0);
    x += widths[i] + sp;
  });
  ctx.restore();
}
const FADE = .4;
function renderFrame(f) {
  const t = Math.min(f / FPS, DUR - 1e-3);
  let i = SHOTS.findIndex(s => t >= s.start && t < s.end); if (i < 0) i = t < SHOTS[0].start ? 0 : SHOTS.length - 1;
  renderShot(i, t);
  octx.setTransform(1, 0, 0, 1, 0, 0); octx.globalAlpha = 1; octx.drawImage(glc, 0, 0);
  const prev = SHOTS[i - 1];
  if (prev && prev.opt.tr === 'fade' && t < SHOTS[i].start + FADE) {
    tctx.drawImage(glc, 0, 0); renderShot(i - 1, Math.min(t, prev.end - 1e-3));
    octx.drawImage(glc, 0, 0); octx.globalAlpha = smooth((t - SHOTS[i].start) / FADE); octx.drawImage(tmp, 0, 0); octx.globalAlpha = 1;
  }
  if (SHOTS[i].opt.fadeIn && t < SHOTS[i].start + .6) { octx.fillStyle = '#000'; octx.globalAlpha = 1 - smooth((t - SHOTS[i].start) / .6); octx.fillRect(0, 0, W, H); octx.globalAlpha = 1; }
  if (t > DUR - .6) { octx.fillStyle = '#000'; octx.globalAlpha = smooth((t - (DUR - .6)) / .6); octx.fillRect(0, 0, W, H); octx.globalAlpha = 1; }
  // grade: soft vignette + fine grain
  const g = octx.createRadialGradient(540, 900, 520, 540, 960, 1280); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(8,4,16,.34)'); octx.fillStyle = g; octx.fillRect(0, 0, W, H);
  octx.save(); octx.globalCompositeOperation = 'overlay'; octx.globalAlpha = .05; octx.fillStyle = octx.createPattern(grains[f % 4], 'repeat'); octx.translate((f * 37) % 256, (f * 91) % 256); octx.fillRect(-256, -256, W + 512, H + 512); octx.restore();
  drawCaption(octx, t);
}
export async function start() {
  await document.fonts.load('700 64px Poppins');
  window.SHOT_SPANS = SHOTS.map((s, i) => [s.start, i === SHOTS.length - 1 ? DUR : s.end]);
  window.TOTAL_FRAMES = Math.round(DUR * FPS);
  window.renderFrame = renderFrame;
  window.grab = (q = .93) => out.toDataURL('image/jpeg', q);
  window.READY = true;
}
