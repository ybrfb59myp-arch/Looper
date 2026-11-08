/* ---------- DSP: resampling (transpozycja) + WSOLA (tempo bez zmiany wysokości) ---------- */
function resampleLen(n, P){ return Math.max(1, Math.floor((n - 1) / P) + 1); }

// y[i] = x(i * P), Catmull-Rom interpolation. Played back at the original rate this shifts pitch by P.
function* resampleGen(x, P, y){
  const L = y.length, last = x.length - 1, CH = 1 << 16;
  for (let s = 0; s < L; s += CH){
    const e = Math.min(L, s + CH);
    for (let i = s; i < e; i++){
      const p = i * P;
      let i1 = p | 0; if (i1 > last) i1 = last;
      const f = p - i1;
      const i0 = i1 > 0 ? i1 - 1 : 0;
      const i2 = i1 < last ? i1 + 1 : last;
      const i3 = i1 + 2 <= last ? i1 + 2 : last;
      const p0 = x[i0], p1 = x[i1], p2 = x[i2], p3 = x[i3];
      y[i] = p1 + 0.5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0)));
    }
    yield e / L;
  }
}

// out[i] = x[i - off] (zero outside)
function alignCopy(x, off, out){
  const a = Math.max(0, off), s = a - off;
  const len = Math.min(out.length - a, x.length - s);
  if (len > 0) out.set(x.subarray(s, s + len), a);
}

/*
  WSOLA time stretch by factor S (output length = Ly * S), pitch preserved.
  Ys[t] / Os[t]: track t lives at y-domain index i = j + Os[t] for its sample j.
  The search runs on the mix of all tracks, then every track is overlap-added with the
  same frame positions, so the tracks stay locked to each other.
*/
function* wsolaGen(Ys, Os, Ly, S, sr, outs){
  let N = 1024; while (N < sr * 0.04) N *= 2;
  const Hs = N >> 1, Ha = Hs / S;
  const win = new Float32Array(N);
  for (let i = 0; i < N; i++) win[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / N);
  const Delta = Math.round(sr * 0.012);           // search tolerance ±12 ms
  const MF = 3 * N + Delta + 64;                  // margin (samples) on both sides of the mix
  const nT = Ys.length;
  // full-rate mix of all tracks, used only for the similarity search
  const Lm = MF + Ly + MF;
  const mix = new Float32Array(Lm);
  for (let t = 0; t < nT; t++){
    const Y = Ys[t], base = Os[t] + MF;
    const a = Math.max(0, -base), b = Math.min(Y.length, Lm - base);
    for (let j = a; j < b; j++) mix[base + j] += Y[j];
  }
  yield 0;
  // decimated (÷16) mix for the coarse search
  const Lz = (Lm >> 4) + 1;
  const z = new Float32Array(Lz);
  for (let i = 0; i < Lm; i++) z[i >> 4] += mix[i];
  const Nd = N >> 4;
  const Lout = outs[0].length;
  const K = Math.ceil(Lout / Hs) + 1;

  function ola(k, p){
    const m = k * Hs;
    for (let t = 0; t < nT; t++){
      const out = outs[t], Y = Ys[t], O = Os[t];
      const i0 = Math.max(0, -m, O - p);
      const i1 = Math.min(N, Lout - m, Y.length + O - p);
      const base = p - O;
      for (let i = i0; i < i1; i++) out[m + i] += win[i] * Y[base + i];
    }
  }

  let prev = Math.round(-Ha);
  ola(-1, prev);
  for (let k = 0; k < K; k++){
    const nom = Math.round(k * Ha);
    const tStart = prev + Hs;
    const tf = tStart + MF;
    const tz = tf >> 4;
    let Et = 0;
    for (let i = 0; i < Nd; i++){ const v = z[tz + i]; Et += v * v; }
    let p = nom;
    if (Et > 1e-9){
      const lo = (nom - Delta + MF) >> 4, hi = (nom + Delta + MF) >> 4;
      let E = 0;
      for (let i = 0; i < Nd; i++){ const v = z[lo + i]; E += v * v; }
      let best = lo, bestScore = -Infinity;
      for (let c = lo; c <= hi; c++){
        let s = 0;
        for (let i = 0; i < Nd; i++) s += z[tz + i] * z[c + i];
        const score = s / Math.sqrt(E + 1e-12);
        if (score > bestScore){ bestScore = score; best = c; }
        const a = z[c], b = z[c + Nd];
        E += b * b - a * a; if (E < 0) E = 0;
      }
      const center = best * 16 - MF + (tf & 15);
      let bs = -Infinity;
      const cLo = Math.max(center - 16, nom - Delta), cHi = Math.min(center + 16, nom + Delta);
      for (let c = cLo; c <= cHi; c++){
        const cf = c + MF;
        let s = 0, e = 0;
        for (let i = 0; i < N; i += 4){ const v = mix[cf + i]; s += mix[tf + i] * v; e += v * v; }
        const score = s / Math.sqrt(e + 1e-12);
        if (score > bs){ bs = score; p = c; }
      }
    }
    ola(k, p);
    prev = p;
    if ((k & 63) === 63) yield k / K;
  }
  yield 1;
}
