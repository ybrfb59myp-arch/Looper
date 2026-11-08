import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import shutil
INIT = """
(() => {
  const desc = Object.getOwnPropertyDescriptor(BaseAudioContext.prototype, 'currentTime');
  Object.defineProperty(BaseAudioContext.prototype, 'currentTime', { configurable: true, get(){ if (window.__freezeAll && !this.__fresh) return 5; return desc.get.call(this); } });
  const Orig = window.AudioContext;
  window.__ctxCount = 0;
  window.AudioContext = function(...a){ const c = new Orig(...a); window.__ctxCount++; if (window.__markFresh) c.__fresh = true; return c; };
  window.AudioContext.prototype = Orig.prototype;
})();
"""
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc: pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
def names(pg): return [e.inner_text() for e in pg.query_selector_all('.trk-name')]
def cur(pg): return pg.evaluate("[...document.querySelectorAll('[data-part]')].find(b=>b.getAttribute('aria-pressed')==='true').dataset.part")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':820,'height':1180}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    c.add_init_script(INIT)
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    print('fx collapsed by default:', pg.evaluate("document.getElementById('fxCard').classList.contains('collapsed')"), '| summary:', pg.inner_text('#fxSummary'))
    load(pg, 1, FIX + '/loud.wav')
    # 1) stuck engine -> watchdog
    pg.evaluate("window.__freezeAll = true; window.__markFresh = true;")
    n0 = pg.evaluate("window.__ctxCount")
    pg.click('#play'); pg.wait_for_timeout(1600)
    t1 = pg.inner_text('#now'); pg.wait_for_timeout(600); t2 = pg.inner_text('#now')
    print('watchdog: contexts', n0, '->', pg.evaluate("window.__ctxCount"), '| playhead moves:', t1, '->', t2, '| msg:', pg.inner_text('#msg')[:60])
    pg.click('#play'); pg.evaluate("window.__freezeAll = false")
    # 2) background -> return -> first tap makes a fresh engine
    pg.evaluate("""Object.defineProperty(document, 'hidden', {configurable:true, get(){return true}}); document.dispatchEvent(new Event('visibilitychange'));""")
    pg.wait_for_timeout(600)
    pg.evaluate("""Object.defineProperty(document, 'hidden', {configurable:true, get(){return false}}); document.dispatchEvent(new Event('visibilitychange'));""")
    n1 = pg.evaluate("window.__ctxCount")
    pg.click('#play'); pg.wait_for_timeout(900)
    a = pg.inner_text('#now'); pg.wait_for_timeout(500); bnow = pg.inner_text('#now')
    print('after return: contexts', n1, '->', pg.evaluate("window.__ctxCount"), '| playing:', a, '->', bnow)
    pg.click('#play')
    # 3) copy part A -> B
    pg.click('#partCopy'); pg.wait_for_timeout(200)
    print('copy row:', pg.inner_text('#copyLabel'), [e.inner_text() for e in pg.query_selector_all('[data-copyto]')])
    pg.click('[data-copyto=B]'); pg.wait_for_timeout(900)
    print('after copy: part', cur(pg), names(pg), '| B dot', pg.evaluate("document.querySelector('[data-part=B]').classList.contains('has')"))
    # copy again onto B needs confirm
    pg.click('[data-part=A]'); pg.wait_for_timeout(600); pg.click('#partCopy'); pg.click('[data-copyto=B]'); pg.wait_for_timeout(100)
    print('confirm label:', pg.inner_text('[data-copyto=B]')); pg.click('#copyCancel')
    # 4) tempo summary
    pg.click('#fxToggle'); pg.eval_on_selector('#tempo', "e=>{e.value=-12;e.dispatchEvent(new Event('input'));e.dispatchEvent(new Event('change'))}"); pg.wait_for_timeout(200)
    pg.click('#fxCollapse'); print('fx summary:', pg.inner_text('#fxSummary'), '| collapsed:', pg.evaluate("document.getElementById('fxCard').classList.contains('collapsed')"))
    pg.wait_for_timeout(2500)
    # 5) backup all sessions + restore
    pg.click('#sessBtn'); pg.click('#sessNew'); pg.wait_for_timeout(1200); load(pg, 1, FIX + '/quiet.wav'); pg.click('#sessBtn')
    pg.click('#menuBtn'); pg.click('#settings summary'); pg.wait_for_timeout(200)
    pg.click('#backupBtn'); pg.wait_for_timeout(2500)
    print('backup button:', pg.inner_text('#backupBtn'))
    with pg.expect_download(timeout=8000) as dl: pg.click('#backupBtn')
    bf = dl.value.path(); shutil.copy(bf, FIX + '/backup.looper'); print('backup magic:', open(bf,'rb').read(8), dl.value.suggested_filename)
    with pg.expect_file_chooser() as fc: pg.click('#restoreBtn')
    fc.value.set_files(FIX + '/backup.looper'); pg.wait_for_timeout(3500)
    print('restore msg:', pg.inner_text('#msg'))
    pg.click('#sessBtn'); pg.wait_for_timeout(200)
    print('sessions:', [e.inner_text() for e in pg.query_selector_all('.sess-info b')])
    r = pg.query_selector_all('.sess-row [data-sact=open]'); r[0].click(); pg.wait_for_timeout(3000)
    print('opened restored:', pg.inner_text('#sessName'), names(pg), '| B dot', pg.evaluate("document.querySelector('[data-part=B]').classList.contains('has')"))
    pg.screenshot(path=OUT + '/v8_ipad.png', clip={'x':0,'y':0,'width':820,'height':1180})
    print('ERRS', errs); b.close()
