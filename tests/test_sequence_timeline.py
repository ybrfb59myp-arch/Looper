import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
def cur(pg): return pg.evaluate("[...document.querySelectorAll('[data-part]')].find(b=>b.getAttribute('aria-pressed')==='true').dataset.part")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':820,'height':1180}, device_scale_factor=2, color_scheme='dark')
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.goto(URL); pg.wait_for_timeout(1500)
    # the context is fresh -> make quick content: A and B
    def load(idx, path):
        with pg.expect_file_chooser() as fc: pg.click(f'.track:nth-child({idx}) [data-act=load]')
        fc.value.set_files(path); pg.wait_for_timeout(1500)
    def dragloop(x1, x2):
        bb = pg.query_selector('#wave').bounding_box()
        pg.mouse.move(bb['x']+x1, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+x2, bb['y']+60, steps=6); pg.mouse.up(); pg.wait_for_timeout(200)
    load(1, FIX + '/loud.wav'); dragloop(100, 160)
    pg.click('[data-part=B]'); pg.wait_for_timeout(500); load(1, FIX + '/screen.mp4'); dragloop(100, 200)
    pg.click('[data-part=A]'); pg.wait_for_timeout(500)
    pg.click('#seqStrip .step[data-step="add"]'); pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('wheelPart').scrollTop = 40"); pg.wait_for_timeout(350)
    pg.evaluate("document.getElementById('wheelCount').scrollTop = 0"); pg.wait_for_timeout(350); pg.click('#pkDone')
    print('seq:', [e.inner_text().replace('\n','') for e in pg.query_selector_all('#seqStrip .step')])
    pg.click('[data-mode=seq]'); pg.click('#play')
    seen = []
    for i in range(16):
        pg.wait_for_timeout(300)
        chip = pg.evaluate("(document.querySelector('#seqStrip .step.playing')||{}).innerText")
        seen.append((cur(pg), (chip or '').replace('\n','')))
    print('timeline:', seen)
    pg.screenshot(path=OUT + '/v7_seq.png', clip={'x':0,'y':0,'width':820,'height':1180})
    pg.click('#play')
    print('ERRS', errs); b.close()
