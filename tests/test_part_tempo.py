import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import subprocess
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc: pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
def cur(pg): return pg.evaluate("[...document.querySelectorAll('[data-part]')].find(b=>b.getAttribute('aria-pressed')==='true').dataset.part")
def fx(pg): return pg.evaluate("[document.getElementById('fxPart').textContent, +document.getElementById('tempo').value, +document.getElementById('semi').value, document.getElementById('fxSummary').textContent].join(' | ')")
def wheel(pg, wid, idx): pg.evaluate(f"document.getElementById('{wid}').scrollTop = {idx}*40"); pg.wait_for_timeout(350)
def chips(pg): return [e.inner_text().replace('\n','') for e in pg.query_selector_all('#seqStrip .step')]
def dur(path): return subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',path],capture_output=True,text=True).stdout.strip()
def settempo(pg, v): pg.eval_on_selector('#tempo', f"e=>{{e.value={v};e.dispatchEvent(new Event('input'));e.dispatchEvent(new Event('change'))}}")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=3, color_scheme='dark', accept_downloads=True)
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    load(pg, 1, FIX + '/loud.wav')
    pg.click('#fxToggle'); settempo(pg, -20); pg.wait_for_timeout(2500)
    print('A:', fx(pg))
    pg.click('[data-part=B]'); pg.wait_for_timeout(600); print('B (new):', fx(pg))
    load(pg, 1, FIX + '/quiet.wav'); pg.click('#semiPlus'); pg.click('#semiPlus'); pg.wait_for_timeout(3000)
    print('B:', fx(pg))
    pg.click('[data-part=A]'); pg.wait_for_timeout(800); print('back to A:', fx(pg))
    # sequence A x1, B x1
    pg.click('#seqStrip .step[data-step="add"]'); pg.wait_for_timeout(300); wheel(pg, 'wheelPart', 1); wheel(pg, 'wheelCount', 0); pg.click('#pkDone')
    print('sequence:', chips(pg))
    pg.click('[data-mode=seq]'); pg.wait_for_timeout(200); pg.click('#play'); pg.wait_for_timeout(1500)
    print('seq t=1.5s:', cur(pg), '|', fx(pg))
    pg.click('#tempoPlus'); pg.wait_for_timeout(2500)   # A now -19 while the sequence plays
    print('after tempo+ during seq:', cur(pg), '|', fx(pg), '| still playing:', pg.get_attribute('#play','aria-label'))
    pg.wait_for_timeout(14500)
    print('seq later:', cur(pg), '|', fx(pg))
    pg.click('#play'); pg.wait_for_timeout(300)
    pg.click('#bounce'); pg.wait_for_timeout(200); pg.click('#bounceSeq'); pg.wait_for_timeout(12000)
    with pg.expect_download(timeout=8000) as dl: pg.click('#bounceShare')
    print('seq mp3:', dl.value.suggested_filename, '| duration', dur(dl.value.path()), '| expected', round(12/0.81 + 12, 2))
    pg.click('#bounceClose')
    pg.click('[data-mode=part]'); pg.wait_for_timeout(300)
    pg.click('[data-part=B]'); pg.wait_for_timeout(600)
    pg.click('#bounce'); pg.wait_for_timeout(200); pg.click('#bounceAll'); pg.wait_for_timeout(6000)
    with pg.expect_download(timeout=8000) as dl: pg.click('#bounceShare')
    print('B mp3:', dl.value.suggested_filename, '| duration', dur(dl.value.path()))
    pg.click('#bounceClose')
    pg.wait_for_timeout(1200)
    pg.reload(); pg.wait_for_timeout(3500)
    print('after reload:', cur(pg), '|', fx(pg)); pg.click('[data-part=A]'); pg.wait_for_timeout(700); print('after reload A:', fx(pg))
    # copy A -> C
    pg.click('#partCopy'); pg.click('[data-copyto=C]'); pg.wait_for_timeout(900)
    print('copied to C:', cur(pg), '|', fx(pg))
    pg.screenshot(path=OUT + '/v9_iphone.png', clip={'x':0,'y':0,'width':390,'height':844})
    # stara kopia zapasowa (jedno tempo dla całej sesji): zob. test_legacy_backup.py
    print('ERRS', errs); b.close()
