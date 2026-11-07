// Captures microphone input in chunks stamped with the AudioContext frame they were recorded at,
// so the main thread can place the take exactly on the timeline.
class RecProc extends AudioWorkletProcessor {
  constructor(){
    super();
    this.on = false;
    this.size = 4096;
    this.buf = new Float32Array(this.size);
    this.n = 0;
    this.f0 = 0;
    this.expected = -1;
    this.port.onmessage = (e) => {
      if (e.data === 'start'){ this.on = true; this.n = 0; this.expected = -1; }
      else if (e.data === 'stop'){ this.flush(); this.on = false; this.port.postMessage({ done: true }); }
    };
  }
  flush(){
    if (this.n > 0){
      const d = this.buf.slice(0, this.n);
      this.port.postMessage({ frame: this.f0, data: d }, [d.buffer]);
      this.n = 0;
    }
  }
  process(inputs){
    if (!this.on) return true;
    const inp = inputs[0];
    const ch0 = inp && inp[0];
    if (!ch0) return true;
    if (this.n > 0 && currentFrame !== this.expected) this.flush();
    const L = ch0.length, nc = inp.length;
    for (let i = 0; i < L; i++){
      if (this.n === 0) this.f0 = currentFrame + i;
      let v = 0;
      for (let c = 0; c < nc; c++) v += inp[c][i];
      this.buf[this.n++] = v / nc;
      if (this.n === this.size) this.flush();
    }
    this.expected = currentFrame + L;
    return true;
  }
}
registerProcessor('rec-proc', RecProc);
