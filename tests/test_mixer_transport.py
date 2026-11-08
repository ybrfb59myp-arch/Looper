import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import subprocess, re
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc:
        pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
def mean_db(path):
    out = subprocess.run(['ffmpeg','-i',path,'-af','volumedetect','-f','null','-'],capture_output=True,text=True).stderr
    return re.search(r'mean_volume: (-?[\d.]+) dB', out).group(1)
def export(pg, tag):
    pg.click('#bounce'); pg.click('#bounceAll'); pg.wait_for_timeout(5000)
    with pg.expect_download(timeout=5000) as dl: pg.click('#bounceShare')
    p = dl.value.path(); pg.click('#bounceClose'); return mean_db(p)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    load(pg, 1, FIX + '/loud.wav'); pg.click('#addTrack'); load(pg, 2, FIX + '/quiet.wav')
    print('faders:', [e.get_attribute('aria-valuetext') for e in pg.query_selector_all('.fader')])
    pg.click('#mixer .strip[data-id]:nth-child(2) [data-ms=mute]'); print('loud only (export mean):', export(pg, 'a'))
    pg.click('#mixer .strip[data-id]:nth-child(2) [data-ms=mute]'); pg.click('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]')
    print('quiet only (export mean):', export(pg, 'b'))
    pg.click('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]')
    pg.query_selector('#mixer .strip[data-id]:nth-child(2) .fader').scroll_into_view_if_needed(); pg.wait_for_timeout(200)
    f = pg.query_selector('#mixer .strip[data-id]:nth-child(2) .fader').bounding_box()
    pg.mouse.move(f['x']+15, f['y']+f['height']*0.3); pg.mouse.down(); pg.mouse.move(f['x']+15, f['y']+f['height']*0.3+30, steps=5); pg.mouse.up()
    print('fader drag:', pg.inner_text('#msg'))
    # loop via drag on canvas, skip + start
    bb = pg.query_selector('#wave').bounding_box()
    pg.mouse.move(bb['x']+40, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+120, bb['y']+60, steps=6); pg.mouse.up()
    print('loop', pg.inner_text('#tA'), pg.inner_text('#tB'))
    pg.click('#toStart'); pg.wait_for_timeout(300); pg.click('#play')
    print('toStart paused at:', pg.inner_text('#now'))
    pg.click('[data-skip="10"]'); pg.wait_for_timeout(100); print('+10 in loop ->', pg.inner_text('#now'))
    pg.click('#loopToggle'); pg.click('#loop'); pg.click('[data-skip="5"]'); pg.wait_for_timeout(100); print('loop off, +5 ->', pg.inner_text('#now'))
    pg.click('[data-skip="-10"]'); pg.wait_for_timeout(100); print('-10 ->', pg.inner_text('#now'))
    pg.click('#lock'); pg.click('[data-skip="5"]'); pg.wait_for_timeout(100); print('locked, +5 ->', pg.inner_text('#now'), '| skip enabled:', pg.is_enabled('[data-skip="5"]'))
    pg.click('#lock')
    pg.screenshot(path=OUT + '/v5_phone.png', clip={'x':0,'y':0,'width':390,'height':844})
    # migracja starych suwaków (sprzed wyrównywania poziomów): vol 0.01/1.5 i brak trim w stanie, potem przeładowanie
    pg.wait_for_timeout(1200)
    pg.evaluate("""() => new Promise((res) => { const r = indexedDB.open('petla-ab', 1); r.onsuccess = () => { const db = r.result; const tx = db.transaction('kv','readwrite'); const st = tx.objectStore('kv');
      const g = st.get('sessions'); g.onsuccess = () => { const sid = g.result.current; const q = st.get('s'+sid+'-state'); q.onsuccess = () => { const s = q.result; const sl = (s.parts ? s.parts.A.slots : s.slots); sl[0].vol = 0.01; sl[1].vol = 1.5; sl.forEach(x => delete x.trim); st.put(s, 's'+sid+'-state'); }; };
      tx.oncomplete = () => res(true); tx.onabort = () => res(false); }; })""")
    pg.reload(); pg.wait_for_timeout(3000)
    print('after migration faders:', [e.get_attribute('aria-valuetext') for e in pg.query_selector_all('.fader')])
    print('ERRS', errs)
    b.close()
