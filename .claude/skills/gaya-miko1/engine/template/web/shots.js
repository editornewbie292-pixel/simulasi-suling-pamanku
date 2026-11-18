// ---------- example reel: "Kunang-kunang" (a scared kid, his grandfather, and fireflies) ----------
// Shots are timed by the voice: L(i) = start of script line i, T('kata') = start of a word.
// Re-running align with a new voiceover re-times everything automatically.
import { THREE, shot, makeScene, camera, camMove, focusSun, kf, lerp, clamp, smooth, backOut, L, T, DUR, M, mat, glowMat, rng, TAU, start } from './core.js';
import { Person, LOOKS, SKIN, blinkAt } from './chars.js';
import * as w from './world.js';

const BIMA = { ...LOOKS.anak, shirt: '#e8564a', pants: '#2f4f8f' };
const KAKEK = { skin: SKIN.gelap, hair: 'peci', hairCol: '#e9e5dd', old: true, eyes: 'iris', browCol: '#d8d2c8', shirt: '#e8e4dc', shirtStyle: 'koko', sleeve: 'long', sarong: '#4f6f8f', motif: 'stripe', motifCol: '#36506a' };

// the kampung alley at night
function alley(mood = 'night') {
  const S = makeScene(mood); const { scene } = S;
  w.ground(scene, { kind: 'tile', tile: 3 });
  w.houseRow(scene, { side: -1, z0: 8, n: 7, seed: 4 }); w.houseRow(scene, { side: 1, z0: 8, n: 7, seed: 8 });
  w.clothesline(scene, [-2.5, -1], [2.5, -2], { y: 2.7, n: 6 });
  w.mountain(scene, -20, -90, 45, 38, '#26315e'); w.mountain(scene, 25, -100, 40, 30, '#202a52');
  w.moon(scene, [-.3, .5, -1]);
  return S;
}
// paddy fields at the edge of the village
function sawah(mood = 'night') {
  const S = makeScene(mood); const { scene } = S;
  w.ground(scene, { kind: 'grass', tile: 4, color: mood === 'glow' ? '#6a9a7a' : '#ffffff' });
  w.rice(scene, { x: 0, z: -104, size: 200, col: mood === 'glow' ? '#3f7a3a' : '#5f9a42' });
  w.box(scene, 200, .25, 1.6, '#8a6a48', [0, .02, .6], { ink: false });
  for (let i = 0; i < 6; i++) w.tree(scene, -16 + i * 7 + (i % 2) * 2, -26 - (i % 3) * 6, 1.4, { leaf: '#3f6a3a' });
  w.bamboo(scene, { x: -7, z: -9, n: 12, r: 1.4, h: 8, col: '#7f9a46', glow: mood === 'glow' ? .25 : 0 });
  w.mountain(scene, -25, -110, 50, 40, mood === 'glow' ? '#0f2a1c' : '#26315e'); w.mountain(scene, 30, -120, 45, 32, mood === 'glow' ? '#0c2216' : '#202a52');
  if (mood !== 'glow') w.moon(scene, [.35, .45, -1]);
  return S;
}
// a firefly, built from simple shapes; returns { g, tail, light }
function firefly(scene, s = 1) {
  const g = new THREE.Group();
  g.add(M(new THREE.CapsuleGeometry(.12 * s, .28 * s, 6, 10), '#3a2a24', [0, 0, 0], { rot: [0, 0, Math.PI / 2] }));
  g.add(M(new THREE.SphereGeometry(.13 * s, 12, 10), '#e0663a', [-.26 * s, .03 * s, 0]));
  for (const k of [-1, 1]) { const wing = M(new THREE.SphereGeometry(.22 * s, 12, 8), new THREE.MeshToonMaterial({ color: '#d8e8f0', transparent: true, opacity: .55 }), [0, .14 * s, k * .12 * s], { inkW: 2 }); wing.scale.set(1.3, .18, .6); wing.rotation.y = k * .35; g.add(wing); }
  for (const k of [-1, 1]) g.add(M(new THREE.CylinderGeometry(.008 * s, .008 * s, .3 * s, 4), '#2a1c18', [-.4 * s, .12 * s, k * .06 * s], { rot: [k * .4, 0, .9], ink: false }));
  const tail = new THREE.Mesh(new THREE.SphereGeometry(.15 * s, 16, 12), glowMat('#c8ff5a', 1.3)); tail.position.set(.32 * s, -.02 * s, 0); tail.scale.set(1.2, .9, .9); g.add(tail);
  const light = new THREE.PointLight('#b8ff6a', 4, 3 * s, 1.6); light.position.copy(tail.position); g.add(light);
  scene.add(g); return { g, tail, light };
}

// 1. Bima at his door; the lights go out
shot(0, L(1), () => {
  const S = alley('night'), cam = camera(36), { scene } = S;
  const lampA = w.lamp(scene, -2.2, 2.55, 1.2, { power: 3, dist: 6 }), lampB = w.lamp(scene, 2.2, 2.55, -5, { power: 3, dist: 6 });
  const bima = new Person(scene, BIMA, { x: -1.55, z: 1.2, h: 1.05 });
  const off = T('padam');
  return { scene, cam, update(lt, t) {
    const dark = clamp((t - off) / .15);
    for (const L of [lampA, lampB]) { L.children[2].intensity = (1 - dark) * 3 * (1 + Math.sin(t * 40) * .03); L.children[1].material.color.set(dark > .5 ? '#3a3020' : '#ffd890').multiplyScalar(dark > .5 ? 1 : 2.5); }
    S.hemi.intensity = lerp(1.0, .55, dark); S.sun.intensity = lerp(1.1, .7, dark);
    const scared = t > T('takut');
    bima.set({ eyes: dark > .5 ? 'shock' : scared ? 'wide' : 'open', mouth: dark > .5 ? 'wavy' : scared ? 'flat' : 'smile', brows: scared ? 'worried' : 'flat', look: [Math.sin(t * 1.3) * .8, -.2],
      blink: blinkAt(t), sweat: dark > .5 ? clamp((t - off) * 3) : 0, armL: scared ? [.5, -1.6] : [.15, -.1], armR: scared ? [.5, -1.6] : [.15, -.1], bob: dark > .5 ? Math.sin(t * 30) * .004 : 0 });
    const f = bima.face3();
    camMove(cam, lt, [[0, [1.0, 1.15, 6.2], [f[0] + .25, f[1] - .25, f[2]]], [L(1) - .1, [-.2, .95, 3.3], [f[0] + .1, f[1] - .12, f[2]]]], .03, 1);
  } };
});

// 2. Grandfather walks him to the paddy fields
shot(L(1), L(2), () => {
  const S = sawah('night'), cam = camera(34), { scene } = S; focusSun(S.sun, 0, 0, 16);
  const kakek = new Person(scene, KAKEK, { h: 1.6 }), bima = new Person(scene, BIMA, { h: 1.05 });
  const dur = L(2) - L(1);
  return { scene, cam, update(lt, t) {
    const x = lerp(-2.6, .6, lt / dur);
    kakek.at(x + .75, .6); bima.at(x - .15, .75);
    kakek.set({ eyes: 'open', mouth: 'smile', look: [-.6, .2], blink: blinkAt(t, 2), walk: t * 6, armL: [.55, -.15], armR: [.15, -.1], tilt: -.03 });
    bima.set({ eyes: 'open', mouth: 'flat', brows: 'worried', look: [.8, -.6], blink: blinkAt(t, 1), walk: t * 7.5 + 1, armR: [1.2, -.2], armL: [.15, -.1] });
    camMove(cam, lt, [[0, [x - .2, 1.3, 6.2], [x + .4, 1.0, 0]], [dur, [x + .3, 1.2, 5.6], [x + .5, .95, 0]]], .03, 2);
  } };
});

// 3. Hundreds of green lights over the paddy
shot(L(2), L(3), () => {
  const S = sawah('glow'), cam = camera(40), { scene } = S;
  w.specks(scene, { x: 0, z: -9, w: 26, d: 16, h: 3.5, n: 260, col: '#b8ff6a', size: 6 });
  w.specks(scene, { x: 0, z: -3, w: 10, d: 6, h: 2.5, n: 40, col: '#d8ff8a', size: 11, seed: 9 });
  w.glowShrooms(scene, -3, -2.5, { n: 6, s: .8 });
  const kakek = new Person(scene, KAKEK, { x: .55, z: 0, h: 1.6 }), bima = new Person(scene, BIMA, { x: -.1, z: .3, h: 1.05 });
  const dur = L(3) - L(2);
  return { scene, cam, update(lt, t) {
    const wow = t > T('berkedip');
    kakek.set({ eyes: 'open', mouth: 'smile', look: [-.8, -.6], blink: blinkAt(t, 2) });
    bima.set({ eyes: wow ? 'wide' : 'open', mouth: wow ? 'o' : 'flat', brows: 'up', look: [-.6, -1], blink: wow ? 0 : blinkAt(t, 1) });
    camMove(cam, lt, [[0, [0, .75, 6.5], [0, 1.2, -6]], [dur, [.35, .95, 4.4], [-.2, 1.35, -6]]], .025, 3);
  } };
});

// 4. "Kunang-kunang," says Grandfather
shot(L(3), L(4), () => {
  const S = sawah('glow'), cam = camera(30), { scene } = S;
  w.specks(scene, { x: 0, z: -5, w: 14, d: 8, h: 3, n: 160, col: '#b8ff6a', size: 7 });
  const kakek = new Person(scene, KAKEK, { x: 0, z: 0, h: 1.6 });
  const glow = new THREE.PointLight('#9dff7a', 3, 4, 1.5); glow.position.set(-.8, 1.4, 1); scene.add(glow);
  return { scene, cam, update(lt, t) {
    const talking = t < T.end('kata') + .1;
    kakek.set({ eyes: 'open', mouth: 'smile', talk: talking ? 1 : 0, t, brows: 'up', look: [.3, 0], blink: blinkAt(t, 3) });
    const f = kakek.face3();
    camMove(cam, lt, [[0, [.2, f[1] - .15, 3.2], [f[0], f[1] - .22, f[2]]], [L(4) - L(3), [.05, f[1] - .12, 2.6], [f[0], f[1] - .2, f[2]]]], .015, 4);
  } };
});

// 5. Inside its belly: chemicals glow when they meet oxygen
shot(L(4), L(5), () => {
  const S = makeScene('glow', { fog: ['#06140c', 4, 30] }), cam = camera(34), { scene } = S;
  w.specks(scene, { x: 0, z: -4, w: 12, d: 8, h: 4, n: 90, col: '#9dff6a', size: 5 });
  const ff = firefly(scene, 1.0); ff.g.position.set(0, 1.5, 0);
  // oxygen bubbles drifting into the tail
  const R = rng(4), bubbles = [];
  for (let i = 0; i < 9; i++) { const b = M(new THREE.SphereGeometry(.06 + R() * .05, 12, 8), '#9fd8ff', [0, 0, 0], { inkW: 2 }); scene.add(b); bubbles.push([b, R() * TAU, .4 + R() * .5]); }
  const ox = T('oksigen'), dur = L(5) - L(4);
  return { scene, cam, update(lt, t) {
    ff.g.position.y = 1.5 + Math.sin(t * 1.5) * .06; ff.g.rotation.y = -.35 + Math.sin(t * .6) * .1;
    const pulse = .6 + .4 * Math.sin(t * 4) + (t > ox ? .5 : 0);
    ff.tail.material.color.set('#c8ff5a').multiplyScalar(.9 + pulse * .5); ff.light.intensity = 2 + pulse * 2;
    const tp = ff.tail.getWorldPosition(new THREE.Vector3());
    bubbles.forEach(([b, ph, sp], i) => { const k = ((lt * sp + i / 9) % 1); const a = ph + lt * .5; b.position.set(tp.x + Math.cos(a) * (.7 - k * .65), tp.y + (1 - k) * .55 - .15, tp.z + Math.sin(a) * (.7 - k * .65)); b.scale.setScalar(.6 - k * .4); b.visible = t > ox - .6; });
    const a = lerp(-.5, .55, smooth(lt / dur));
    camMove(cam, lt, [[0, [Math.sin(a) * 2.4, 1.75, Math.cos(a) * 2.4], [0, 1.5, 0]], [dur, [Math.sin(a) * 1.9, 1.62, Math.cos(a) * 1.9], [0, 1.5, 0]]], .015, 5);
  } };
});

// 6. Its light is almost cold: Bima holds one
shot(L(5), L(6), () => {
  const S = sawah('glow'), cam = camera(30), { scene } = S;
  w.specks(scene, { x: 0, z: -4, w: 12, d: 8, h: 3, n: 140, col: '#b8ff6a', size: 7 });
  const bima = new Person(scene, BIMA, { x: 0, z: 0, h: 1.05 });
  const ball = new THREE.Mesh(new THREE.SphereGeometry(.035, 12, 8), glowMat('#d8ff7a', 1.4)); scene.add(ball);
  const L1 = new THREE.PointLight('#b8ff6a', 1.2, 1.5, 1.6); scene.add(L1);
  return { scene, cam, update(lt, t) {
    bima.set({ eyes: lt > .6 ? 'happy' : 'wide', mouth: lt > .6 ? 'grin' : 'o', brows: 'up', look: [0, .8], armL: [.6, -1.9], armR: [.6, -1.9] });
    const p = bima.mesh.position, hy = (1470 - 900) * bima.k;
    ball.position.set(p.x, hy + Math.sin(t * 3) * .02, p.z + .12); L1.position.set(p.x, hy + .1, p.z + .35); L1.intensity = 1.1 + Math.sin(t * 5) * .4;
    const f = bima.face3();
    camMove(cam, lt, [[0, [.3, .75, 2.2], [0, .62, 0]], [L(6) - L(5), [.1, .72, 1.7], [0, .64, 0]]], .015, 6);
  } };
});

// 7. They blink to call a partner
shot(L(6), L(7), () => {
  const S = makeScene('glow', { fog: ['#06140c', 4, 30] }), cam = camera(36), { scene } = S;
  w.specks(scene, { x: 0, z: -5, w: 14, d: 10, h: 4, n: 120, col: '#9dff6a', size: 5 });
  w.bamboo(scene, { x: -3, z: -4, n: 8, r: 1, h: 7, col: '#3f5a2a', glow: .2 });
  const a = firefly(scene, .8), b = firefly(scene, .8);
  a.g.position.set(-.35, 2.0, 0); b.g.position.set(.35, 1.15, -.3); b.g.rotation.y = Math.PI;
  const dur = L(7) - L(6);
  return { scene, cam, update(lt, t) {
    const on1 = Math.sin(t * 6) > .3, on2 = Math.sin(t * 6 - 2.2) > .3;
    for (const [f, on] of [[a, on1], [b, on2]]) { f.tail.material.color.set(on ? '#c8ff5a' : '#2a3a1a').multiplyScalar(on ? 1.5 : 1); f.light.intensity = on ? 3 : .2; }
    a.g.position.y = 2.0 + Math.sin(t * 1.7) * .06; b.g.position.y = 1.15 + Math.sin(t * 1.4 + 1) * .06;
    camMove(cam, lt, [[0, [-.4, 1.6, 4.0], [0, 1.58, 0]], [dur, [.35, 1.55, 3.3], [0, 1.58, 0]]], .02, 7);
  } };
});

// 8. Since that night, Bima waits for the power cut
shot(L(7), 999, () => {
  const S = alley('night'), cam = camera(34), { scene } = S;
  w.specks(scene, { x: -1, z: 0, w: 5, d: 4, h: 2.4, n: 40, col: '#b8ff6a', size: 8 });
  const bima = new Person(scene, BIMA, { x: -1.55, z: 1.2, h: 1.05 });
  S.hemi.intensity = .6;
  return { scene, cam, update(lt, t) {
    const waiting = t > T('menunggu');
    bima.set({ eyes: waiting ? 'happy' : 'open', mouth: waiting ? 'grin' : 'smile', brows: 'up', look: [-.5, -.8], blink: blinkAt(t), armL: waiting ? [2.5, .2] : [.15, -.1], armR: [.15, -.1] });
    const f = bima.face3();
    camMove(cam, lt, [[0, [-.3, .9, 3.0], [f[0], f[1] - .1, f[2]]], [3.5, [.6, 1.3, 5.5], [f[0] + .2, f[1] + .1, f[2]]]], .025, 8);
  } };
});

start();
