import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
# Menu ☰ (Ustawienia, Jak to działa), chowanie miksera, zwijana karta Pętla ze strzałkami,
# karta części w dwóch rzędach na iPhonie, przewijanie przy zablokowanej pętli.
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc: pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
def wheel(pg, wid, idx): pg.evaluate(f"document.getElementById('{wid}').scrollTop = {idx}*40"); pg.wait_for_timeout(350)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for vw, vh, tag in ((390, 844, 'phone'), (820, 1180, 'ipad')):
        c = b.new_context(viewport={'width':vw,'height':vh}, device_scale_factor=2, color_scheme='dark', has_touch=True)
        pg = c.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
        pg.goto(URL); pg.wait_for_timeout(1500)
        print(tag, 'menu hidden at start:', pg.is_hidden('#menuPanel'), '| settings at bottom gone:', pg.evaluate("document.getElementById('settings').closest('#menuPanel') !== null"))
        load(pg, 1, FIX + '/loud.wav'); pg.click('#addTrack'); load(pg, 2, FIX + '/quiet.wav')
        for part, cnt in ((1, 0), (0, 0)):
            pg.click('#seqStrip .step[data-step="add"]'); pg.wait_for_timeout(300); wheel(pg, 'wheelPart', part); wheel(pg, 'wheelCount', cnt); pg.click('#pkDone')
        top = pg.query_selector('.parts-top').bounding_box()['height']
        print(tag, 'parts top row height:', round(top), '(one row = 46)')
        bb = pg.query_selector('#wave').bounding_box()
        pg.mouse.move(bb['x']+40, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+150, bb['y']+60, steps=6); pg.mouse.up(); pg.wait_for_timeout(300)
        print(tag, 'loop card collapsed:', pg.evaluate("document.getElementById('loopCard').classList.contains('collapsed')"), '| summary:', pg.inner_text('#loopSummary'))
        pg.click('#loopToggle'); pg.wait_for_timeout(150)
        print(tag, 'nudges:', [e.inner_text() for e in pg.query_selector_all('[data-d]')])
        a0 = pg.inner_text('#tA'); pg.click('[data-d="0.1"]'); pg.wait_for_timeout(150); print(tag, 'A', a0, '-> (→ 0,1 s)', pg.inner_text('#tA'))
        pg.click('#menuBtn'); pg.wait_for_timeout(150); pg.click('#settings summary'); pg.wait_for_timeout(150)
        print(tag, 'menu open:', pg.is_visible('#menuPanel'), '| backup button visible:', pg.is_visible('#backupBtn'))
        pg.screenshot(path=f'{OUT}/layout_{tag}_menu.png', clip={'x':0,'y':0,'width':vw,'height':min(vh, 900)})
        pg.click('#sessBtn'); pg.wait_for_timeout(150); print(tag, 'sessions open closes menu:', pg.is_hidden('#menuPanel')); pg.click('#sessBtn')
        w0 = pg.query_selector('#wave').bounding_box()['width']; pg.click('#mixToggle'); pg.wait_for_timeout(400)
        print(tag, 'mixer hidden:', pg.is_hidden('#mixer'), '| wave width', round(w0), '->', round(pg.query_selector('#wave').bounding_box()['width']))
        pg.click('#seqCollapse'); pg.wait_for_timeout(150); print(tag, 'collapsed sequence summary:', pg.inner_text('#seqSum'))
        pg.click('#lock'); pg.wait_for_timeout(150)
        print(tag, 'locked canvas touch-action:', pg.evaluate("getComputedStyle(document.getElementById('wave')).touchAction"))
        bb = pg.query_selector('#wave').bounding_box(); pg.mouse.click(bb['x']+100, bb['y']+60); pg.wait_for_timeout(150)
        print(tag, 'tap on locked loop says:', pg.inner_text('#msg')[:30])
        pg.screenshot(path=f'{OUT}/layout_{tag}.png', full_page=True)
        pg.reload(); pg.wait_for_timeout(2500)
        print(tag, 'after reload: mixer hidden', pg.is_hidden('#mixer'), '| loop card open', not pg.evaluate("document.getElementById('loopCard').classList.contains('collapsed')"), '| sequence collapsed', pg.evaluate("document.getElementById('partsCard').classList.contains('collapsed')"))
        print(tag, 'ERRS', errs); c.close()
    b.close()
