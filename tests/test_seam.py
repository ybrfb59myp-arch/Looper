import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import base64, math, struct, subprocess, wave
import numpy as np
# Lupa przejścia (karta Pętla): suwak 0–5 s; gra końcówkę pętli (B−h…B), przejście B→A i początek (A…A+h)
# w kółko, bez ciszy. Sprawdzamy: wygląd, wartości suwaka, pozycję na ekranie i prawdziwy dźwięk
# (nagrywany z wyjścia aplikacji: sygnał testowy to „glissando”, którego wysokość mówi, które miejsce gra).
SR = 48000
CHIRP = '/tmp/looper-chirp.wav'
F0, K = 300.0, 60.0                     # częstotliwość = F0 + K * czas_w_nagraniu
if not os.path.exists(CHIRP):
    n = SR * 10
    ph, out = 0.0, []
    for i in range(n):
        ph += 2 * math.pi * (F0 + K * i / SR) / SR
        out.append(int(9000 * math.sin(ph)))
    with wave.open(CHIRP, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(struct.pack('<%dh' % n, *out))

TAP = """
(() => {
  const C = window.AudioContext || window.webkitAudioContext;
  const orig = AudioNode.prototype.connect;
  window.__starts = [];
  AudioNode.prototype.connect = function (dest, ...rest) {
    const r = orig.call(this, dest, ...rest);
    if (dest instanceof AudioDestinationNode && !this.context.__tap) {
      const md = this.context.createMediaStreamDestination();
      this.context.__tap = md;
      const rec = new MediaRecorder(md.stream);
      window.__chunks = []; window.__rec = rec;
      rec.ondataavailable = (e) => window.__chunks.push(e.data);
      rec.start();
    }
    if (dest instanceof AudioDestinationNode) orig.call(this, this.context.__tap);
    return r;
  };
  const st = AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start = function (when, off, dur) {
    window.__starts.push({ when, off, loop: this.loop, ls: this.loopStart, le: this.loopEnd, now: this.context.currentTime });
    return st.call(this, when, off, dur);
  };
})();
"""
def secs(t):
    m, rest = t.split(':'); return int(m) * 60 + float(rest.replace(',', '.'))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for (w, h, tag) in [(390, 844, 'phone'), (820, 1180, 'pad')]:
        c = b.new_context(viewport={'width':w,'height':h}, device_scale_factor=2, color_scheme='dark')
        c.add_init_script(TAP)
        pg = c.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
        pg.goto(URL); pg.wait_for_timeout(1200)
        with pg.expect_file_chooser() as fc: pg.click('.track:nth-child(1) [data-act=load]')
        fc.value.set_files(CHIRP); pg.wait_for_timeout(1500)
        if pg.get_attribute('#loopToggle', 'aria-expanded') != 'true': pg.click('#loopToggle')
        print(tag, 'no loop -> seam disabled:', pg.get_attribute('#seam', 'aria-disabled'))
        bb = pg.query_selector('#wave').bounding_box()
        x1, x2 = (60, 230) if tag == 'phone' else (100, 500)
        pg.mouse.move(bb['x']+x1, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+x2, bb['y']+60, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
        A, B = secs(pg.inner_text('#tA')), secs(pg.inner_text('#tB'))
        sb = pg.query_selector('#seam').bounding_box()
        print(tag, f'loop {A:.2f}-{B:.2f} | seam enabled: {pg.get_attribute("#seam", "aria-disabled") == "false"} | pill {sb["width"]:.0f}x{sb["height"]:.0f}')
        # przesuń trochę: wartość rośnie łagodnie; skrajnie w prawo = 5 s; skrajnie w lewo = wyłączona
        def drag(dx):
            pg.query_selector('#seam').scroll_into_view_if_needed()
            sb = pg.query_selector('#seam').bounding_box(); cy = sb['y'] + sb['height'] / 2
            pg.mouse.move(sb['x'] + 30, cy); pg.mouse.down(); pg.mouse.move(sb['x'] + 30 + dx, cy, steps=8); pg.mouse.up(); pg.wait_for_timeout(150)
            return pg.get_attribute('#seam', 'aria-valuetext')
        print(tag, 'small drag +10px:', drag(10), '| +400px:', drag(400), '| -1000px:', drag(-1000), '| summary', repr(pg.inner_text('#loopSummary')))
        print(tag, 'set ~2 s:', drag(80), '| summary', repr(pg.inner_text('#loopSummary')))
        hh = float(pg.get_attribute('#seam', 'aria-valuenow')) / 2
        pg.query_selector('#loopCard').screenshot(path=f'{OUT}/seam_card_{tag}.png')
        # granie z lupą: pozycje na ekranie muszą być w oknach [B−h, B] i [A, A+h]
        pg.evaluate('window.__starts.length = 0')
        pg.click('#play'); pos = []
        for i in range(70):
            pg.wait_for_timeout(50); pos.append(secs(pg.inner_text('#now')))
        pg.click('#play'); pg.wait_for_timeout(200)
        inwin = [(B - hh - 0.06 <= t <= B + 0.02) or (A - 0.02 <= t <= A + hh + 0.06) for t in pos]
        print(tag, f'h={hh:.2f}s | positions in windows: {sum(inwin)}/{len(pos)} | min {min(pos):.2f} max {max(pos):.2f}')
        st = pg.evaluate('window.__starts')
        reps = sorted({round(s['when'], 4) for s in st})
        gaps = [round(y - x, 4) for x, y in zip(reps, reps[1:])]
        print(tag, 'sources: loop', {(s['loop'], round(s['ls'], 3), round(s['le'], 3)) for s in st}, '| offsets', sorted({round(s['off'], 3) for s in st}), '| gaps', sorted(set(gaps)))
        # ten sam podgląd bez lupy: zwykła pętla ma te same punkty loopStart/loopEnd
        drag(-1000); pg.evaluate('window.__starts.length = 0'); pg.click('#play'); pg.wait_for_timeout(400); pg.click('#play')
        st2 = pg.evaluate('window.__starts')
        print(tag, 'normal loop sources:', {(s['loop'], round(s['ls'], 3), round(s['le'], 3)) for s in st2}, '| summary', repr(pg.inner_text('#loopSummary')))
        # kłódka w trakcie grania z lupą: karta się zwija, lupa wyłącza, gra cała pętla; otwarcie kłódki rozwija kartę
        drag(80); pg.click('#play'); pg.wait_for_timeout(600)
        pg.click('#lock'); pg.wait_for_timeout(200)
        lp = []
        for i in range(30):
            pg.wait_for_timeout(100); lp.append(secs(pg.inner_text('#now')))
        pg.click('#play'); pg.wait_for_timeout(150)
        outside = sum(1 for t in lp if A + hh + 0.1 < t < B - hh - 0.1)
        print(tag, 'locked: card folded', pg.evaluate("document.getElementById('loopCard').classList.contains('collapsed')"), '| seam', pg.get_attribute('#seam', 'aria-valuetext'),
              '| summary', repr(pg.inner_text('#loopSummary')), '| positions outside seam windows', outside, '/', len(lp))
        pg.click('#lock'); pg.wait_for_timeout(200)
        print(tag, 'unlocked: card open', not pg.evaluate("document.getElementById('loopCard').classList.contains('collapsed')"))
        # prawdziwy dźwięk: lupa ~2 s, nagranie wyjścia, odczyt wysokości -> miejsce w nagraniu
        drag(80); pg.wait_for_timeout(100)
        pg.evaluate("() => new Promise((res) => { const r = window.__rec; r.onstop = () => { const n = new MediaRecorder(r.stream); window.__chunks = []; n.ondataavailable = (e) => window.__chunks.push(e.data); window.__rec = n; n.start(); res(); }; r.stop(); })")
        pg.click('#play'); pg.wait_for_timeout(5000); pg.click('#play'); pg.wait_for_timeout(300)
        data = pg.evaluate("""() => new Promise((res) => { window.__rec.onstop = async () => { const bl = new Blob(window.__chunks); const buf = new Uint8Array(await bl.arrayBuffer()); let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000)); res(btoa(s)); }; window.__rec.stop(); })""")
        open(f'/tmp/seam_out_{tag}.webm', 'wb').write(base64.b64decode(data))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'/tmp/seam_out_{tag}.webm', '-ac', '1', '-ar', '48000', f'/tmp/seam_out_{tag}.wav'], check=True)
        with wave.open(f'/tmp/seam_out_{tag}.wav') as wf:
            x = np.frombuffer(wf.readframes(wf.getnframes()), dtype='<i2').astype(float)
        win, hop = 2048, 480
        est = []
        for i in range(0, len(x) - win, hop):
            seg = x[i:i + win]
            if np.sqrt(np.mean(seg ** 2)) < 300: est.append(None); continue
            sp = np.abs(np.fft.rfft(seg * np.hanning(win), 8 * win))
            f = np.argmax(sp) * SR / (8 * win)
            est.append((f - F0) / K)
        tl = [e for e in est if e is not None]
        ok = [(B - hh - 0.08 <= t <= B + 0.05) or (A - 0.05 <= t <= A + hh + 0.08) for t in tl]
        jumps_ba = sum(1 for u, v in zip(tl, tl[1:]) if u > B - 0.2 and v < A + 0.2)
        jumps_ab = sum(1 for u, v in zip(tl, tl[1:]) if u < A + hh + 0.2 and u > A and v > B - hh - 0.2)
        silent = sum(1 for e in est[len(est)//10: -len(est)//10] if e is None)
        print(tag, f'audio: {len(tl)} windows, in seam windows {sum(ok)}/{len(tl)}, B→A joins {jumps_ba}, back-jumps {jumps_ab}, silent windows mid-play {silent}')
        print(tag, 'ERRS', errs)
        c.close()
    b.close()
