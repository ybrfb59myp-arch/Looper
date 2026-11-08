import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc:
        pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1800)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for vw, vh, tag in ((820, 1180, 'ipad'), (390, 844, 'phone')):
        c = b.new_context(viewport={'width':vw,'height':vh}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
        pg = c.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
        pg.goto(URL); pg.wait_for_timeout(1500)
        load(pg, 1, FIX + '/test.wav')
        pg.click('#addTrack'); load(pg, 2, FIX + '/screen.mp4')
        strips = pg.query_selector_all('#mixer .strip[data-id]')
        print(tag, 'strips:', len(strips))
        f = pg.query_selector('#mixer .strip[data-id]:nth-child(2) .fader').bounding_box()
        pg.mouse.move(f['x']+15, f['y']+f['height']/2); pg.mouse.down(); pg.mouse.move(f['x']+15, f['y']+f['height']/2+25, steps=5); pg.mouse.up()
        print(tag, 'fader t2 ->', pg.get_attribute('#mixer .strip[data-id]:nth-child(2) .fader', 'aria-valuenow'), '| msg', pg.inner_text('#msg'))
        pg.click('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]'); pg.wait_for_timeout(100)
        print(tag, 'mute t1:', pg.get_attribute('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]', 'aria-pressed'), '| strip off:', pg.evaluate("document.querySelector('#mixer .strip[data-id]').classList.contains('off')"))
        pg.click('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]')
        pg.click('#mixer .strip[data-id]:nth-child(2) [data-ms=solo]'); pg.wait_for_timeout(100)
        print(tag, 'solo t2 -> t1 off:', pg.evaluate("document.querySelector('#mixer .strip[data-id]').classList.contains('off')"))
        pg.click('#play'); pg.wait_for_timeout(800); pg.click('#play')
        pg.click('#bounce'); pg.click('#bounceAll'); pg.wait_for_timeout(6000)
        print(tag, 'bounce:', pg.inner_text('#bounceTitle')); pg.click('#bounceClose')
        pg.wait_for_timeout(1200); pg.reload(); pg.wait_for_timeout(3500)
        print(tag, 'after reload solo t2:', pg.get_attribute('#mixer .strip[data-id]:nth-child(2) [data-ms=solo]', 'aria-pressed'), '| vol t2', pg.get_attribute('#mixer .strip[data-id]:nth-child(2) .fader', 'aria-valuenow'))
        pg.screenshot(path=f'{OUT}/mixer_{tag}.png', clip={'x':0,'y':0,'width':vw,'height':min(vh, 900)})
        print(tag, 'ERRS', errs)
        c.close()
    b.close()
