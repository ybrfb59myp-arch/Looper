// Encodes a mono Float32 mix to MP3 off the main thread (LAME via lamejs, LGPL — see lame.LICENSE.txt).
importScripts('lame.min.js');
onmessage = (e) => {
  try {
    const { pcm, sr, kbps } = e.data;
    const enc = new lamejs.Mp3Encoder(1, sr, kbps || 128);
    const N = pcm.length, block = 1152 * 16, parts = [];
    const i16 = new Int16Array(block);
    let step = 0;
    for (let i = 0; i < N; i += block){
      const len = Math.min(block, N - i);
      for (let j = 0; j < len; j++){
        let s = pcm[i + j];
        s = s < -1 ? -1 : s > 1 ? 1 : s;
        i16[j] = s < 0 ? s * 32768 : s * 32767;
      }
      const out = enc.encodeBuffer(len === block ? i16 : i16.subarray(0, len));
      if (out.length) parts.push(new Uint8Array(out.buffer, out.byteOffset, out.length).slice());
      if ((step++ % 16) === 0) postMessage({ progress: i / N });
    }
    const end = enc.flush();
    if (end.length) parts.push(new Uint8Array(end.buffer, end.byteOffset, end.length).slice());
    postMessage({ done: true, blob: new Blob(parts, { type: 'audio/mpeg' }) });
  } catch (err) {
    postMessage({ error: String(err && err.message || err) });
  }
};
