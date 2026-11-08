import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import URL, FIX, OUT, CHROME
from playwright.sync_api import sync_playwright
# Przypomnienia o kopiach: pasek po wyjściu z sesji ze zmianami (i przy starcie, gdy otwarta sesja ma zmiany
# bez kopii), „Nie teraz”, pełna kopia co 7 dni („Później”), data ostatniej pełnej kopii w Ustawieniach,
# stare sesje bez zapisanej historii kopii, plik kopii sesji da się otworzyć.
EDIT_IDX = """(fn) => new Promise((res) => { const r = indexedDB.open('petla-ab', 1); r.onsuccess = () => { const db = r.result;
  const tx = db.transaction('kv', 'readwrite'); const st = tx.objectStore('kv'); const g = st.get('sessions');
  g.onsuccess = () => { const s = g.result; (new Function('s', fn))(s); st.put(s, 'sessions'); };
  tx.oncomplete = () => res(true); }; })"""
def bar(pg):
    return pg.inner_text('#bkText') if pg.is_visible('#bkBar') else None
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    c = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, color_scheme='dark', accept_downloads=True)
    pg = c.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE '+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    print('start, empty session:', bar(pg))
    with pg.expect_file_chooser() as fc: pg.click('.track:nth-child(1) [data-act=load]')
    fc.value.set_files(FIX + '/test.wav'); pg.wait_for_timeout(1500)
    pg.click('#sessBtn'); pg.click('#sessRename'); pg.fill('#renameIn', 'Ćwiczenie'); pg.click('#renameOk')
    pg.click('#sessNew'); pg.wait_for_timeout(800)
    print('after leaving for a new session:', bar(pg), '| buttons', pg.inner_text('#bkSave'), '/', pg.inner_text('#bkLater'))
    pg.screenshot(path=OUT + '/backup_bar_phone.png', clip={'x':0,'y':0,'width':390,'height':300})
    with pg.expect_download(timeout=8000) as dl: pg.click('#bkSave')
    path = dl.value.path(); fname = dl.value.suggested_filename
    sess_copy = os.path.join(OUT, 'session-copy.looper'); dl.value.save_as(sess_copy)
    head = open(path, 'rb').read(8)
    pg.wait_for_timeout(300)
    print('session copy:', fname, head, os.path.getsize(path) // 1000, 'kB | bar after:', bar(pg), '| msg', pg.inner_text('#msg'))
    # back to the first session (leaving the empty one): no bar
    pg.click('.sess-row:has-text("Ćwiczenie") [data-sact=open]'); pg.wait_for_timeout(1500)
    print('back to Ćwiczenie:', bar(pg))
    pg.reload(); pg.wait_for_timeout(2500)
    print('reload, nothing changed:', bar(pg))
    # change something (mute) -> reload -> bar for the open session
    pg.click('#mixer .strip[data-id] [data-ms=mute]'); pg.wait_for_timeout(1200)
    pg.reload(); pg.wait_for_timeout(2500)
    print('reload after a change:', bar(pg))
    pg.click('#bkLater'); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(2500)
    print('reload after "Nie teraz":', bar(pg))
    # listening only is not a change
    pg.click('#play'); pg.wait_for_timeout(800); pg.click('#play'); pg.wait_for_timeout(1200)
    pg.reload(); pg.wait_for_timeout(2500)
    print('reload after just listening:', bar(pg))
    # weekly full backup: pretend the reminder started counting 8 days ago
    pg.evaluate(EDIT_IDX, "s.backup = { lastFull: 0, since: Date.now() - 8 * 86400000, snoozeUntil: 0 };")
    pg.reload(); pg.wait_for_timeout(2500)
    print('8 days later:', bar(pg), '| buttons', pg.inner_text('#bkSave'), '/', pg.inner_text('#bkLater'))
    pg.click('#bkSave'); pg.wait_for_timeout(1500)
    print('full: second step label:', pg.inner_text('#bkSave'))
    with pg.expect_download(timeout=8000) as dl: pg.click('#bkSave')
    path = dl.value.path(); print('full copy:', dl.value.suggested_filename, open(path, 'rb').read(8), '| bar after:', bar(pg))
    pg.click('#menuBtn'); pg.click('#settings summary'); pg.wait_for_timeout(200)
    print('settings:', pg.inner_text('#backupLast'))
    pg.click('#menuBtn')
    pg.reload(); pg.wait_for_timeout(2500)
    print('reload after full copy:', bar(pg))
    # "Później" postpones the weekly reminder by a day
    pg.evaluate(EDIT_IDX, "s.backup.lastFull = Date.now() - 9 * 86400000; s.list.forEach((m) => { m.edited = Date.now() - 86400000; m.copied = Date.now() - 86400000; });")
    pg.reload(); pg.wait_for_timeout(2500)
    print('9 days after the last full copy:', bar(pg))
    pg.click('#bkLater'); pg.wait_for_timeout(400); pg.reload(); pg.wait_for_timeout(2500)
    print('after "Później":', bar(pg))
    # older sessions (before this version) have no backup history: the open one is offered a copy
    pg.evaluate(EDIT_IDX, "s.list.forEach((m) => { delete m.edited; delete m.copied; delete m.sig; delete m.snoozed; });")
    pg.reload(); pg.wait_for_timeout(2500)
    print('older session:', bar(pg))
    # the session copy opens as a session with its recording
    pg.click('#bkLater')
    pg.click('#sessBtn')
    with pg.expect_file_chooser() as fc: pg.click('#sessImport')
    fc.value.set_files(sess_copy); pg.wait_for_timeout(2500)
    print('opened copy:', pg.inner_text('#sessName'), '| tracks', [e.inner_text() for e in pg.query_selector_all('.trk-name')], '| bar', bar(pg))
    print('ERRS', errs)
    b.close()
