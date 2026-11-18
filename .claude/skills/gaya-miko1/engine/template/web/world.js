// ---------- /gaya-miko1 world kit: low-poly Indonesian places with ink edges ----------
import { THREE, M, mat, glowMat, ink, hull, canvasTex, rng, TAU, INK, clamp, lerp } from './core.js';
const G = THREE;

// ---------- ground textures ----------
const TEX = {};
function groundTex(kind) {
  if (TEX[kind]) return TEX[kind];
  const R = rng(7);
  const draw = {
    tile: (c, w, h) => { c.fillStyle = '#9a9a92'; c.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 64) for (let x = 0; x < w; x += 64) { c.fillStyle = `rgb(${150 + R() * 18},${150 + R() * 16},${142 + R() * 14})`; c.fillRect(x + 3, y + 3, 58, 58); } },
    grass: (c, w, h) => { c.fillStyle = '#5f9a42'; c.fillRect(0, 0, w, h); for (let i = 0; i < 2600; i++) { c.fillStyle = R() > .5 ? 'rgba(120,180,80,.5)' : 'rgba(40,90,40,.4)'; c.fillRect(R() * w, R() * h, 3, 9); } },
    dirt: (c, w, h) => { c.fillStyle = '#8a6a48'; c.fillRect(0, 0, w, h); for (let i = 0; i < 1800; i++) { c.fillStyle = R() > .5 ? 'rgba(160,125,90,.5)' : 'rgba(80,55,35,.4)'; c.beginPath(); c.arc(R() * w, R() * h, 1 + R() * 3, 0, TAU); c.fill(); } },
    plank: (c, w, h) => { for (let y = 0; y < h; y += 42) { c.fillStyle = `rgb(${170 + R() * 20},${120 + R() * 14},${70 + R() * 10})`; c.fillRect(0, y, w, 40); c.fillStyle = 'rgba(60,30,10,.5)'; c.fillRect(0, y + 40, w, 2); } },
    sand: (c, w, h) => { c.fillStyle = '#d8b878'; c.fillRect(0, 0, w, h); for (let i = 0; i < 2000; i++) { c.fillStyle = 'rgba(150,110,60,.25)'; c.fillRect(R() * w, R() * h, 2, 2); } },
  }[kind];
  TEX[kind] = canvasTex(512, 512, draw); return TEX[kind];
}
export function ground(scene, o = {}) {
  const size = o.size || 220, kind = o.kind || 'grass';
  const t = groundTex(kind).clone(); t.needsUpdate = true; t.repeat.set(size / (o.tile || 4), size / (o.tile || 4));
  const m = new G.Mesh(new G.PlaneGeometry(size, size), mat(o.color || '#ffffff', { map: t }));
  m.rotation.x = -Math.PI / 2; m.position.set(o.x || 0, o.y || 0, o.z || 0); m.receiveShadow = true; scene.add(m); return m;
}

// ---------- kontrakan / village houses ----------
const WALLS = ['#e8d9a8', '#d9e2c4', '#f0c8a8', '#c8d8e0', '#e8b8b0', '#d8c8e8', '#f2e2c2'];
// a row of attached houses along z, on one side of an alley (side -1 = left, faces +x; side 1 = right, faces -x)
export function houseRow(scene, o = {}) {
  const side = o.side || -1, x = o.x != null ? o.x : side * 2.6, z0 = o.z0 ?? 6, n = o.n || 8, w = o.w || 3.4, d = 4, h = o.h || 3.1;
  const R = rng(o.seed || (side > 0 ? 3 : 9)); const g = new G.Group();
  for (let i = 0; i < n; i++) {
    const z = z0 - i * w, col = (o.walls || WALLS)[Math.floor(R() * (o.walls || WALLS).length)];
    const cx = x + side * d / 2;
    g.add(M(new G.BoxGeometry(d, h, w - .04), col, [cx, h / 2, z]));
    // roof slab sticking out over the alley
    g.add(M(new G.BoxGeometry(d + .9, .18, w), '#b4553a', [cx - side * .45, h + .09, z], { rot: [0, 0, side * .08] }));
    const fx = x - side * .01; // facade plane x
    // door with frame
    g.add(M(new G.BoxGeometry(.12, 2.15, 1.05), '#3c2a24', [fx, 1.07, z - w * .22]));
    g.add(M(new G.BoxGeometry(.06, 2.0, .9), R() > .4 ? '#2f5f4a' : '#7a4a2a', [fx - side * .07, 1.0, z - w * .22], { ink: false }));
    // window with bars
    g.add(M(new G.BoxGeometry(.1, .95, 1.1), '#3a4a5a', [fx, 1.75, z + w * .2]));
    for (let k = -1; k <= 1; k++) g.add(M(new G.BoxGeometry(.06, .95, .05), '#5a3a2a', [fx - side * .06, 1.75, z + w * .2 + k * .32], { ink: false }));
    // step / bench
    if (R() > .5) g.add(M(new G.BoxGeometry(.5, .35, .9), '#8a8a82', [fx - side * .3, .17, z + w * .2]));
    if (R() > .55) g.add(M(new G.CylinderGeometry(.22, .18, .45, 10), ['#3a7fc0', '#d84a3a', '#e8b030'][Math.floor(R() * 3)], [fx - side * .35, .22, z - w * .45]));
  }
  scene.add(g); return g;
}
// clothesline between two points with hanging laundry that sways
export function clothesline(scene, a, b, o = {}) {
  const y = o.y || 2.6, n = o.n || 6, R = rng(o.seed || 4), g = new G.Group();
  const p0 = new G.Vector3(a[0], y, a[1]), p1 = new G.Vector3(b[0], y, b[1]);
  const curve = new G.QuadraticBezierCurve3(p0, p0.clone().lerp(p1, .5).add(new G.Vector3(0, -.25, 0)), p1);
  g.add(new G.Mesh(new G.TubeGeometry(curve, 24, .012, 4), mat('#d8d0c0')));
  const items = [];
  for (let i = 0; i < n; i++) {
    const k = (i + .5) / n, p = curve.getPoint(k), kind = Math.floor(R() * 3), col = o.cols ? o.cols[i % o.cols.length] : ['#e8e4dc', '#d84a3a', '#3a6ab8', '#e8b030', '#7a4bc4', '#3fa35b'][Math.floor(R() * 6)];
    const tex = canvasTex(128, 160, (c, w, h) => {
      c.fillStyle = col; c.strokeStyle = INK; c.lineWidth = 6;
      if (kind === 0) { c.beginPath(); c.moveTo(20, 6); c.lineTo(108, 6); c.lineTo(124, 40); c.lineTo(100, 48); c.lineTo(100, 152); c.lineTo(28, 152); c.lineTo(28, 48); c.lineTo(4, 40); c.closePath(); c.fill(); c.stroke(); }
      else if (kind === 1) { c.fillRect(8, 4, 112, 150); c.strokeRect(8, 4, 112, 150); c.fillStyle = 'rgba(255,220,120,.9)'; for (let y = 20; y < 150; y += 28) for (let x = 22; x < 120; x += 28) { c.beginPath(); c.arc(x, y, 7, 0, TAU); c.fill(); } }
      else { c.fillRect(14, 4, 100, 120); c.fillStyle = 'rgba(255,255,255,.6)'; for (let y = 10; y < 120; y += 24) c.fillRect(14, y, 100, 9); c.strokeRect(14, 4, 100, 120); }
    });
    const m = new G.Mesh(new G.PlaneGeometry(.55, .7), new G.MeshToonMaterial({ map: tex, alphaTest: .5, side: G.DoubleSide }));
    m.geometry.translate(0, -.35, 0); m.position.copy(p); m.lookAt(p.x + (p1.z - p0.z), p.y, p.z - (p1.x - p0.x)); m.castShadow = true;
    m.customDepthMaterial = new G.MeshDepthMaterial({ depthPacking: G.RGBADepthPacking, map: tex, alphaTest: .5 });
    g.add(m); items.push([m, R() * 6]);
  }
  scene.add(g);
  scene.userData.tick.push((lt, t) => items.forEach(([m, ph]) => { m.rotation.x = Math.sin(t * 1.6 + ph) * .08 * (o.wind || 1); }));
  return g;
}

// ---------- nature ----------
// bamboo clump. o: { x, z, r (spread), n, h, col, glow (0..1 spots of light for night scenes) }
export function bamboo(scene, o = {}) {
  const R = rng(o.seed || 11), g = new G.Group(), n = o.n || 14, H = o.h || 9, col = o.col || '#9fb446';
  const nodeM = mat(o.nodeCol || '#6f8a2a');
  for (let i = 0; i < n; i++) {
    const a = R() * TAU, d = Math.sqrt(R()) * (o.r || 1.2), x = (o.x || 0) + Math.cos(a) * d, z = (o.z || 0) + Math.sin(a) * d;
    const h = H * (.7 + R() * .5), r = .07 + R() * .05, lean = (R() - .5) * .12;
    const stem = M(new G.CylinderGeometry(r, r * 1.1, h, 8), col, [x, h / 2, z], { rot: [lean, 0, (R() - .5) * .12], inkW: 2 });
    for (let y = -h / 2 + .9; y < h / 2; y += .9 + R() * .4) stem.add(new G.Mesh(new G.CylinderGeometry(r * 1.18, r * 1.18, .05, 8), nodeM).translateY(y));
    if (o.glow) for (let k = 0; k < 3; k++) if (R() < o.glow) { const s = new G.Mesh(new G.SphereGeometry(r * 1.3, 8, 6), glowMat(o.glowCol || '#5dff7a', 2.4)); s.scale.set(1, 2.2, 1); s.position.y = -h / 2 + .3 + R() * 1.6; stem.add(s); }
    g.add(stem);
  }
  // leafy crowns
  const leaf = mat(o.leafCol || '#4f7a2e');
  for (let i = 0; i < (o.crowns || 6); i++) { const a = R() * TAU, d = R() * (o.r || 1.2) * 1.6; const m = new G.Mesh(new G.SphereGeometry(1.4 + R(), 10, 7), leaf); m.scale.set(1.4, .5, 1.4); m.position.set((o.x || 0) + Math.cos(a) * d, H * (.85 + R() * .3), (o.z || 0) + Math.sin(a) * d); m.castShadow = true; hull(m, 1.05); g.add(m); }
  scene.add(g); return g;
}
export function tree(scene, x, z, s = 1, o = {}) {
  const g = new G.Group(); g.add(M(new G.CylinderGeometry(.18 * s, .26 * s, 2.4 * s, 7), o.trunk || '#7a5236', [x, 1.2 * s, z]));
  const R = rng(o.seed || Math.floor(x * 13 + z * 7)), leaf = o.leaf || '#5d9440';
  for (let i = 0; i < 4; i++) g.add(M(new G.SphereGeometry((1 + R() * .5) * s, 12, 8), leaf, [x + (R() - .5) * 1.4 * s, (2.6 + R() * 1.2) * s, z + (R() - .5) * 1.4 * s], { hull: 1.05 }));
  scene.add(g); return g;
}
export function mountain(scene, x, z, r, h, col = '#5a7a6a', o = {}) {
  const m = new G.Mesh(new G.ConeGeometry(r, h, o.seg || 7, 1), mat(col)); m.position.set(x, h / 2 - .5, z); m.rotation.y = o.rot || .4; m.receiveShadow = true; ink(m, 2.5, INK, 20); scene.add(m);
  if (o.cap) { const c = new G.Mesh(new G.ConeGeometry(r * .28, h * .28, o.seg || 7, 1), mat(o.cap)); c.position.set(x, h - .5 - h * .14 + .02, z); c.rotation.y = o.rot || .4; scene.add(c); }
  return m;
}
export function hills(scene, o = {}) { const R = rng(o.seed || 3); for (let i = 0; i < (o.n || 6); i++) { const m = new G.Mesh(new G.SphereGeometry(8 + R() * 10, 16, 10), mat(o.col || '#6fa64e')); m.scale.y = .35; m.position.set((R() - .5) * 120, -1, -(o.z || 40) - R() * 50); hull(m, 1.01); scene.add(m); } }
export function bush(scene, x, z, s = 1, col = '#4f8a3a') { const g = new G.Group(); for (let i = 0; i < 3; i++) g.add(M(new G.SphereGeometry(.55 * s, 10, 7), col, [x + (i - 1) * .5 * s, .4 * s, z + (i % 2) * .2], { hull: 1.07 })); scene.add(g); return g; }
export function rice(scene, o = {}) { // sawah: paddy rows
  const size = o.size || 200, t = canvasTex(256, 256, (c, w, h) => { c.fillStyle = o.col || '#7fb84a'; c.fillRect(0, 0, w, h); c.strokeStyle = 'rgba(40,90,30,.55)'; c.lineWidth = 5; for (let y = 0; y < h; y += 16) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); } }, [size / 3, size / 3]);
  const m = new G.Mesh(new G.PlaneGeometry(size, size), mat('#ffffff', { map: t })); m.rotation.x = -Math.PI / 2; m.position.set(o.x || 0, .01, o.z || 0); m.receiveShadow = true; scene.add(m); return m;
}
// glowing mushrooms (for "glow" scenes). Adds a soft point light.
export function glowShrooms(scene, x, z, o = {}) {
  const R = rng(o.seed || 21), col = o.col || '#6bff78', g = new G.Group();
  for (let i = 0; i < (o.n || 7); i++) {
    const s = (.15 + R() * .35) * (o.s || 1), px = x + (R() - .5) * 1.2, pz = z + (R() - .5) * 1.2;
    g.add(M(new G.CylinderGeometry(s * .25, s * .3, s * 1.2, 7), '#d8f0d0', [px, s * .6, pz], { hull: 1.12 }));
    const cap = new G.Mesh(new G.SphereGeometry(s, 12, 8, 0, TAU, 0, Math.PI / 2), glowMat(col, 1.8)); cap.position.set(px, s * 1.15, pz); g.add(cap);
  }
  const L = new G.PointLight(col, o.light ?? 6, 6, 1.6); L.position.set(x, .8, z); g.add(L);
  scene.add(g); return g;
}
// floating light specks (fireflies / spores)
export function specks(scene, o = {}) {
  const R = rng(o.seed || 5), n = o.n || 60, p = [], base = [];
  for (let i = 0; i < n; i++) { const v = [(o.x || 0) + (R() - .5) * (o.w || 10), .3 + R() * (o.h || 3), (o.z || 0) + (R() - .5) * (o.d || 10)]; base.push(v); p.push(...v); }
  const geo = new G.BufferGeometry(); geo.setAttribute('position', new G.Float32BufferAttribute(p, 3));
  const pts = new G.Points(geo, new G.PointsMaterial({ color: new G.Color(o.col || '#8dff9a').multiplyScalar(2), size: o.size || 7, sizeAttenuation: false, toneMapped: false, transparent: true, opacity: .9 }));
  scene.add(pts);
  scene.userData.tick.push((lt, t) => { const a = geo.attributes.position.array; base.forEach((v, i) => { a[i * 3] = v[0] + Math.sin(t * .7 + i) * .2; a[i * 3 + 1] = v[1] + Math.sin(t * .9 + i * 2) * .15; a[i * 3 + 2] = v[2] + Math.cos(t * .6 + i) * .2; }); geo.attributes.position.needsUpdate = true; });
  return pts;
}
export function rain(scene, o = {}) {
  const R = rng(9), n = o.n || 1500, w = o.w || 30, p = [];
  for (let i = 0; i < n; i++) { const x = (o.x || 0) + (R() - .5) * w, y = R() * 14, z = (o.z || 0) + (R() - .5) * w; p.push(x, y, z, x + .05, y - .45, z); }
  const geo = new G.BufferGeometry(); geo.setAttribute('position', new G.Float32BufferAttribute(p, 3)); const base = Float32Array.from(p);
  const lines = new G.LineSegments(geo, new G.LineBasicMaterial({ color: '#c8d8f0', transparent: true, opacity: .55 })); scene.add(lines);
  scene.userData.tick.push((lt, t) => { const a = geo.attributes.position.array; for (let i = 0; i < a.length; i += 6) { const y = ((base[i + 1] - t * 16) % 14 + 14) % 14; a[i + 1] = y; a[i + 4] = y - .45; } geo.attributes.position.needsUpdate = true; });
  return lines;
}
export function moon(scene, dir = [-.4, .45, -1], col = '#fff3c4') {
  const v = new G.Vector3(...dir).normalize().multiplyScalar(380);
  const m = new G.Mesh(new G.CircleGeometry(16, 32), new G.MeshBasicMaterial({ color: new G.Color(col).multiplyScalar(1.6), fog: false, toneMapped: false })); m.position.copy(v); m.lookAt(0, 0, 0); scene.add(m); return m;
}
export function sunDisc(scene, dir = [-.5, .12, -1], col = '#ffe2a0', size = 26) {
  const v = new G.Vector3(...dir).normalize().multiplyScalar(380);
  const m = new G.Mesh(new G.CircleGeometry(size, 32), new G.MeshBasicMaterial({ color: new G.Color(col).multiplyScalar(1.4), fog: false, toneMapped: false })); m.position.copy(v); m.lookAt(0, 0, 0); scene.add(m); return m;
}
export function clouds(scene, o = {}) {
  const R = rng(o.seed || 2), g = new G.Group(), m = mat(o.col || '#ffffff');
  for (let i = 0; i < (o.n || 8); i++) { const c = new G.Group(); for (let k = 0; k < 4; k++) { const s = new G.Mesh(new G.IcosahedronGeometry(2 + R() * 2, 1), m); s.position.set(k * 2.4 - 3.6, R() * 1.2, R()); c.add(s); } c.scale.set(1.6, .7, 1); c.position.set((R() - .5) * 160, 30 + R() * 20, -60 - R() * 80); g.add(c); }
  scene.add(g); scene.userData.tick.push((lt, t) => { g.position.x = t * .6; }); return g;
}

// ---------- props ----------
export function lamp(scene, x, y, z, o = {}) { // hanging bulb with warm light
  const g = new G.Group(); g.add(M(new G.CylinderGeometry(.01, .01, o.cord || .6, 4), INK, [x, y + (o.cord || .6) / 2, z], { ink: false }));
  const b = new G.Mesh(new G.SphereGeometry(.09, 12, 8), glowMat(o.col || '#ffd890', 2.5)); b.position.set(x, y, z); g.add(b);
  const L = new G.PointLight(o.col || '#ffcf80', o.power ?? 8, o.dist || 9, 1.6); L.position.set(x, y - .1, z); L.castShadow = !!o.shadow; g.add(L);
  scene.add(g); return g;
}
export function table(scene, x, z, o = {}) { const g = new G.Group(), w = o.w || 1.2, d = o.d || .7, h = o.h || .75, c = o.col || '#7a4a2a'; g.add(M(new G.BoxGeometry(w, .07, d), c, [x, h, z])); for (const [i, k] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(M(new G.BoxGeometry(.06, h, .06), c, [x + i * (w / 2 - .06), h / 2, z + k * (d / 2 - .06)])); scene.add(g); return g; }
export function basket(scene, x, z, o = {}) { const m = M(new G.CylinderGeometry(.32, .26, .3, 12), o.col || '#c89a4a', [x, (o.y || 0) + .15, z]); scene.add(m); return m; }
export function bucket(scene, x, z, col = '#3a7fc0') { const m = M(new G.CylinderGeometry(.2, .16, .32, 12), col, [x, .16, z]); scene.add(m); return m; }
export function stool(scene, x, z, col = '#8a5a3a') { const g = new G.Group(); g.add(M(new G.BoxGeometry(.5, .06, .5), col, [x, .45, z])); for (const [i, k] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(M(new G.BoxGeometry(.05, .45, .05), col, [x + i * .2, .22, z + k * .2])); scene.add(g); return g; }
export function logs(scene, x, z, o = {}) { const g = new G.Group(), R = rng(o.seed || 3); for (let i = 0; i < (o.n || 8); i++) { const m = M(new G.CylinderGeometry(.09, .09, 2, 8), o.col || '#b89048', [x + (R() - .5) * 1.2, .1 + Math.floor(i / 4) * .17, z + (i % 4) * .19], { rot: [0, 0, Math.PI / 2], inkW: 2 }); g.add(m); } scene.add(g); return g; }
export function box(scene, w, h, d, col, pos, o) { const m = M(new G.BoxGeometry(w, h, d), col, pos, o); scene.add(m); return m; }
export function wallRoom(scene, o = {}) { // simple interior: floor + 3 walls
  const w = o.w || 6, d = o.d || 6, h = o.h || 3; const g = new G.Group();
  g.add(M(new G.BoxGeometry(w, .1, d), o.floor || '#a8784a', [0, -.05, 0], { ink: false }));
  g.add(M(new G.BoxGeometry(w, h, .1), o.wall || '#e8d9a8', [0, h / 2, -d / 2]));
  g.add(M(new G.BoxGeometry(.1, h, d), o.wall2 || o.wall || '#e0d0a0', [-w / 2, h / 2, 0]));
  g.add(M(new G.BoxGeometry(.1, h, d), o.wall2 || o.wall || '#e0d0a0', [w / 2, h / 2, 0]));
  scene.add(g); return g;
}

// ---------- more kampung pieces ----------
// asphalt / concrete road along z with a dashed centre line
export function road(scene, o = {}) {
  const w = o.w || 5, len = o.len || 120, x = o.x || 0;
  const t = canvasTex(128, 512, (c, W, H) => { c.fillStyle = o.col || '#5a5a5e'; c.fillRect(0, 0, W, H); const R = rng(4); for (let i = 0; i < 900; i++) { c.fillStyle = R() > .5 ? 'rgba(255,255,255,.06)' : 'rgba(0,0,0,.1)'; c.fillRect(R() * W, R() * H, 2, 2); } if (o.line !== false) { c.fillStyle = '#e8e0c8'; for (let y = 0; y < H; y += 128) c.fillRect(W / 2 - 4, y, 8, 64); } }, [1, len / 8]);
  const m = new G.Mesh(new G.PlaneGeometry(w, len), mat('#ffffff', { map: t })); m.rotation.x = -Math.PI / 2; m.position.set(x, .015, o.z || 0); m.receiveShadow = true; scene.add(m); return m;
}
// electricity poles along a line with sagging wires between them
export function poles(scene, pts, o = {}) {
  const h = o.h || 7, g = new G.Group();
  pts.forEach(([x, z]) => { g.add(M(new G.CylinderGeometry(.09, .12, h, 8), o.col || '#8a8a86', [x, h / 2, z])); g.add(M(new G.BoxGeometry(1.2, .08, .08), '#5a5a58', [x, h - .5, z])); });
  for (let i = 0; i < pts.length - 1; i++) for (const k of [-.5, .5]) {
    const a = new G.Vector3(pts[i][0] + k, h - .45, pts[i][1]), b = new G.Vector3(pts[i + 1][0] + k, h - .45, pts[i + 1][1]);
    const c = new G.QuadraticBezierCurve3(a, a.clone().lerp(b, .5).add(new G.Vector3(0, -.6, 0)), b);
    g.add(new G.Mesh(new G.TubeGeometry(c, 20, .015, 4), mat('#1e1a1e')));
  }
  scene.add(g); return g;
}
export function potPlant(scene, x, z, o = {}) { const g = new G.Group(), s = o.s || 1; g.add(M(new G.CylinderGeometry(.22 * s, .16 * s, .34 * s, 10), o.pot || '#c0643a', [x, .17 * s, z])); g.add(M(new G.SphereGeometry(.32 * s, 10, 7), o.leaf || '#4f9a3a', [x, .5 * s, z], { hull: 1.07 })); scene.add(g); return g; }
// bamboo fence from (x0,z0) to (x1,z1)
export function fence(scene, x0, z0, x1, z1, o = {}) {
  const g = new G.Group(), n = Math.max(2, Math.round(Math.hypot(x1 - x0, z1 - z0) / .14)), h = o.h || 1.1, col = o.col || '#c8a85a';
  for (let i = 0; i <= n; i++) { const k = i / n; g.add(M(new G.CylinderGeometry(.05, .05, h * (i % 2 ? .95 : 1), 6), col, [lerp(x0, x1, k), h / 2, lerp(z0, z1, k)], { inkW: 1.5 })); }
  const len = Math.hypot(x1 - x0, z1 - z0), ang = Math.atan2(x1 - x0, z1 - z0);
  for (const y of [h * .35, h * .75]) g.add(M(new G.CylinderGeometry(.035, .035, len, 6), '#a8883a', [(x0 + x1) / 2, y, (z0 + z1) / 2], { rot: [Math.PI / 2, 0, 0], inkW: 1.5 }).rotateOnWorldAxis(new G.Vector3(0, 1, 0), ang));
  scene.add(g); return g;
}
// a small warung: counter, awning, shelves of goods and a sign
export function warung(scene, x, z, o = {}) {
  const g = new G.Group(), rot = o.rot || 0, wall = o.wall || '#7fbfa8';
  g.add(M(new G.BoxGeometry(3.2, 2.8, 2.4), wall, [0, 1.4, -1.2]));
  g.add(M(new G.BoxGeometry(2.6, 1.9, .1), '#3a2a24', [0, 1.55, -.02], { ink: false }));
  const R = rng(5); for (let s = 0; s < 3; s++) { g.add(M(new G.BoxGeometry(2.4, .05, .3), '#8a5a3a', [0, .9 + s * .5, -.2], { ink: false })); for (let i = 0; i < 9; i++) g.add(M(new G.BoxGeometry(.18, .26, .16), ['#e8564a', '#f2c230', '#3a7fc0', '#3fa35b', '#f0f0e8'][Math.floor(R() * 5)], [-1.05 + i * .26, 1.06 + s * .5, -.2], { inkW: 1.5 })); }
  g.add(M(new G.BoxGeometry(3.0, .95, .6), o.counter || '#c89a5a', [0, .48, .45]));
  g.add(M(new G.BoxGeometry(3.6, .1, 1.4), o.awning || '#d8463a', [0, 2.75, .55], { rot: [-.18, 0, 0] }));
  const sign = canvasTex(512, 128, (c, W, H) => { c.fillStyle = o.signCol || '#f6efd8'; c.fillRect(0, 0, W, H); c.strokeStyle = INK; c.lineWidth = 10; c.strokeRect(5, 5, W - 10, H - 10); c.fillStyle = o.textCol || '#c8302c'; c.font = '700 64px Poppins'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(o.text || 'WARUNG', W / 2, H / 2 + 4); });
  const sm = new G.Mesh(new G.PlaneGeometry(2.2, .55), new G.MeshToonMaterial({ map: sign })); sm.position.set(0, 3.25, .02); g.add(sm);
  g.position.set(x, 0, z); g.rotation.y = rot; g.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  scene.add(g); return g;
}
// a scooter (motor bebek)
export function motor(scene, x, z, o = {}) {
  const g = new G.Group(), col = o.col || '#d8302c';
  for (const zz of [-.6, .6]) g.add(M(new G.TorusGeometry(.26, .08, 8, 16), '#222', [0, .3, zz], { rot: [0, Math.PI / 2, 0], inkW: 2 }));
  g.add(M(new G.BoxGeometry(.32, .38, 1.1), col, [0, .62, .05]));
  g.add(M(new G.BoxGeometry(.3, .12, .55), '#222', [0, .86, -.15]));
  g.add(M(new G.BoxGeometry(.12, .7, .12), '#444', [0, .85, .62], { rot: [-.3, 0, 0] }));
  g.add(M(new G.BoxGeometry(.7, .06, .06), '#333', [0, 1.2, .72]));
  g.position.set(x, 0, z); g.rotation.y = o.rot || 0; scene.add(g); return g;
}
export function coconut(scene, x, z, o = {}) {
  const g = new G.Group(), h = o.h || 6, lean = o.lean || .15;
  const c = new G.QuadraticBezierCurve3(new G.Vector3(0, 0, 0), new G.Vector3(lean * h * .2, h * .5, 0), new G.Vector3(lean * h, h, 0));
  g.add(new G.Mesh(new G.TubeGeometry(c, 16, .16, 7), mat('#9a7a52')));
  const top = c.getPoint(1); for (let i = 0; i < 7; i++) { const lf = M(new G.BoxGeometry(2.4, .04, .45), '#4f9a3a', [top.x + Math.cos(i / 7 * TAU) * 1.1, top.y - .25, Math.sin(i / 7 * TAU) * 1.1], { inkW: 2 }); lf.rotation.set(0, -i / 7 * TAU, -.35); g.add(lf); }
  g.position.set(x, 0, z); g.traverse(m => { if (m.isMesh) m.castShadow = true; }); scene.add(g); return g;
}
export function sea(scene, o = {}) {
  const m = new G.Mesh(new G.PlaneGeometry(400, 200, 40, 20), mat(o.col || '#2f9ad0', { transparent: true, opacity: .95 }));
  m.rotation.x = -Math.PI / 2; m.position.set(0, o.y || .05, (o.z || -20) - 100); m.receiveShadow = true; scene.add(m);
  const p = m.geometry.attributes.position, base = Float32Array.from(p.array);
  scene.userData.tick.push((lt, t) => { for (let i = 0; i < p.count; i++) p.array[i * 3 + 2] = Math.sin(base[i * 3] * .3 + t * 1.2) * .08 + Math.cos(base[i * 3 + 1] * .4 + t) * .06; p.needsUpdate = true; });
  return m;
}
