import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc:
        pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
    c = b.new_context(viewport={'width':820,'height':1180}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    c.grant_permissions(['microphone'], origin='http://localhost:8765')
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    load(pg, 1, FIX + '/loud.wav')
    for i in range(5): pg.click('#addTrack')
    print('tracks:', len(pg.query_selector_all('.track')), '| count label:', pg.inner_text('#trkCount'), '| add enabled:', pg.is_enabled('#addTrack'))
    load(pg, 2, FIX + '/quiet.wav')
    print('user-select body:', pg.evaluate("getComputedStyle(document.body).webkitUserSelect || getComputedStyle(document.body).userSelect"))
    # drag strip area left of the fader (on empty space between M/S and fader? use strip top edge area)
    pg.query_selector('#mixer .strip[data-id]:nth-child(2)').scroll_into_view_if_needed(); pg.wait_for_timeout(200)
    st = pg.query_selector('#mixer .strip[data-id]:nth-child(2)').bounding_box()
    x = st['x'] + st['width'] - 40; y = st['y'] + st['height'] - 6
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x, y - 30, steps=5)
    print('bubble visible during drag:', pg.evaluate("getComputedStyle(document.querySelector('#mixer .strip.dragging .bubble')).opacity"), '| text:', pg.inner_text('#mixer .strip.dragging .bubble'))
    pg.mouse.up()
    print('after drag dragging class:', len(pg.query_selector_all('#mixer .strip.dragging')))
    # collapse
    pg.click('#trkCollapse'); pg.wait_for_timeout(200)
    print('collapsed:', pg.evaluate("document.getElementById('tracks').classList.contains('collapsed')"), '| dots:', len(pg.query_selector_all('.recdot')), '| mini visible:', pg.is_visible('#addTrackMini'), pg.is_visible('#bounceMini'))
    # record via dot into track 3 (empty) -> backing plays
    pg.query_selector_all('.recdot')[2].click(); pg.wait_for_timeout(2500)
    print('recording via dot:', pg.evaluate("document.body.classList.contains('recording')"), '| active dot:', len(pg.query_selector_all('.recdot.rec-active')))
    pg.query_selector('.recdot.rec-active').click(); pg.wait_for_timeout(1500)
    pg.click('#trkToggle'); pg.wait_for_timeout(200)
    print('names:', [e.inner_text() for e in pg.query_selector_all('.trk-name')][:4])
    pg.click('#trkCollapse'); pg.wait_for_timeout(200)
    # armed confirm on dot of track 1
    pg.query_selector_all('.recdot')[0].click(); pg.wait_for_timeout(150)
    print('dot armed:', len(pg.query_selector_all('.recdot.armed')), '| msg:', pg.inner_text('#msg'))
    pg.wait_for_timeout(4300)
    pg.reload(); pg.wait_for_timeout(3000)
    print('after reload collapsed:', pg.evaluate("document.getElementById('tracks').classList.contains('collapsed')"), '| tracks', pg.inner_text('#trkCount'))
    pg.screenshot(path=OUT + '/v6_ipad.png', clip={'x':0,'y':0,'width':820,'height':1180})
    print('ERRS', errs); b.close()
