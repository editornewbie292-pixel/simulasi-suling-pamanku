// ---------- /gaya-miko1 characters: flat cartoon people living in the 3D world ----------
// Drawn in 2D (wide pillow head, thick ink, cel shading, hair with a white sheen), placed in 3D as a
// camera-facing card that casts a real shadow and takes the scene's light colour.
import { THREE, INK, TAU, clamp, lerp, rng } from './core.js';

export const SKIN = { sawo: '#b67a50', terang: '#d39a6c', gelap: '#8e5a3a', kuning: '#e0aa78' };
const DW = 1000, DH = 1500, RES = 1.3;            // design units, texture scale
const FEET = 1470, TOP = 140;                       // design y of the soles / top of a plain head

// ---------- outfits / looks (mix freely) ----------
// spec = { skin, hair: 'bun'|'bob'|'short'|'spiky'|'peci'|'hijab'|'long'|'bald', hairCol, hijabCol,
//          old, eyes: 'dot'|'iris', irisCol, browCol, shirt, shirtStyle: 'plain'|'office'|'kebaya'|'koko'|'kaos'|'apron',
//          sleeve: 'long'|'short', sarong: colour|null, motif: 'ring'|'stripe'|'kawung'|null, motifCol, pants, sandal }
export const LOOKS = {
  nenek:    { skin: SKIN.sawo, hair: 'bun', hairCol: '#e9e5dd', old: true, eyes: 'iris', browCol: '#c9c1b5', shirt: '#8fbf9f', shirtStyle: 'kebaya', sleeve: 'long', sarong: '#6b3b2e', motif: 'ring', motifCol: '#e8b040' },
  ibu:      { skin: SKIN.sawo, hair: 'hijab', hijabCol: '#2f8f98', shirt: '#c8573f', shirtStyle: 'plain', sleeve: 'long', sarong: '#3d3a6a', motif: 'ring', motifCol: '#d8d0ff' },
  gadis:    { skin: SKIN.sawo, hair: 'bob', hairCol: '#1f1820', shirt: '#9a82d8', shirtStyle: 'kaos', sleeve: 'long', pants: '#3b4f86' },
  pegawai:  { skin: SKIN.sawo, hair: 'bob', hairCol: '#1f1820', shirt: '#2a3a72', shirtStyle: 'office', sleeve: 'long', pants: '#232a44' },
  bapak:    { skin: SKIN.gelap, hair: 'peci', hairCol: '#1f1820', shirt: '#e8e4dc', shirtStyle: 'koko', sleeve: 'long', sarong: '#6b8f6a', motif: 'stripe', motifCol: '#3d5a3c' },
  pemuda:   { skin: SKIN.sawo, hair: 'short', hairCol: '#1f1820', shirt: '#f0b532', shirtStyle: 'kaos', sleeve: 'short', pants: '#3a5aa0' },
  anak:     { skin: SKIN.sawo, hair: 'spiky', hairCol: '#1f1820', shirt: '#e8564a', shirtStyle: 'kaos', sleeve: 'short', pants: '#2f4f8f', kid: true },
};

// ---------- 2D drawing ----------
function headPath(ctx, cx, cy, a, b, n = 2.6) {
  ctx.beginPath();
  for (let i = 0; i <= 72; i++) { const th = i / 72 * TAU, c = Math.cos(th), s = Math.sin(th);
    const x = cx + a * Math.sign(c) * Math.pow(Math.abs(c), 2 / n), y = cy + b * Math.sign(s) * Math.pow(Math.abs(s), 2 / n);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
  ctx.closePath();
}
function stroke(ctx, w, col = INK) { ctx.lineWidth = w; ctx.strokeStyle = col; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke(); }
function fillS(ctx, fill, w = 20) { if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (w) stroke(ctx, w); }
// soft cel shade across a shape: lit on the left, shaded on the right (light comes from the key side)
function shade(ctx, pathFn, x0, x1, y0, y1, amt = .2, side = 1) {
  ctx.save(); pathFn(); ctx.clip();
  const g = ctx.createLinearGradient(side > 0 ? x0 : x1, 0, side > 0 ? x1 : x0, 0);
  g.addColorStop(0, 'rgba(255,240,225,.10)'); g.addColorStop(.5, 'rgba(255,240,225,0)'); g.addColorStop(.62, `rgba(70,25,30,${amt * .6})`); g.addColorStop(1, `rgba(60,20,30,${amt})`);
  ctx.fillStyle = g; ctx.fillRect(x0 - 20, y0 - 20, x1 - x0 + 40, y1 - y0 + 40); ctx.restore();
}
function tube(ctx, pts, w, col) {
  ctx.beginPath(); ctx.moveTo(...pts[0]); for (let i = 1; i < pts.length; i++) ctx.lineTo(...pts[i]);
  stroke(ctx, w + 22, INK); ctx.beginPath(); ctx.moveTo(...pts[0]); for (let i = 1; i < pts.length; i++) ctx.lineTo(...pts[i]); stroke(ctx, w, col);
}
function limb(ox, oy, side, a1, a2, l1, l2) {
  const ex = ox + side * Math.sin(a1) * l1, ey = oy + Math.cos(a1) * l1, b = a1 + a2;
  return [[ox, oy], [ex, ey], [ex + side * Math.sin(b) * l2, ey + Math.cos(b) * l2]];
}
function shadeHex(hex, k) { const n = parseInt(hex.slice(1), 16); const f = c => Math.round(clamp(c * k, 0, 255)); return `rgb(${f(n >> 16 & 255)},${f(n >> 8 & 255)},${f(n & 255)})`; }
function motifFill(ctx, x0, y0, x1, y1, spec) {
  const col = spec.motifCol || '#e8b040', m = spec.motif;
  ctx.save(); ctx.strokeStyle = col; ctx.fillStyle = col;
  if (m === 'ring') for (let y = y0 + 30; y < y1; y += 58) for (let x = x0 + ((y / 58) % 2 ? 0 : 29); x < x1; x += 58) { ctx.beginPath(); ctx.arc(x, y, 15, 0, TAU); ctx.lineWidth = 6; ctx.stroke(); ctx.beginPath(); ctx.arc(x, y, 4, 0, TAU); ctx.fill(); }
  else if (m === 'stripe') for (let y = y0; y < y1; y += 46) { ctx.fillRect(x0, y, x1 - x0, 16); }
  else if (m === 'kawung') for (let y = y0 + 30; y < y1; y += 60) for (let x = x0 + 30; x < x1; x += 60) for (let k = 0; k < 4; k++) { ctx.beginPath(); ctx.ellipse(x + Math.cos(k * TAU / 4) * 14, y + Math.sin(k * TAU / 4) * 14, 12, 7, k * TAU / 4, 0, TAU); ctx.fill(); }
  ctx.restore();
}

// pose = { eyes:'open'|'closed'|'happy'|'wide'|'half'|'shock', mouth:'smile'|'flat'|'o'|'grin'|'smirk'|'frown'|'wavy'|'teeth'|'talk',
//          brows:'flat'|'up'|'angry'|'worried'|'one', look:[x,y], blink:0..1, talk:0..1 (mouth flap), t,
//          armL:[a1,a2], armR:[a1,a2] (radians, 0 = hanging), walk:phase|null, bob, lean, tilt, flip, sweat:0..1, tears:0..1, blush }
export function drawPerson(ctx, spec, P) {
  const sx = 500, hy = spec.kid ? 430 : 390, a = spec.kid ? 290 : 300, b = spec.kid ? 245 : 250;
  const old = spec.old, look = P.look || [0, 0];
  ctx.save();
  ctx.translate(500, FEET); ctx.rotate(P.lean || 0); ctx.translate(-500, -FEET);
  if (P.flip) { ctx.translate(DW, 0); ctx.scale(-1, 1); }
  ctx.translate(0, (P.bob || 0) * 40);
  const shY = spec.kid ? 720 : 690, legTop = spec.kid ? 1130 : 1100;
  // ---- legs
  const walk = P.walk;
  const legCol = spec.sarong ? spec.skin : (spec.pants || '#333');
  for (const side of [-1, 1]) {
    const sw = walk == null ? 0 : Math.sin(walk + (side > 0 ? Math.PI : 0)) * .35;
    const lift = walk == null ? 0 : Math.max(0, Math.sin(walk + (side > 0 ? Math.PI : 0) + 1)) * 30;
    const x0 = sx + side * 70, x1 = x0 + Math.sin(sw) * 300 * side * 0 + Math.sin(sw) * 300;
    tube(ctx, [[x0, legTop], [lerp(x0, x1, .5) + side * 4, (legTop + FEET - 30) / 2], [x1, FEET - 30 - lift]], spec.sarong ? 34 : 40, legCol);
    ctx.beginPath(); ctx.ellipse(x1 + side * 14, FEET - 18 - lift, 58, 22, 0, 0, TAU); fillS(ctx, spec.sandal || '#3a2a2a', 12);
  }
  // ---- arms (behind the body when hanging, in front when raised)
  const arms = { L: P.armL || [.18, -.1], R: P.armR || [.18, -.1] };
  const armPts = {};
  for (const [k, side] of [['L', -1], ['R', 1]]) armPts[k] = limb(sx + side * 205, shY, side, arms[k][0], arms[k][1], 210, 190);
  const sleeve = spec.shirtStyle === 'office' ? spec.shirt : spec.shirt;
  const drawArm = k => {
    const p = armPts[k], short = spec.sleeve === 'short';
    if (short) { tube(ctx, [p[0], [lerp(p[0][0], p[1][0], .55), lerp(p[0][1], p[1][1], .55)]], 66, sleeve); tube(ctx, [[lerp(p[0][0], p[1][0], .5), lerp(p[0][1], p[1][1], .5)], p[1], p[2]], 46, spec.skin); }
    else tube(ctx, p, 60, sleeve);
    ctx.beginPath(); ctx.arc(p[2][0], p[2][1], 34, 0, TAU); fillS(ctx, spec.skin, 12);
  };
  const raised = k => arms[k][0] > 1.9;
  // ---- torso
  const tb = spec.sarong ? 1160 : 1120, tw = spec.kid ? .9 : 1;
  const torso = () => { ctx.beginPath(); ctx.moveTo(sx, 560); ctx.bezierCurveTo(sx + 190 * tw, 560, sx + 262 * tw, 720, sx + 276 * tw, 900); ctx.bezierCurveTo(sx + 290 * tw, tb - 70, sx + 190 * tw, tb, sx, tb); ctx.bezierCurveTo(sx - 190 * tw, tb, sx - 290 * tw, tb - 70, sx - 276 * tw, 900); ctx.bezierCurveTo(sx - 262 * tw, 720, sx - 190 * tw, 560, sx, 560); ctx.closePath(); };
  for (const k of ['L', 'R']) if (!raised(k)) drawArm(k);
  if (spec.sarong) { // sarong / skirt
    const sk = () => { ctx.beginPath(); ctx.moveTo(sx - 262, 930); ctx.lineTo(sx + 262, 930); ctx.quadraticCurveTo(sx + 250, 1200, sx + 205, 1345); ctx.lineTo(sx - 205, 1345); ctx.quadraticCurveTo(sx - 250, 1200, sx - 262, 930); ctx.closePath(); };
    sk(); ctx.fillStyle = spec.sarong; ctx.fill(); ctx.save(); sk(); ctx.clip(); motifFill(ctx, sx - 270, 930, sx + 270, 1350, spec); ctx.restore();
    shade(ctx, sk, sx - 270, sx + 270, 930, 1345, .25); sk(); stroke(ctx, 20);
  }
  torso(); ctx.fillStyle = spec.shirt; ctx.fill();
  ctx.save(); torso(); ctx.clip();
  if (spec.shirtStyle === 'office') { ctx.beginPath(); ctx.moveTo(sx - 70, 600); ctx.lineTo(sx, 760); ctx.lineTo(sx + 70, 600); ctx.closePath(); ctx.fillStyle = '#f4f4f0'; ctx.fill(); stroke(ctx, 10); }
  if (spec.shirtStyle === 'kebaya') { ctx.beginPath(); ctx.moveTo(sx - 90, 600); ctx.lineTo(sx, 800); ctx.lineTo(sx + 90, 600); stroke(ctx, 12, shadeHex(spec.shirt, .6)); for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(sx, 830 + i * 70, 10, 0, TAU); ctx.fillStyle = shadeHex(spec.shirt, .6); ctx.fill(); } }
  if (spec.shirtStyle === 'koko') { ctx.fillStyle = shadeHex(spec.shirt, .8); ctx.fillRect(sx - 14, 600, 28, 400); for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(sx, 660 + i * 85, 9, 0, TAU); ctx.fillStyle = '#b8a888'; ctx.fill(); } }
  if (spec.shirtStyle === 'apron') { ctx.beginPath(); ctx.roundRect(sx - 170, 760, 340, 420, 40); ctx.fillStyle = '#f4efe2'; ctx.fill(); stroke(ctx, 10); }
  ctx.restore();
  shade(ctx, torso, sx - 290, sx + 290, 560, tb, .26);
  torso(); stroke(ctx, 20);
  if (spec.shirtStyle === 'office') { // lanyard + ID card
    ctx.beginPath(); ctx.moveTo(sx - 95, 600); ctx.lineTo(sx, 900); ctx.lineTo(sx + 95, 600); stroke(ctx, 14, '#d8262e');
    ctx.beginPath(); ctx.roundRect(sx - 52, 890, 104, 136, 10); fillS(ctx, '#f8f8f6', 10);
    ctx.fillStyle = '#6a8fc8'; ctx.fillRect(sx - 34, 910, 68, 44); ctx.fillStyle = '#bbb'; for (let i = 0; i < 3; i++) ctx.fillRect(sx - 34, 968 + i * 16, 68 - i * 14, 8);
  }
  // ---- head
  drawHead(ctx, spec, P, sx, hy, a, b, old, look);
  for (const k of ['L', 'R']) if (raised(k)) drawArm(k);
  ctx.restore();
}

function drawHead(ctx, spec, P, cx, cy, a, b, old, look) {
  ctx.save();
  ctx.translate(cx, cy + b); ctx.rotate(P.tilt || 0); ctx.translate(-cx, -cy - b);
  const hair = spec.hair, hc = spec.hairCol || '#1f1820';
  const hp = () => headPath(ctx, cx, cy, a, b);
  // back hair / hijab
  if (hair === 'bun') { ctx.beginPath(); ctx.arc(cx, cy - b - 45, 100, 0, TAU); fillS(ctx, hc, 20); sheen(ctx, cx - 30, cy - b - 70, 50, hc); }
  if (hair === 'bob' || hair === 'long') { const L = hair === 'long' ? 1.15 : .45; ctx.beginPath(); ctx.moveTo(cx - a * 1.1, cy - b * .2); ctx.quadraticCurveTo(cx - a * 1.18, cy + b * L, cx - a * .95, cy + b * (L + .15)); ctx.lineTo(cx + a * .95, cy + b * (L + .15)); ctx.quadraticCurveTo(cx + a * 1.18, cy + b * L, cx + a * 1.1, cy - b * .2); ctx.closePath(); fillS(ctx, hc, 20); }
  if (hair === 'hijab') {
    const hj = spec.hijabCol || '#2f8f98';
    const back = () => { headPath(ctx, cx, cy + 10, a * 1.2, b * 1.22, 2.4); };
    ctx.beginPath(); ctx.moveTo(cx - a * 1.12, cy + b * .2); ctx.quadraticCurveTo(cx - a * 1.05, cy + b * 1.65, cx - a * .3, cy + b * 1.75); ctx.lineTo(cx + a * .3, cy + b * 1.75); ctx.quadraticCurveTo(cx + a * 1.05, cy + b * 1.65, cx + a * 1.12, cy + b * .2); ctx.closePath(); fillS(ctx, hj, 20);
    shade(ctx, () => { ctx.beginPath(); ctx.rect(cx - a * 1.3, cy, a * 2.6, b * 1.8); }, cx - a * 1.2, cx + a * 1.2, cy, cy + b * 1.8, .22);
    back(); fillS(ctx, hj, 20); shade(ctx, back, cx - a * 1.2, cx + a * 1.2, cy - b * 1.3, cy + b * 1.3, .24);
    sheen(ctx, cx - a * .55, cy - b * .95, 110, hj);
  }
  // skin
  hp(); ctx.fillStyle = spec.skin; ctx.fill();
  shade(ctx, hp, cx - a, cx + a, cy - b, cy + b, .2);
  hp(); stroke(ctx, 20);
  // face
  drawFace(ctx, spec, P, cx, cy, a, b, old, look);
  // front hair
  if (hair === 'bun' || hair === 'bob' || hair === 'short' || hair === 'spiky' || hair === 'long') {
    const fr = () => {
      ctx.beginPath(); ctx.moveTo(cx - a * 1.05, cy + (hair === 'bun' ? -b * .05 : b * .05));
      if (hair === 'bun') { ctx.quadraticCurveTo(cx - a * .7, cy - b * .55, cx - a * .1, cy - b * .5); ctx.quadraticCurveTo(cx + a * .5, cy - b * .62, cx + a * 1.05, cy - b * .02); }
      else if (hair === 'bob' || hair === 'long') { ctx.quadraticCurveTo(cx - a * .85, cy - b * .45, cx - a * .35, cy - b * .5); ctx.quadraticCurveTo(cx + a * .2, cy - b * .3, cx + a * .45, cy - b * .55); ctx.quadraticCurveTo(cx + a * .9, cy - b * .45, cx + a * 1.05, cy + b * .05); }
      else { ctx.quadraticCurveTo(cx - a * .8, cy - b * .5, cx - a * .3, cy - b * .55); ctx.lineTo(cx - a * .1, cy - b * .4); ctx.lineTo(cx + a * .15, cy - b * .58); ctx.lineTo(cx + a * .35, cy - b * .45); ctx.quadraticCurveTo(cx + a * .9, cy - b * .55, cx + a * 1.05, cy + b * .0); }
      ctx.lineTo(cx + a * 1.3, cy - b * 1.6); ctx.lineTo(cx - a * 1.3, cy - b * 1.6); ctx.closePath();
    };
    ctx.save(); headPath(ctx, cx, cy - 4, a * 1.03, b * 1.03); ctx.clip(); fr(); ctx.fillStyle = hc; ctx.fill(); ctx.restore();
    ctx.save(); headPath(ctx, cx, cy - 4, a * 1.03, b * 1.03); ctx.clip(); fr(); stroke(ctx, 18); ctx.restore();
    if (hair === 'spiky') for (let i = 0; i < 6; i++) { const x = cx - a * .75 + i * a * .3; ctx.beginPath(); ctx.moveTo(x - 40, cy - b * .9); ctx.lineTo(x + 5, cy - b * 1.22 - (i % 2) * 20); ctx.lineTo(x + 45, cy - b * .88); fillS(ctx, hc, 16); }
    headPath(ctx, cx, cy - 4, a * 1.03, b * 1.03); ctx.save(); ctx.clip(); ctx.restore();
    sheen(ctx, cx - a * .45, cy - b * .78, 120, hc);
  }
  if (hair === 'peci') { // velvet cap sitting on the head, a little hair showing at the temples
    for (const s of [-1, 1]) { ctx.save(); hp(); ctx.clip(); ctx.beginPath(); ctx.ellipse(cx + s * a * .92, cy - b * .3, a * .16, b * .3, 0, 0, TAU); ctx.fillStyle = hc; ctx.fill(); stroke(ctx, 12); ctx.restore(); }
    hp(); stroke(ctx, 20);
    ctx.beginPath(); ctx.moveTo(cx - a * .86, cy - b * .5); ctx.lineTo(cx - a * .8, cy - b * 1.08); ctx.quadraticCurveTo(cx, cy - b * 1.2, cx + a * .8, cy - b * 1.08); ctx.lineTo(cx + a * .86, cy - b * .5); ctx.quadraticCurveTo(cx, cy - b * .62, cx - a * .86, cy - b * .5); fillS(ctx, '#1a1418', 18);
    ctx.beginPath(); ctx.moveTo(cx - a * .55, cy - b * .98); ctx.quadraticCurveTo(cx - a * .1, cy - b * 1.06, cx + a * .25, cy - b * 1.02); stroke(ctx, 10, 'rgba(255,255,255,.35)');
  }
  if (hair === 'hijab') { // front band over the forehead
    const hj = spec.hijabCol || '#2f8f98';
    ctx.save(); hp(); ctx.clip(); ctx.beginPath(); ctx.moveTo(cx - a * 1.1, cy - b * .05); ctx.quadraticCurveTo(cx, cy - b * .78, cx + a * 1.1, cy - b * .05); ctx.lineTo(cx + a * 1.2, cy - b * 1.3); ctx.lineTo(cx - a * 1.2, cy - b * 1.3); ctx.closePath(); ctx.fillStyle = hj; ctx.fill(); stroke(ctx, 18); ctx.restore();
    hp(); stroke(ctx, 20);
  }
  // sweat / tears
  if (P.sweat > 0) { const x = cx + a * .98, y = cy - b * .35 + (1 - P.sweat) * -20; ctx.save(); ctx.globalAlpha = P.sweat; ctx.beginPath(); ctx.moveTo(x, y - 45); ctx.quadraticCurveTo(x + 32, y + 5, x, y + 26); ctx.quadraticCurveTo(x - 32, y + 5, x, y - 45); fillS(ctx, '#8fd8ff', 10); ctx.restore(); }
  if (P.tears > 0) for (const s of [-1, 1]) { ctx.save(); ctx.globalAlpha = P.tears; ctx.beginPath(); ctx.moveTo(cx + s * a * .33, cy + 30); ctx.quadraticCurveTo(cx + s * a * .4, cy + b * .5, cx + s * a * .35, cy + b * .9); stroke(ctx, 22, '#8fd8ff'); ctx.restore(); }
  ctx.restore();
}
function sheen(ctx, x, y, r, base) { // the white streak on hair
  ctx.save(); ctx.globalAlpha = .85; ctx.beginPath(); ctx.arc(x + r * .6, y + r * .9, r, Math.PI * 1.15, Math.PI * 1.45); stroke(ctx, 12, '#ffffff'); ctx.beginPath(); ctx.arc(x + r * .6, y + r * .9, r * .78, Math.PI * 1.2, Math.PI * 1.32); stroke(ctx, 8, 'rgba(255,255,255,.7)'); ctx.restore();
}
function drawFace(ctx, spec, P, cx, cy, a, b, old, look) {
  const ey = cy - b * .02, ex = a * .34, eyes = P.eyes || 'open', blink = P.blink || 0;
  const iris = spec.eyes === 'iris';
  // blush
  ctx.save(); ctx.globalAlpha = P.blush === false ? 0 : .3; ctx.fillStyle = '#e8606a';
  for (const s of [-1, 1]) { ctx.beginPath(); ctx.ellipse(cx + s * a * .62, cy + b * .3, 52, 28, 0, 0, TAU); ctx.fill(); } ctx.restore();
  // eyes
  for (const s of [-1, 1]) {
    const x = cx + s * ex, y = ey;
    if (eyes === 'closed' || blink > .85) { ctx.beginPath(); ctx.arc(x, y - 6, 30, .2 * Math.PI, .8 * Math.PI); stroke(ctx, 13); continue; }
    if (eyes === 'happy') { ctx.beginPath(); ctx.arc(x, y + 14, 30, 1.15 * Math.PI, 1.85 * Math.PI); stroke(ctx, 13); continue; }
    const open = 1 - blink;
    if (iris) {
      const r = eyes === 'wide' || eyes === 'shock' ? 62 : 54;
      ctx.save(); ctx.beginPath(); ctx.ellipse(x, y, r, r * open, 0, 0, TAU); ctx.fillStyle = '#fbfbf7'; ctx.fill(); stroke(ctx, 11); ctx.clip();
      const ir = eyes === 'shock' ? 16 : 32, px = x + look[0] * 16, py = y + look[1] * 12;
      ctx.beginPath(); ctx.arc(px, py, ir, 0, TAU); const g = ctx.createRadialGradient(px, py - 10, 4, px, py, ir); g.addColorStop(0, '#a6d4f2'); g.addColorStop(1, spec.irisCol || '#4f8fc8'); ctx.fillStyle = g; ctx.fill();
      ctx.beginPath(); ctx.arc(px, py, ir * .45, 0, TAU); ctx.fillStyle = INK; ctx.fill();
      ctx.beginPath(); ctx.arc(px - ir * .35, py - ir * .4, ir * .28, 0, TAU); ctx.fillStyle = '#fff'; ctx.fill();
      if (eyes === 'half') { ctx.fillStyle = spec.skin; ctx.fillRect(x - r - 5, y - r - 5, r * 2 + 10, r * .95); }
      ctx.restore();
      if (eyes === 'half') { ctx.beginPath(); ctx.moveTo(x - r, y - r * .05); ctx.lineTo(x + r, y - r * .05); stroke(ctx, 11); }
      if (old) { ctx.beginPath(); ctx.arc(x, y + 8, r + 14, .25 * Math.PI, .6 * Math.PI); stroke(ctx, 6, 'rgba(90,50,40,.55)'); }
    } else {
      const ry = (eyes === 'wide' ? 40 : eyes === 'shock' ? 30 : 33) * open, rx = eyes === 'wide' ? 30 : 24;
      const px = x + look[0] * 10, py = y + look[1] * 8;
      if (eyes === 'shock' || eyes === 'wide') { ctx.beginPath(); ctx.ellipse(x, y, 46, 50 * open, 0, 0, TAU); fillS(ctx, '#fbfbf7', 10); }
      ctx.beginPath(); ctx.ellipse(px, py, eyes === 'shock' ? 14 : rx, eyes === 'shock' ? 16 : Math.max(2, ry), 0, 0, TAU); ctx.fillStyle = INK; ctx.fill();
      if (ry > 12 && eyes !== 'shock') { ctx.beginPath(); ctx.arc(px - 7, py - 11, 8, 0, TAU); ctx.fillStyle = '#fff'; ctx.fill(); }
      if (eyes === 'half') { ctx.fillStyle = spec.skin; ctx.fillRect(x - 40, y - 50, 80, 48); ctx.beginPath(); ctx.moveTo(x - 34, y - 2); ctx.lineTo(x + 34, y - 2); stroke(ctx, 11); }
    }
  }
  // brows
  const bc = spec.browCol || INK, bw = old ? 18 : 22, by = ey - (iris ? 95 : 72), br = P.brows || 'flat';
  for (const s of [-1, 1]) {
    const x = cx + s * ex; let inner = 0, outer = 0, arch = 8;
    if (br === 'up') { inner = -22; outer = -16; arch = 14; }
    if (br === 'angry') { inner = 22; outer = -10; arch = 0; }
    if (br === 'worried') { inner = -24; outer = 10; arch = 4; }
    if (br === 'one' && s > 0) { inner = -26; outer = -26; arch = 16; }
    ctx.beginPath(); ctx.moveTo(x + s * 50, by + outer); ctx.quadraticCurveTo(x, by - arch + (inner + outer) / 2, x - s * 48, by + inner); stroke(ctx, bw, bc);
  }
  if (old) { // forehead + smile lines
    for (let i = 0; i < 2; i++) { ctx.beginPath(); ctx.moveTo(cx - 60, cy - b * .5 - i * 26); ctx.quadraticCurveTo(cx, cy - b * .56 - i * 26, cx + 60, cy - b * .5 - i * 26); stroke(ctx, 6, 'rgba(90,50,40,.4)'); }
    for (const s of [-1, 1]) { ctx.beginPath(); ctx.arc(cx + s * 120, cy + b * .45, 50, s > 0 ? -.4 : Math.PI - .9, s > 0 ? .9 : Math.PI + .4); stroke(ctx, 6, 'rgba(90,50,40,.4)'); }
  }
  // nose
  ctx.beginPath(); ctx.moveTo(cx + 4, cy + b * .08); ctx.quadraticCurveTo(cx + 34, cy + b * .22, cx + 2, cy + b * .3); stroke(ctx, 11);
  // mouth
  const my = cy + b * .5; let m = P.mouth || 'smile';
  if (P.talk > 0) { const k = Math.abs(Math.sin((P.t || 0) * 17)) * P.talk; if (k > .25) { ctx.beginPath(); ctx.ellipse(cx, my + 4, 30 + k * 6, 8 + k * 22, 0, 0, TAU); fillS(ctx, '#6a2028', 11); return; } }
  if (m === 'smile') { ctx.beginPath(); ctx.arc(cx, my - 36, 52, .3 * Math.PI, .7 * Math.PI); stroke(ctx, 12); }
  else if (m === 'flat') { ctx.beginPath(); ctx.moveTo(cx - 36, my); ctx.lineTo(cx + 36, my); stroke(ctx, 12); }
  else if (m === 'frown') { ctx.beginPath(); ctx.arc(cx, my + 40, 42, 1.25 * Math.PI, 1.75 * Math.PI); stroke(ctx, 12); }
  else if (m === 'smirk') { ctx.beginPath(); ctx.moveTo(cx - 34, my + 6); ctx.quadraticCurveTo(cx + 10, my + 18, cx + 44, my - 16); stroke(ctx, 12); }
  else if (m === 'o') { ctx.beginPath(); ctx.ellipse(cx, my + 4, 24, 30, 0, 0, TAU); fillS(ctx, '#6a2028', 11); }
  else if (m === 'wavy') { ctx.beginPath(); for (let i = 0; i <= 16; i++) { const x = cx - 50 + i * 6.25, y = my + Math.sin(i * 1.4) * 9; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } stroke(ctx, 11); }
  else if (m === 'grin') { ctx.beginPath(); ctx.moveTo(cx - 62, my - 14); ctx.quadraticCurveTo(cx, my - 4, cx + 62, my - 14); ctx.quadraticCurveTo(cx + 52, my + 52, cx, my + 50); ctx.quadraticCurveTo(cx - 52, my + 52, cx - 62, my - 14); ctx.closePath(); ctx.fillStyle = '#6a2028'; ctx.fill(); ctx.save(); ctx.clip(); ctx.fillStyle = '#fff'; ctx.fillRect(cx - 70, my - 20, 140, 22); ctx.beginPath(); ctx.ellipse(cx, my + 46, 34, 18, 0, 0, TAU); ctx.fillStyle = '#e8707a'; ctx.fill(); ctx.restore(); ctx.beginPath(); ctx.moveTo(cx - 62, my - 14); ctx.quadraticCurveTo(cx, my - 4, cx + 62, my - 14); ctx.quadraticCurveTo(cx + 52, my + 52, cx, my + 50); ctx.quadraticCurveTo(cx - 52, my + 52, cx - 62, my - 14); stroke(ctx, 11); }
  else if (m === 'teeth') { ctx.beginPath(); ctx.roundRect(cx - 52, my - 20, 104, 44, 10); fillS(ctx, '#fbfbf7', 11); for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(cx + i * 18, my - 20); ctx.lineTo(cx + i * 18, my + 24); stroke(ctx, 6); } ctx.beginPath(); ctx.moveTo(cx - 52, my + 2); ctx.lineTo(cx + 52, my + 2); stroke(ctx, 6); }
}

// ---------- the 3D card ----------
export class Person {
  // scene: from makeScene().scene; spec: LOOKS.x or your own; o: { x, z, h (metres, feet to crown), rot }
  constructor(scene, spec, o = {}) {
    this.spec = spec; this.P = {}; this.key = '';
    this.c = document.createElement('canvas'); this.c.width = DW * RES; this.c.height = DH * RES; this.ctx = this.c.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.c); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8;
    const h = o.h || 1.55, k = h / (FEET - TOP);
    const geo = new THREE.PlaneGeometry(DW * k, DH * k); geo.translate(0, (FEET - DH / 2) * k, 0);
    const tint = (scene.userData.mood && scene.userData.mood.tint) || '#ffffff';
    this.mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: this.tex, alphaTest: .5, side: THREE.DoubleSide, color: o.tint || tint }));
    this.mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: this.tex, alphaTest: .5 });
    this.mesh.castShadow = true; this.mesh.position.set(o.x || 0, o.y || 0, o.z || 0); this.k = k; this.h = h;
    scene.add(this.mesh); scene.userData.chars.push(this);
  }
  set(P) { this.P = P; return this; }
  at(x, z, y = 0) { this.mesh.position.set(x, y, z); return this; }
  // world position of the face, handy for aiming the camera
  face3() { const p = this.mesh.position; return [p.x, p.y + (FEET - (this.spec.kid ? 430 : 390)) * this.k, p.z]; }
  face(cam) {
    const p = this.mesh.position; this.mesh.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z);
    const P = Object.assign({}, this.P); if (P.talk) P.t = Math.round((P.t || 0) * 30) / 30; else delete P.t;
    const key = JSON.stringify(P); if (key === this.key) return; this.key = key;
    const ctx = this.ctx; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, this.c.width, this.c.height); ctx.scale(RES, RES);
    drawPerson(ctx, this.spec, P); this.tex.needsUpdate = true;
  }
}
// blink helper: natural blinks every few seconds
export const blinkAt = (t, seed = 0) => { const p = (t + seed * 1.37) % 3.7; return p < .12 ? Math.sin(p / .12 * Math.PI) : 0; };
