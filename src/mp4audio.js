/* ---------- video (MP4 / MOV) → AAC audio as ADTS, so decodeAudioData can read it ---------- */
function mp4AacToAdts(ab){
  const u8 = new Uint8Array(ab), dv = new DataView(ab);
  const fourcc = (p) => String.fromCharCode(u8[p], u8[p + 1], u8[p + 2], u8[p + 3]);
  function boxes(start, end){
    const out = [];
    let p = start;
    while (p + 8 <= end){
      let size = dv.getUint32(p), hdr = 8;
      const type = fourcc(p + 4);
      if (size === 1){ size = Number(dv.getBigUint64(p + 8)); hdr = 16; }
      else if (size === 0) size = end - p;
      if (size < hdr || p + size > end) break;
      out.push({ type, start: p, body: p + hdr, end: p + size });
      p += size;
    }
    return out;
  }
  const find = (list, type) => list.find((b) => b.type === type);
  const kids = (b) => boxes(b.body, b.end);

  function parseEsds(p){
    const readLen = () => { let len = 0; for (let i = 0; i < 4; i++){ const b = u8[p++]; len = (len << 7) | (b & 0x7f); if (!(b & 0x80)) break; } return len; };
    if (u8[p++] !== 0x03) throw new Error('esds');
    readLen(); p += 2;
    const flags = u8[p++];
    if (flags & 0x80) p += 2;
    if (flags & 0x40) p += 1 + u8[p];
    if (flags & 0x20) p += 2;
    if (u8[p++] !== 0x04) throw new Error('esds/dcd');
    readLen(); p += 13;
    if (u8[p++] !== 0x05) throw new Error('esds/dsi');
    readLen();
    const b0 = u8[p], b1 = u8[p + 1];
    let aot = b0 >> 3;
    const sfi = ((b0 & 7) << 1) | (b1 >> 7);
    const ch = (b1 >> 3) & 15;
    if (aot === 31 || sfi === 15) throw new Error('unsupported AAC config');
    if (aot === 5 || aot === 29) aot = 2;
    return { aot, sfi, ch };
  }

  const moov = find(boxes(0, u8.length), 'moov');
  if (!moov) throw new Error('no moov');
  for (const trak of kids(moov).filter((b) => b.type === 'trak')){
    const mdia = find(kids(trak), 'mdia'); if (!mdia) continue;
    const mk = kids(mdia);
    const hdlr = find(mk, 'hdlr'); if (!hdlr) continue;
    if (fourcc(hdlr.body + 8) !== 'soun') continue;
    const minf = find(mk, 'minf'); if (!minf) continue;
    const stbl = find(kids(minf), 'stbl'); if (!stbl) continue;
    const st = kids(stbl);
    const stsd = find(st, 'stsd');
    const entry = stsd && boxes(stsd.body + 8, stsd.end)[0];
    if (!entry || entry.type !== 'mp4a') throw new Error('audio is not AAC (' + (entry ? entry.type : '?') + ')');
    const ver = dv.getUint16(entry.body + 8);
    let childStart = entry.body + 28 + (ver === 1 ? 16 : ver === 2 ? 36 : 0);
    let esds = null;
    (function search(s, e){
      for (const b of boxes(s, e)){
        if (b.type === 'esds'){ esds = b; return; }
        if (b.type === 'wave') search(b.body, b.end);
        if (esds) return;
      }
    })(childStart, entry.end);
    if (!esds) throw new Error('no esds');
    const cfg = parseEsds(esds.body + 4);

    const stsz = find(st, 'stsz');
    const fixed = dv.getUint32(stsz.body + 4), count = dv.getUint32(stsz.body + 8);
    const sizes = new Uint32Array(count);
    for (let i = 0; i < count; i++) sizes[i] = fixed || dv.getUint32(stsz.body + 12 + i * 4);

    const stco = find(st, 'stco'), co64 = find(st, 'co64');
    let offsets;
    if (stco){ const n = dv.getUint32(stco.body + 4); offsets = new Float64Array(n); for (let i = 0; i < n; i++) offsets[i] = dv.getUint32(stco.body + 8 + i * 4); }
    else if (co64){ const n = dv.getUint32(co64.body + 4); offsets = new Float64Array(n); for (let i = 0; i < n; i++) offsets[i] = Number(dv.getBigUint64(co64.body + 8 + i * 8)); }
    else throw new Error('no chunk offsets');

    const stsc = find(st, 'stsc');
    const ne = dv.getUint32(stsc.body + 4), ents = [];
    for (let i = 0; i < ne; i++) ents.push([dv.getUint32(stsc.body + 8 + i * 12), dv.getUint32(stsc.body + 12 + i * 12)]);

    let total = 0;
    for (let i = 0; i < count; i++) total += sizes[i] + 7;
    const out = new Uint8Array(total);
    let w = 0, si = 0, e = 0;
    const profile = cfg.aot - 1;
    for (let c = 0; c < offsets.length && si < count; c++){
      while (e + 1 < ents.length && ents[e + 1][0] <= c + 1) e++;
      const spc = ents[e][1];
      let off = offsets[c];
      for (let k = 0; k < spc && si < count; k++, si++){
        const sz = sizes[si], len = sz + 7;
        if (off + sz > u8.length) { si = count; break; }
        out[w] = 0xFF; out[w + 1] = 0xF1;
        out[w + 2] = ((profile & 3) << 6) | ((cfg.sfi & 15) << 2) | ((cfg.ch >> 2) & 1);
        out[w + 3] = ((cfg.ch & 3) << 6) | ((len >> 11) & 3);
        out[w + 4] = (len >> 3) & 0xFF;
        out[w + 5] = ((len & 7) << 5) | 0x1F;
        out[w + 6] = 0xFC;
        out.set(u8.subarray(off, off + sz), w + 7);
        w += len; off += sz;
      }
    }
    return out.slice(0, w).buffer;
  }
  throw new Error('no audio track');
}
