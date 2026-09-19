"""Pictures for the vocabulary: ARASAAC pictograms (https://arasaac.org), licence CC BY-NC-SA, author Sergio Palao,
owner Gobierno de Aragón. Only exact keyword matches are taken, so a wrong picture is rare; words without a match simply
have no picture. Output: ../img/<id>.webp (256 px, white background) and ../img/index.json {term: id}.
Incremental: search results are cached in tools/img_cache/, existing files are kept.  usage: python build_images.py [max_new]
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image
from media_terms import all_terms, APP, ROOT

CACHE = os.path.join(ROOT, 'img_cache'); OUT = os.path.join(APP, 'img')
UA = {'User-Agent': 'PhunziesClassroom/1.13 (non-commercial classroom app; teacher in Spain)'}
OVERRIDES = os.path.join(ROOT, 'img_overrides.json')   # {"term": pictogram id, or 0 for "no picture"} fixes after a visual check

def get(url, tries=3):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 + 3 * i)
        except Exception: time.sleep(2 + 3 * i)
    return None

def variants(term):
    t = term.split(' / ')[0].split('/')[0].strip() if '/' in term and ' ' not in term.split('/')[0].strip() else term
    v = [t]
    for pre in ('to ', 'a ', 'an ', 'the '):
        if t.startswith(pre): v.append(t[len(pre):])
    t2 = re.sub(r"\b(your|his|her|my|someone's|somebody's|one's)\b", '', t).replace('  ', ' ').strip()
    if t2 != t: v.append(t2)
    # second-choice spellings, only for short terms: singular / plural, -ing form, "have breakfast" -> "breakfast"
    if len(t.split()) <= 3 and not t.endswith('.'):
        m = re.match(r"^(?:have|eat|take|play|ride|do|go|make)\s+(?:(?:a|an|the|your|my)\s+)?(.+)$", t)
        if m and len(t.split()) <= 3: v.append(m.group(1))
        last = t.split()[-1]; stem = t[:len(t) - len(last)]
        if last.endswith('ies') and len(last) > 4: v.append(stem + last[:-3] + 'y')
        elif last.endswith('oes') or last.endswith('ches') or last.endswith('shes') or last.endswith('sses') or last.endswith('xes'): v.append(stem + last[:-2])
        elif last.endswith('s') and not last.endswith('ss') and len(last) > 3: v.append(stem + last[:-1])
        elif len(t.split()) == 1 and not last.endswith('ing'): v.append(t + 's')
        if len(t.split()) == 1 and last.endswith('ing') and len(last) > 5:
            b = last[:-3]; v += [b, b + 'e'] + ([b[:-1]] if len(b) > 2 and b[-1] == b[-2] else [])
    return list(dict.fromkeys(x for x in v if x))

def search(q):
    f = os.path.join(CACHE, re.sub(r'[^a-z0-9]+', '_', q)[:80] + '.json')
    if os.path.exists(f): return json.load(open(f, encoding='utf-8'))
    raw = get('https://api.arasaac.org/v1/pictograms/en/search/' + urllib.parse.quote(q))
    res = json.loads(raw) if raw else []
    slim = [{'id': x['_id'], 'kw': [k.get('keyword', '').lower() for k in x.get('keywords', [])], 'bad': bool(x.get('sex') or x.get('violence'))} for x in res[:12]]
    json.dump(slim, open(f, 'w', encoding='utf-8')); time.sleep(0.12)
    return slim

def pick(term):
    for q in variants(term):
        for x in search(q):
            if not x['bad'] and q in x['kw']: return x['id']
    return None

def main():
    os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    over = json.load(open(OVERRIDES, encoding='utf-8')) if os.path.exists(OVERRIDES) else {}
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    index, new, miss = {}, 0, 0
    terms = all_terms()
    for n, (term, kind) in enumerate(terms, 1):
        if kind == 'verbs': continue
        pid = over[term] if term in over else pick(term)
        if not pid: miss += 1; continue
        dst = os.path.join(OUT, f'{pid}.webp')
        if not os.path.exists(dst):
            if new >= limit: continue
            raw = get(f'https://static.arasaac.org/pictograms/{pid}/{pid}_300.png')
            if not raw: miss += 1; continue
            im = Image.open(io.BytesIO(raw)).convert('RGBA'); bg = Image.new('RGBA', im.size, 'white'); bg.alpha_composite(im)
            bg.convert('RGB').resize((256, 256), Image.LANCZOS).save(dst, 'WEBP', quality=78, method=6); new += 1; time.sleep(0.1)
        index[term] = pid
        if n % 200 == 0: print(f'{n}/{len(terms)} terms · {len(index)} with picture', flush=True)
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    size = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f'DONE {len(index)} terms with a picture, {miss} without, {new} downloaded now, folder {size // 1024} KB', flush=True)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
