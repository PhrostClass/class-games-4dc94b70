"""Drive the Milton Education panel with the installed Edge (Playwright, channel=msedge).
Usage: python milton.py <step>   — each step saves screenshots/DOM to tools/milton_out/
"""
import sys, os, json, time
from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(__file__), 'milton_out')
os.makedirs(OUT, exist_ok=True)
PROFILE = os.path.join(os.path.dirname(__file__), 'milton_profile')
URL = 'https://panel.miltoneducation.com/#!/'
_sec = json.load(open(os.path.join(os.path.dirname(__file__), 'milton_secrets.json'), encoding='utf-8'))  # gitignored: {"user": ..., "pass": ...}
USER = _sec['user']
PASS = _sec['pass']

def shot(page, name):
    page.screenshot(path=os.path.join(OUT, name + '.png'), full_page=False)
    with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8') as f:
        f.write(page.url + '\n\n' + page.evaluate('document.body.innerText'))

def run(step):
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE, channel='msedge', headless=True, viewport={'width': 1280, 'height': 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)
        shot(page, '01_start')
        if step == 'clicks':
            # python milton.py clicks "Student Mode" "5" "Yes" "Textbook"   (text of things to click, in order)
            for i, txt in enumerate(sys.argv[2:]):
                loc = page.get_by_text(txt, exact=False).locator('visible=true')
                n = loc.count()
                print(f'[{i}] "{txt}": {n} matches')
                if not n: shot(page, f'10_{i}_notfound'); break
                loc.first.click(timeout=15000)
                page.wait_for_timeout(3500)
                if len(ctx.pages) > 1 and ctx.pages[-1] != page: page = ctx.pages[-1]; page.wait_for_timeout(4000); print('  -> switched to new tab', page.url)
                shot(page, f'10_{i}_{txt[:12].replace(" ", "_")}')
        if step == 'dom':
            # python milton.py dom <url>
            page.goto(sys.argv[2], wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(6000)
            shot(page, '20_dom')
            info = page.evaluate("""() => ({
              links: [...document.querySelectorAll('a,button,[ng-click],[data-ng-click]')].map(e => (e.innerText||'').trim().replace(/\s+/g,' ').slice(0,60) + ' | ' + (e.getAttribute('href')||e.getAttribute('ng-click')||e.getAttribute('data-ng-click')||'')).filter(x => x.length > 3).slice(0,200),
              imgs: [...document.querySelectorAll('img')].map(i => i.src).slice(0,100),
              iframes: [...document.querySelectorAll('iframe')].map(i => i.src),
              canvases: document.querySelectorAll('canvas').length,
            })""")
            with open(os.path.join(OUT, '20_dom.json'), 'w', encoding='utf-8') as f: json.dump(info, f, indent=1, ensure_ascii=False)
            print(json.dumps(info, indent=1, ensure_ascii=False)[:6000])
        if step == 'book':
            # python milton.py book <index>  — open the Nth cover on the textbooks page and dump what the viewer is made of
            page.goto('https://primary.miltoneducation.com/#!/textbooks', wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(6000)
            covers = page.evaluate("[...document.querySelectorAll('img')].map(i => i.src).filter(s => /public\/textbooks\/template_/i.test(s))")
            print('covers:', covers)
            idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            imgs = page.locator('img').locator('visible=true')
            # click the cover with matching src
            target = None
            for k in range(imgs.count()):
                src = imgs.nth(k).get_attribute('src') or ''
                if covers and src == covers[idx]: target = imgs.nth(k); break
            if target is None: target = imgs.nth(idx)
            target.click(timeout=15000); page.wait_for_timeout(8000)
            if len(ctx.pages) > 1 and ctx.pages[-1] != page: page = ctx.pages[-1]; page.wait_for_timeout(6000); print('  -> new tab', page.url)
            shot(page, '30_book')
            info = page.evaluate("""() => ({ url: location.href,
              iframes: [...document.querySelectorAll('iframe')].map(i => i.src),
              imgs: [...document.querySelectorAll('img')].map(i => i.src).filter(s => !/images\/(trainer|gamification|messages)/.test(s)).slice(0,80),
              canvases: document.querySelectorAll('canvas').length,
              text: document.body.innerText.slice(0, 3000) })""")
            print(json.dumps(info, indent=1, ensure_ascii=False)[:8000])
            for fr in page.frames[1:]:
                try: print('FRAME', fr.url, '|', fr.evaluate('document.body ? document.body.innerText.slice(0,1500) : ""'))
                except Exception as e: print('frame err', e)
        if step == 'unit':
            # python milton.py unit <textbook-url> "Unit text" ["next click"...]
            page.goto('https://primary.miltoneducation.com/#!/textbooks', wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(6000)
            covers = page.evaluate("[...document.querySelectorAll('img')].map(i => i.src).filter(s => /public\/textbooks\/template_/i.test(s))")
            bidx = int(sys.argv[2]); imgs = page.locator('img').locator('visible=true'); target = None
            for k in range(imgs.count()):
                if (imgs.nth(k).get_attribute('src') or '') == covers[bidx]: target = imgs.nth(k); break
            target.click(timeout=15000); page.wait_for_timeout(7000)
            for i, txt in enumerate(sys.argv[3:]):
                loc = page.get_by_text(txt, exact=False).locator('visible=true'); print(f'[{i}] "{txt}": {loc.count()}')
                if not loc.count(): break
                loc.first.click(timeout=15000); page.wait_for_timeout(6000)
                if len(ctx.pages) > 1 and ctx.pages[-1] != page: page = ctx.pages[-1]; page.wait_for_timeout(6000); print('  -> new tab', page.url)
                shot(page, f'40_{i}')
            info = page.evaluate("""() => ({ url: location.href,
              iframes: [...document.querySelectorAll('iframe')].map(i => i.src),
              imgs: [...document.querySelectorAll('img')].map(i => i.src).filter(s => /content\.milton|textbook|unit|page/i.test(s) && !/template_|public\/books\//.test(s)).slice(0,80),
              canvases: document.querySelectorAll('canvas').length, objects: [...document.querySelectorAll('object,embed,video,audio')].map(o => o.tagName + ':' + (o.src||o.data||'')).slice(0,20),
              text: document.body.innerText.slice(0, 4000) })""")
            print(json.dumps(info, indent=1, ensure_ascii=False)[:9000])
            for fr in page.frames[1:]:
                try: print('FRAME', fr.url, '|', fr.evaluate('document.body ? document.body.innerText.slice(0,2000) : ""'))
                except Exception as e: print('frame err', e)
        if step == 'net':
            # python milton.py net <bookidx> "Unit text" "click"...  — like 'unit' but logs network responses
            seen = []
            page.on('response', lambda r: seen.append((r.status, r.headers.get('content-type', ''), r.url)))
            page.goto('https://primary.miltoneducation.com/#!/textbooks', wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(6000)
            covers = page.evaluate("[...document.querySelectorAll('img')].map(i => i.src).filter(s => /public\/textbooks\/template_/i.test(s))")
            bidx = int(sys.argv[2]); imgs = page.locator('img').locator('visible=true'); target = None
            for k in range(imgs.count()):
                if (imgs.nth(k).get_attribute('src') or '') == covers[bidx]: target = imgs.nth(k); break
            target.click(timeout=15000); page.wait_for_timeout(7000)
            for i, txt in enumerate(sys.argv[3:]):
                mark = len(seen)
                loc = page.get_by_text(txt, exact=False).locator('visible=true'); print(f'[{i}] "{txt}": {loc.count()}')
                if not loc.count(): break
                loc.first.click(timeout=15000); page.wait_for_timeout(9000)
                shot(page, f'50_{i}')
                for st, ct, u in seen[mark:]:
                    if 'image/' in ct or u.endswith('.png') or u.endswith('.jpg') or 'fonts' in u or '.js' in u or '.css' in u: continue
                    print(f'   {st} {ct[:40]:40} {u[:160]}')
            with open(os.path.join(OUT, '50_net.json'), 'w', encoding='utf-8') as f: json.dump(seen, f, indent=0)
        if step == 'api':
            # python milton.py api <bookidx>  — open the book and print every JSON response body (book + units structure)
            bodies = []
            def on_resp(r):
                try:
                    if 'application/json' in r.headers.get('content-type', '') and 'miltoneducation' in r.url: bodies.append((r.url, r.text()))
                except Exception as e: pass
            page.on('response', on_resp)
            page.goto('https://primary.miltoneducation.com/#!/textbooks', wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(6000)
            covers = page.evaluate("[...document.querySelectorAll('img')].map(i => i.src).filter(s => /public\/textbooks\/template_/i.test(s))")
            bidx = int(sys.argv[2]); imgs = page.locator('img').locator('visible=true'); target = None
            for k in range(imgs.count()):
                if (imgs.nth(k).get_attribute('src') or '') == covers[bidx]: target = imgs.nth(k); break
            target.click(timeout=15000); page.wait_for_timeout(7000)
            for i, txt in enumerate(sys.argv[3:]):
                loc = page.get_by_text(txt, exact=False).locator('visible=true'); print(f'[{i}] "{txt}": {loc.count()}')
                if not loc.count(): break
                loc.first.click(timeout=15000); page.wait_for_timeout(8000)
            with open(os.path.join(OUT, f'60_api_{bidx}.json'), 'w', encoding='utf-8') as f: json.dump(bodies, f, indent=0, ensure_ascii=False)
            for u, b in bodies: print('==', u, len(b)); print(b[:700]); print()
        if step == 'harvest':
            # python milton.py harvest <grade 1-6>  — enter Student Mode for that grade, then save textbooks list + every unit JSON and PDF url
            grade = sys.argv[2]
            for txt in ['Student Mode', f'{grade}ºA PRIM', 'Yes']:
                loc = page.get_by_text(txt, exact=False).locator('visible=true'); loc.first.click(timeout=15000); page.wait_for_timeout(3500)
                if len(ctx.pages) > 1 and ctx.pages[-1] != page: page = ctx.pages[-1]; page.wait_for_timeout(6000)
            base = 'https://primary.miltoneducation.com'
            books = page.request.get(base + '/textbooks/').json()
            d = os.path.join(os.path.dirname(__file__), 'milton_data', f'grade{grade}'); os.makedirs(d, exist_ok=True)
            json.dump(books, open(os.path.join(d, 'textbooks.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            manifest = []
            for b in books:
                print('BOOK', b['id'], b['title'], len(b['units']))
                for u in b['units']:
                    uj = page.request.get(base + '/textbook/unit/' + u['id']).json()
                    json.dump(uj, open(os.path.join(d, f"unit_{u['id']}.json"), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
                    manifest.append({'book': b['title'], 'bookId': b['id'], 'unitId': u['id'], 'pos': uj.get('position'), 'title': uj.get('title'), 'pdf': uj.get('pdf'), 'extra': uj.get('extra')})
                    nq = 0
                    for sec in uj.get('sections', []):
                        for ex in sec.get('exercises', []):
                            qp = os.path.join(d, f"q_{ex['id']}.json")
                            if os.path.exists(qp): continue
                            try:
                                qr = page.request.get(base + '/textbook/questions/' + ex['id'])
                                if qr.status == 200:
                                    json.dump(qr.json(), open(qp, 'w', encoding='utf-8'), ensure_ascii=False); nq += 1
                            except Exception as e: print('      q err', ex['id'], e)
                    print('   ', uj.get('position'), uj.get('title'), 'sections', len(uj.get('sections', [])), 'questions fetched', nq, '->', (uj.get('pdf') or '')[-40:], flush=True)
            json.dump(manifest, open(os.path.join(d, 'manifest.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        if step == 'q':
            # python milton.py q <exerciseId>...  — print /textbook/exercises and /textbook/questions for exercises (needs an active student session)
            base = 'https://primary.miltoneducation.com'
            for ex in sys.argv[2:]:
                for ep in ('exercises', 'questions'):
                    r = page.request.get(f'{base}/textbook/{ep}/{ex}'); t = r.text()
                    print(f'== {ep}/{ex} status={r.status} len={len(t)}'); print(t[:2500]); print()
        if step == 'login':
            # try common selectors
            for sel in ['input[type=email]', 'input[name=email]', 'input[type=text]']:
                if page.locator(sel).count():
                    page.locator(sel).first.fill(USER); break
            page.locator('input[type=password]').first.fill(PASS)
            shot(page, '02_filled')
            page.keyboard.press('Enter')
            page.wait_for_timeout(5000)
            shot(page, '03_after_login')
        ctx.close()

if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'look')
