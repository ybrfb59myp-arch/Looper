import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import subprocess, re, shutil
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc:
        pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
def dragloop(pg, x1, x2):
    bb = pg.query_selector('#wave').bounding_box()
    pg.mouse.move(bb['x']+x1, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+x2, bb['y']+60, steps=6); pg.mouse.up(); pg.wait_for_timeout(200)
def chips(pg): return [e.inner_text().replace('\n','') for e in pg.query_selector_all('#seqStrip .step')]
def cur(pg): return pg.evaluate("[...document.querySelectorAll('[data-part]')].find(b=>b.getAttribute('aria-pressed')==='true').dataset.part")
def wheel(pg, wid, idx):
    pg.evaluate(f"document.getElementById('{wid}').scrollTop = {idx}*40"); pg.wait_for_timeout(350)
def dur(path):
    return subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',path],capture_output=True,text=True).stdout.strip()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':820,'height':1180}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    print('start: part', cur(pg), '| chips', chips(pg))
    load(pg, 1, FIX + '/loud.wav'); dragloop(pg, 100, 200)
    print('A loop:', pg.inner_text('#tA'), pg.inner_text('#tB'))
    pg.click('[data-part=B]'); pg.wait_for_timeout(600)
    print('switched to', cur(pg), '| tracks:', [e.inner_text() for e in pg.query_selector_all('.trk-name')])
    load(pg, 1, FIX + '/screen.mp4'); dragloop(pg, 100, 300)
    print('B loop:', pg.inner_text('#tA'), pg.inner_text('#tB'))
    pg.click('[data-part=A]'); pg.wait_for_timeout(600)
    print('back to A: tracks', [e.inner_text() for e in pg.query_selector_all('.trk-name')], '| loop', pg.inner_text('#tA'), pg.inner_text('#tB'), '| B has dot:', pg.evaluate("document.querySelector('[data-part=B]').classList.contains('has')"))
    # edit sequence: A x1 -> A x2 ; add B x3 ; add C x1
    pg.click('#seqStrip .step[data-step="0"]'); pg.wait_for_timeout(300); wheel(pg, 'wheelCount', 1)
    print('after wheel:', chips(pg))
    pg.click('#seqStrip .step[data-step="add"]'); pg.wait_for_timeout(300); wheel(pg, 'wheelPart', 1); wheel(pg, 'wheelCount', 2)
    pg.click('#seqStrip .step[data-step="add"]'); pg.wait_for_timeout(300); wheel(pg, 'wheelPart', 2); wheel(pg, 'wheelCount', 0)
    pg.click('#pkDone')
    print('sequence:', chips(pg), '| C empty dimmed:', pg.evaluate("document.querySelector('#seqStrip .step[data-step=\"2\"]').classList.contains('empty')"))
    # move B left then back
    pg.click('#seqStrip .step[data-step="1"]'); pg.click('#pkLeft'); print('moved:', chips(pg)); pg.click('#pkRight'); pg.click('#pkDone')
    pg.click('[data-mode=seq]'); pg.wait_for_timeout(200)
    pg.click('#play'); pg.wait_for_timeout(700)
    pl = pg.evaluate("document.querySelector('#seqStrip .step.playing') && document.querySelector('#seqStrip .step.playing').innerText")
    print('seq playing chip:', repr(pl), '| part view:', cur(pg))
    pg.wait_for_timeout(4200)
    pl2 = pg.evaluate("document.querySelector('#seqStrip .step.playing') && document.querySelector('#seqStrip .step.playing').innerText")
    print('later chip:', repr(pl2), '| part view:', cur(pg), '| now', pg.inner_text('#now'))
    pg.click('#play'); pg.wait_for_timeout(200)
    print('paused, play icon label:', pg.get_attribute('#play','aria-label'))
    pg.click('#bounce'); pg.wait_for_timeout(200)
    print('bounce seq enabled:', pg.is_enabled('#bounceSeq'))
    pg.click('#bounceSeq'); pg.wait_for_timeout(9000)
    print('bounce title:', pg.inner_text('#bounceTitle'))
    with pg.expect_download(timeout=5000) as dl: pg.click('#bounceShare')
    path = dl.value.path(); print('seq mp3:', dl.value.suggested_filename, 'duration', dur(path))
    pg.click('#bounceClose')
    # expected duration
    print('expected:', pg.evaluate("(() => { const pl = seqPlanDebug(); return pl; })()") if False else '')
    pg.wait_for_timeout(1200)
    with pg.expect_download(timeout=8000) as dl2:
        pg.click('#sessBtn'); pg.click('#sessExport')
    sf = dl2.value.path(); shutil.copy(sf, FIX + '/parts.looper'); print('session file bytes', open(sf,'rb').read()[:8])
    pg.reload(); pg.wait_for_timeout(3500)
    print('after reload: part', cur(pg), '| chips', chips(pg), '| mode seq pressed:', pg.get_attribute('[data-mode=seq]','aria-pressed'), '| B dot', pg.evaluate("document.querySelector('[data-part=B]').classList.contains('has')"))
    with pg.expect_file_chooser() as fc:
        pg.click('#sessBtn'); pg.click('#sessImport')
    fc.value.set_files(FIX + '/parts.looper'); pg.wait_for_timeout(4000)
    print('imported:', pg.inner_text('#sessName'), '| chips', chips(pg), '| B dot', pg.evaluate("document.querySelector('[data-part=B]').classList.contains('has')"))
    pg.click('[data-part=B]'); pg.wait_for_timeout(600); print('imported B tracks:', [e.inner_text() for e in pg.query_selector_all('.trk-name')])
    pg.click('[data-part=A]'); pg.wait_for_timeout(600)
    pg.screenshot(path=OUT + '/v7_ipad.png', clip={'x':0,'y':0,'width':820,'height':1180})
    print('ERRS', errs)
    # migration from v3 single-part state
    c2 = b.new_context(viewport={'width':390,'height':844}); pg2 = c2.new_page(); pg2.goto(URL); pg2.wait_for_timeout(1500)
    pg2.evaluate("""() => new Promise((res) => { const r = indexedDB.open('petla-ab', 1); r.onsuccess = () => { const db = r.result; const tx = db.transaction('kv','readwrite'); const st = tx.objectStore('kv');
      st.clear();
      const pcm = new Int16Array(48000*3); for (let i=0;i<pcm.length;i++) pcm[i] = Math.round(8000*Math.sin(i/10));
      st.put({current:1,nextSid:2,list:[{sid:1,name:'Stara v3',created:1,updated:1,tracks:1}]}, 'sessions');
      st.put({kind:'pcm', sr:48000, name:'Nagranie v3', data: pcm.buffer}, 's1-data-3');
      st.put({v:3,nextId:4,tempoPct:0,semi:0,A:0.5,B:1.5,loopOn:true,locked:false,slots:[{id:3,name:'Nagranie v3',vol:1,trim:1,offset:0,has:true}]}, 's1-state');
      tx.oncomplete = () => res(true); }; })""")
    pg2.reload(); pg2.wait_for_timeout(3000)
    print('migrated v3:', pg2.inner_text('#sessName'), [e.inner_text() for e in pg2.query_selector_all('.trk-name')], '| part', cur(pg2), '| chips', chips(pg2), '| A', pg2.inner_text('#tA'))
    b.close()
