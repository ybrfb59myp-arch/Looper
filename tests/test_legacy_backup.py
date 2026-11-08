import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
# Kopia ze starej wersji miała jedno tempo (−12%) dla całej sesji: po wczytaniu każda część ma mieć −12%.
def fx(pg): return pg.evaluate("[document.getElementById('fxPart').textContent, +document.getElementById('tempo').value, +document.getElementById('semi').value, document.getElementById('fxSummary').textContent].join(' | ')")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':390,'height':844}); pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.goto(URL); pg.wait_for_timeout(1500)
    pg.click('#menuBtn'); pg.click('#settings summary'); pg.wait_for_timeout(200)
    with pg.expect_file_chooser() as fc: pg.click('#restoreBtn')
    fc.value.set_files(FIX + '/legacy-backup.looper'); pg.wait_for_timeout(3500)
    pg.click('#sessBtn'); pg.wait_for_timeout(200)
    for r in pg.query_selector_all('.sess-row'):
        t = r.inner_text()
        if 'Stara sesja' in t: r.query_selector('[data-sact=open]').click(); break
    pg.wait_for_timeout(3000)
    print('old session:', pg.inner_text('#sessName'), '| A', fx(pg))
    pg.click('[data-part=B]'); pg.wait_for_timeout(1500); print('B', fx(pg), '| tracks', [e.inner_text() for e in pg.query_selector_all('.trk-name')])
    pg.click('[data-part=C]'); pg.wait_for_timeout(700); print('C', fx(pg))
    print('ERRS', errs); b.close()
