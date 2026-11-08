import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
# Sekwencja na pauzie: pauza pokazuje miejsce, w którym zatrzymała się muzyka, a −10/−5/+5/+10
# przesuwają widok na właściwą część (kreska, czas, podświetlony klocek), tak jak podczas grania.
def cur(pg): return pg.evaluate("[...document.querySelectorAll('[data-part]')].find(b=>b.getAttribute('aria-pressed')==='true').dataset.part")
def chip(pg): return (pg.evaluate("(document.querySelector('#seqStrip .step.playing')||{}).innerText") or '').replace('\n', '')
def state(pg): return f"part {cur(pg)} | now {pg.inner_text('#now')} | chip {chip(pg)!r}"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, color_scheme='dark')
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    def load(idx, path):
        with pg.expect_file_chooser() as fc: pg.click(f'.track:nth-child({idx}) [data-act=load]')
        fc.value.set_files(path); pg.wait_for_timeout(1500)
    def setloop(a, b_):
        # pętla przez przeciągnięcie, potem dokładne wartości strzałkami nie są potrzebne: wypisujemy, co wyszło
        bb = pg.query_selector('#wave').bounding_box()
        pg.mouse.move(bb['x']+a, bb['y']+60); pg.mouse.down(); pg.mouse.move(bb['x']+b_, bb['y']+60, steps=6); pg.mouse.up(); pg.wait_for_timeout(200)
    load(1, FIX + '/loud.wav'); setloop(60, 160)
    la = (pg.inner_text('#tA'), pg.inner_text('#tB'))
    pg.click('[data-part=B]'); pg.wait_for_timeout(500); load(1, FIX + '/screen.mp4'); setloop(60, 200)
    lb = (pg.inner_text('#tA'), pg.inner_text('#tB'))
    pg.click('[data-part=A]'); pg.wait_for_timeout(500)
    pg.click('#seqStrip .step[data-step="add"]'); pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('wheelPart').scrollTop = 40"); pg.wait_for_timeout(350)
    pg.evaluate("document.getElementById('wheelCount').scrollTop = 0"); pg.wait_for_timeout(350); pg.click('#pkDone')
    print('loops: A', la, '| B', lb, '| seq', [e.inner_text().replace('\n','') for e in pg.query_selector_all('#seqStrip .step')])
    pg.click('[data-mode=seq]'); pg.wait_for_timeout(200)
    pg.click('#play'); pg.wait_for_timeout(1200)
    print('playing   :', state(pg))
    pg.click('#play'); pg.wait_for_timeout(300)
    print('paused    :', state(pg))
    for d in ['5', '5', '-10', '10', '-5']:
        pg.click(f'[data-skip="{d}"]'); pg.wait_for_timeout(300)
        print(f'paused {d:>3} :', state(pg))
    pg.click('#play'); pg.wait_for_timeout(400)
    print('play again:', state(pg))
    pg.click('#play'); pg.wait_for_timeout(200)
    pg.screenshot(path=OUT + '/seq_pause_phone.png')
    print('ERRS', errs); b.close()
