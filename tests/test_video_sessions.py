import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import os
def names(pg): return [e.inner_text() for e in pg.query_selector_all('.trk-name')]
def drag(pg, x1, x2, y=60):
    b = pg.query_selector('#wave').bounding_box()
    pg.mouse.move(b['x']+x1, b['y']+y); pg.mouse.down(); pg.mouse.move(b['x']+x2, b['y']+y, steps=6); pg.mouse.up()
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc:
        pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1800)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    c.grant_permissions(['microphone'], origin='http://localhost:8765')
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    print('start:', pg.inner_text('#sessName'), names(pg), '| accept:', pg.get_attribute('#fileIn','accept')[:30])
    load(pg, 1, FIX + '/screen.mp4')
    print('video t1:', names(pg), pg.inner_text('#dur'), '|', pg.inner_text('#msg'))
    pg.click('#addTrack'); load(pg, 2, FIX + '/clip.mov')
    print('mov t2:', names(pg), pg.inner_text('#dur'))
    pg.click('#addTrack'); load(pg, 3, FIX + '/silent.mp4')
    print('silent t3:', names(pg), '| msg:', pg.inner_text('#msg'))
    drag(pg, 60, 200)
    print('loop:', pg.inner_text('#tA'), pg.inner_text('#tB'))
    pg.click('#lock'); pg.wait_for_timeout(100)
    drag(pg, 250, 320)
    print('locked -> loop unchanged:', pg.inner_text('#tA'), pg.inner_text('#tB'), '| tune disabled:', pg.is_disabled('[data-d="0.01"]'), '| clearLoop disabled:', pg.is_disabled('#clearLoop'), '| msg:', pg.inner_text('#msg')[:40])
    pg.click('#lock'); pg.wait_for_timeout(100)
    pg.click('.track:nth-child(2) [data-o="0.1"]'); pg.click('.track:nth-child(2) [data-o="-0.01"]'); pg.wait_for_timeout(600)
    print('t2 shift:', pg.inner_text('.track:nth-child(2) .off-out'))
    # record into track 3 with loop
    pg.click('.track:nth-child(3) [data-act=rec]'); pg.wait_for_timeout(7000)
    print('t3 rec:', names(pg), '| rec?', pg.evaluate("document.body.classList.contains('recording')"), '| off:', pg.inner_text('.track:nth-child(3) .off-out'))
    pg.click('.track:nth-child(3) [data-o="0.01"]'); pg.click('.track:nth-child(3) [data-o="0.01"]'); pg.wait_for_timeout(500)
    pg.click('#menuBtn'); pg.click('#settings summary'); pg.wait_for_timeout(100)
    print('learned:', pg.inner_text('#learnV'))
    # sessions
    pg.click('#sessBtn'); pg.wait_for_timeout(200)
    pg.click('#sessRename'); pg.fill('#renameIn', 'Solo test'); pg.click('#renameOk'); pg.wait_for_timeout(200)
    print('renamed:', pg.inner_text('#sessName'))
    pg.click('#sessNew'); pg.wait_for_timeout(1200)
    print('new session:', pg.inner_text('#sessName'), names(pg), '| list rows:', len(pg.query_selector_all('.sess-row')))
    pg.click('.sess-row [data-sact=open]'); pg.wait_for_timeout(3000)
    print('reopened:', pg.inner_text('#sessName'), names(pg), '| A', pg.inner_text('#tA'))
    pg.click('#sessCopy'); pg.wait_for_timeout(3000)
    print('copy:', pg.inner_text('#sessName'), names(pg), '| rows', len(pg.query_selector_all('.sess-row')))
    with pg.expect_download(timeout=8000) as dl:
        pg.click('#sessExport')
    sf = dl.value.path(); print('export:', dl.value.suggested_filename, os.path.getsize(sf), 'bytes')
    # delete the copy (current)
    cur = pg.query_selector('.sess-row:has(.sess-cur) [data-sact=del]'); cur.click(); pg.wait_for_timeout(100)
    pg.query_selector('.sess-row:has(.sess-cur) [data-sact=del]').click(); pg.wait_for_timeout(3000)
    print('after delete:', pg.inner_text('#sessName'), '| rows', len(pg.query_selector_all('.sess-row')))
    with pg.expect_file_chooser() as fc:
        pg.click('#sessImport')
    import shutil; shutil.copy(sf, FIX + '/test.looper'); fc.value.set_files(FIX + '/test.looper'); pg.wait_for_timeout(4000)
    print('imported:', pg.inner_text('#sessName'), names(pg), '| msg', pg.inner_text('#msg')[:60])
    pg.click('#sessBtn'); pg.wait_for_timeout(200)
    pg.click('#bounce'); pg.click('#bounceAll'); pg.wait_for_timeout(5000)
    print('bounce:', pg.inner_text('#bounceTitle'))
    pg.click('#bounceClose')
    pg.reload(); pg.wait_for_timeout(4000)
    print('after reload:', pg.inner_text('#sessName'), names(pg))
    pg.screenshot(path=OUT + '/v3_full.png', full_page=True)
    print('ERRS', errs)
    # migration from v2
    c2 = b.new_context(viewport={'width':390,'height':844}); pg2 = c2.new_page(); pg2.goto(URL); pg2.wait_for_timeout(1500)
    pg2.evaluate("""() => new Promise((res) => { const r = indexedDB.open('petla-ab', 1); r.onsuccess = () => { const db = r.result; const tx = db.transaction('kv','readwrite'); const st = tx.objectStore('kv');
      st.clear();
      const pcm = new Int16Array(48000*3); for (let i=0;i<pcm.length;i++) pcm[i] = Math.round(8000*Math.sin(i/10));
      st.put({kind:'pcm', sr:48000, name:'Nagranie 20.28', data: pcm.buffer}, 'data-5');
      st.put({kind:'pcm', sr:48000, name:'test', data: pcm.buffer.slice(0)}, 'data-6');
      st.put({v:2, nextId:7, tempoPct:-15, semi:0, A:0.5, B:1.5, loopOn:true, slots:[{id:5,name:'Nagranie 20.28',vol:1,offset:0,has:true},{id:6,name:'test',vol:0.8,offset:0.2,has:true}]}, 'state2');
      tx.oncomplete = () => res(true); }; })""")
    pg2.reload(); pg2.wait_for_timeout(3000)
    print('migrated v2:', pg2.inner_text('#sessName'), names(pg2), '| tempo', pg2.inner_text('#tempoV'), '| t2 off', pg2.inner_text('.track:nth-child(2) .off-out'))
    b.close()
