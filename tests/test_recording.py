import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
def names(pg): return [e.inner_text() for e in pg.query_selector_all('.trk-name')]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    c.grant_permissions(['microphone'], origin='http://localhost:8765')
    pg = c.new_page()
    errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    print('start:', names(pg), '| title', pg.title())
    pg.screenshot(path=OUT + '/v2_empty.png', full_page=False)
    # free recording into track 1
    pg.click('.track[data-id] [data-act=rec]'); pg.wait_for_timeout(2500)
    print('rec label:', pg.inner_text('.rec-active'), '| locked add:', pg.evaluate("getComputedStyle(document.getElementById('addTrack')).pointerEvents"))
    pg.click('.rec-active'); pg.wait_for_timeout(1500)
    print('after free rec:', names(pg), pg.inner_text('#msg')[:70])
    # add track 2 and load file
    pg.click('#addTrack'); pg.wait_for_timeout(200)
    with pg.expect_file_chooser() as fc:
        pg.click('.track:nth-child(2) [data-act=load]')
    fc.value.set_files(FIX + '/test.wav'); pg.wait_for_timeout(2000)
    print('after load t2:', names(pg), '| dur', pg.inner_text('#dur'))
    # pętla: przeciągnięcie palcem po przebiegu (przyciski „Ustaw A/B” zostały usunięte)
    pg.query_selector('#wave').scroll_into_view_if_needed(); bb = pg.query_selector('#wave').bounding_box()
    pg.mouse.move(bb['x']+60, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+110, bb['y']+60, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
    print('loop', pg.inner_text('#tA'), pg.inner_text('#tB'))
    # add track 3 and record with loop (auto stop)
    pg.click('#addTrack'); pg.wait_for_timeout(300)
    pg.click('.track:nth-child(3) [data-act=rec]'); pg.wait_for_timeout(6000)
    print('after loop rec:', names(pg), '| recording?', pg.evaluate("document.body.classList.contains('recording')"))
    # open details of track 3, check offset
    pg.click('.track:nth-child(3) [data-act=open]'); pg.wait_for_timeout(200)
    print('t3 offset:', pg.inner_text('.track:nth-child(3) .off-out'))
    # re-record track 1 needs confirm
    pg.click('.track:nth-child(1) [data-act=rec]'); pg.wait_for_timeout(200)
    print('confirm label:', pg.inner_text('.track:nth-child(1) .rec-label'))
    pg.click('.track:nth-child(1) [data-act=rec]'); pg.wait_for_timeout(1500)
    pg.click('.rec-active'); pg.wait_for_timeout(1500)
    print('re-recorded t1:', names(pg))
    # clear track 3 (two taps), then remove
    pg.click('.track:nth-child(3) [data-act=clear]'); pg.wait_for_timeout(100)
    print('clear armed:', pg.inner_text('.track:nth-child(3) [data-act=clear]'))
    pg.click('.track:nth-child(3) [data-act=clear]'); pg.wait_for_timeout(500)
    print('after clear:', names(pg))
    pg.click('.track:nth-child(3) [data-act=remove]'); pg.wait_for_timeout(500)
    print('after remove:', names(pg), '| add btn', pg.inner_text('#addTrack'))
    # tempo + bounce
    pg.eval_on_selector('#tempo', "e=>{e.value=-15;e.dispatchEvent(new Event('input'));e.dispatchEvent(new Event('change'))}")
    pg.wait_for_timeout(2500)
    pg.click('#bounce'); pg.wait_for_timeout(200)
    print('bounce sheet visible:', pg.is_visible('#bounceSheet'), '| loop option enabled:', pg.is_enabled('#bounceLoop'))
    pg.click('#bounceAll'); pg.wait_for_timeout(9000)
    print('bounce title:', pg.inner_text('#bounceTitle'))
    with pg.expect_download(timeout=5000) as dl:
        pg.click('#bounceShare')
    d = dl.value; path = d.path(); import os
    print('mp3:', d.suggested_filename, os.path.getsize(path), 'bytes', open(path,'rb').read(3))
    pg.click('#bounceClose')
    # save track WAV via details
    pg.click('.track:nth-child(2) [data-act=open]'); pg.wait_for_timeout(200)
    with pg.expect_download(timeout=5000) as dl2:
        pg.click('.track:nth-child(2) [data-act=save]')
    print('wav:', dl2.value.suggested_filename)
    pg.wait_for_timeout(1500)
    pg.reload(); pg.wait_for_timeout(3500)
    print('restored:', names(pg), '| tempo', pg.inner_text('#tempoV'), '| A', pg.inner_text('#tA'))
    c.set_offline(True); pg.reload(); pg.wait_for_timeout(3000)
    print('offline:', names(pg), '| badge', pg.is_visible('#net'))
    c.set_offline(False)
    pg.click('.track:nth-child(2) [data-act=open]'); pg.wait_for_timeout(300)
    pg.screenshot(path=OUT + '/v2_full.png', full_page=True)
    print(errs)
    # migration test in a fresh context: write v1 keys, then load
    c2 = b.new_context(viewport={'width':390,'height':844})
    pg2 = c2.new_page(); pg2.goto(URL); pg2.wait_for_timeout(1200)
    pg2.evaluate("""() => new Promise((res) => { const r = indexedDB.open('petla-ab', 1); r.onsuccess = () => { const db = r.result; const tx = db.transaction('kv','readwrite'); const st = tx.objectStore('kv');
      st.clear();   // jak u kogoś, kto miał tylko pierwszą wersję (bez listy sesji)
      const pcm = new Int16Array(48000*3); for (let i=0;i<pcm.length;i++) pcm[i] = Math.round(8000*Math.sin(i/10));
      st.put({kind:'pcm', sr:48000, name:'Stare nagranie', data: pcm.buffer}, 'track0');
      st.put({kind:'pcm', sr:48000, name:'Stary ślad 2', data: pcm.buffer.slice(0)}, 'track1');
      st.put({offset:0.5, tempoPct:-10, semi:2, A:0.5, B:1.5, loopOn:true, vols:[1,0.8]}, 'state');
      st.delete('state2'); tx.oncomplete = () => res(true); }; })""")
    pg2.reload(); pg2.wait_for_timeout(2500)
    print('migrated:', names(pg2), '| tempo', pg2.text_content('#tempoV'), '| semi', pg2.text_content('#semiV'), '| A', pg2.inner_text('#tA'))
    b.close()
