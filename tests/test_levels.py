import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
import subprocess, re
def load(pg, idx, path):
    with pg.expect_file_chooser() as fc:
        pg.click(f'.track:nth-child({idx}) [data-act=load]')
    fc.value.set_files(path); pg.wait_for_timeout(1500)
def mean_db(path):
    out = subprocess.run(['ffmpeg','-i',path,'-af','volumedetect','-f','null','-'],capture_output=True,text=True).stderr
    return re.search(r'mean_volume: (-?[\d.]+) dB', out).group(1)
def export(pg):
    pg.click('#bounce'); pg.click('#bounceAll'); pg.wait_for_timeout(5000)
    with pg.expect_download(timeout=5000) as dl: pg.click('#bounceShare')
    p = dl.value.path(); pg.click('#bounceClose'); return mean_db(p)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.goto(URL); pg.wait_for_timeout(1500)
    load(pg, 1, FIX + '/loud.wav'); pg.click('#addTrack'); load(pg, 2, FIX + '/quiet.wav')
    pg.click('#mixer .strip[data-id]:nth-child(2) [data-ms=mute]'); print('loud only:', export(pg))
    pg.click('#mixer .strip[data-id]:nth-child(2) [data-ms=mute]'); pg.click('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]'); print('quiet only:', export(pg))
    pg.click('#mixer .strip[data-id]:nth-child(1) [data-ms=mute]'); print('both:', export(pg))
    pg.screenshot(path=OUT + '/v5_phone.png', clip={'x':0,'y':0,'width':390,'height':844})
    print('ERRS', errs); b.close()
