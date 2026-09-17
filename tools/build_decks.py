"""Build textbook decks (textbooks.json for the app + a report) from the harvested Milton data.
python build_decks.py            -> writes ../textbooks.json and milton_data/report.md
"""
import json, os, re, glob, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'milton_data')
OUT_JSON = os.path.join(ROOT, '..', 'textbooks.json')
OUT_REPORT = os.path.join(DATA, 'report.md')

TAG = re.compile(r'<[^>]+>')
URLISH = re.compile(r'(^/|https?://|\.(png|jpg|jpeg|mp3|gif)\b)', re.I)
SMALL = set('a an the is am are to do in on at of my he we it me up go be so or no if us by as and but can has was his her you not did for how who why she they'.split())

def clean(s):
    s = html.unescape(TAG.sub(' ', str(s or '')))
    s = s.replace('\xa0', ' ').replace('|', '/').replace('&', ' ')
    return re.sub(r'\s+', ' ', s).strip()
def entry(*parts):
    ps = [clean(p) for p in parts if clean(p)]
    return ' | '.join(ps[:3]) if ps else ''
def gap_question(q):
    ans = re.findall(r'\[([^\]]+)\]', q)
    return clean(re.sub(r'\[[^\]]+\]', '____', q)), [clean(a) for a in ans]
def verb_forms(d):
    return [x.strip() for x in d.split(',')] if d and re.fullmatch(r"[\w' -]+, [\w' -]+", d) else None

def map_question(q, sec_name):
    """-> list of (kind, entry); kind: vocab (word | definition), word, verb (v | past | participle), qa (question | answer)"""
    t = q.get('type') or ''
    out = []
    a = q.get('answers') or []
    if t in ('flashcard-learn', 'flashcard-game'):
        if len(a) >= 2 and isinstance(a[0], dict):
            x, y = clean(a[0].get('text')), clean(a[1].get('text'))
            if URLISH.search(x): x = ''
            if URLISH.search(y): y = ''
            if x and y:
                if t == 'flashcard-learn': w, d = x, y
                else: w, d = (x, y) if len(x) <= len(y) else (y, x)
                forms = verb_forms(d)
                if forms and (re.search(r'verb', sec_name, re.I) or len(w.split()) == 1): out.append(('verb', entry(w, *forms)))
                else: out.append(('vocab', entry(w, d)))
            elif x or y: out.append(('word', x or y))          # picture flashcard: the word is on whichever side has text
    elif t in ('mapping-game', 'mapping-learn'):
        for x in a:
            if isinstance(x, dict):
                w = clean(x.get('text')) or clean(x.get('description'))
                if w: out.append(('word', w))
    elif t in ('fill-gap', 'select-fill-gap'):
        text, ans = gap_question(q.get('question') or '')
        if not ans: ans = [clean(x) for x in a if isinstance(x, str)]
        if ans and all(len(x) <= 1 for x in ans): return out          # "fill in the letters" spelling exercises
        if text and ans:
            opts = []
            if t == 'select-fill-gap' and q.get('fakeData'):
                for fd in q['fakeData']:
                    for x in (fd if isinstance(fd, list) else [fd]): opts.append(clean(x))
            if opts: text += '  (' + ' / '.join(sorted(set(ans + opts), key=str.lower)) + ')'
            out.append(('qa', entry(text, ', '.join(ans))))
    elif t == 'select-word':
        text, ans = gap_question(q.get('question') or '')
        if text and ans and len(text) <= 220: out.append(('qa', entry(text, ', '.join(ans))))
    elif t == 'quiz':
        c = q.get('correct')
        if isinstance(c, int) and 0 <= c < len(a) and clean(q.get('question')) and all(isinstance(x, str) for x in a):
            opts = [clean(x) for x in a]; text = clean(q.get('question'))
            if len(opts) > 1 and not (len(opts) == 2 and {x.lower() for x in opts} == {'true', 'false'}): text += '  (' + ' / '.join(opts) + ')'
            out.append(('qa', entry(text, opts[c])))
    elif t == 'matching':
        if len(a) >= 2 and isinstance(a[0], dict):
            x, y = clean(a[0].get('text')), clean(a[1].get('text'))
            xi, yi = URLISH.search(x) or a[0].get('type') == 'image', URLISH.search(y) or a[1].get('type') == 'image'
            if x and y and not xi and not yi:
                forms = verb_forms(y)
                out.append(('verb', entry(x, *forms)) if forms else ('qa', entry(x, y)))
            elif (x and not xi) or (y and not yi): out.append(('word', x if (x and not xi) else y))
    elif t == 'groups':
        g = clean(q.get('question'))
        for x in a:
            if isinstance(x, dict) and clean(x.get('text')) and g: out.append(('qa', entry(clean(x.get('text')), g)))
    elif t == 'ordering':
        if a and isinstance(a[0], str):
            sent = clean(a[0]); words = sent.rstrip('.?!').split()
            if len(words) >= 3 and sent[:1].isupper() and not any(len(w) <= 3 and w.islower() and w not in SMALL for w in words):
                shuffled = sorted(words, key=lambda w: (len(w), w.lower()))
                if shuffled == words: shuffled = list(reversed(words))
                out.append(('qa', entry('Put in order: ' + ' / '.join(shuffled), sent)))
    return out

def good_qa(e):
    if ' | ' not in e: return False
    q, a = e.split(' | ', 1); a = a.split('#')[0].strip()
    if URLISH.search(q) or URLISH.search(a): return False
    if len(q) < 8 or len(q) > 260 or not re.search(r'[A-Za-z]{2}', q): return False
    if q.count('____') > 2 or re.match(r'^[A-H]\)?:?\s*____', q): return False
    if not a or len(a) > 60 or not re.search(r'[A-Za-z0-9]', a): return False
    return True
def fix_qa(e):
    q, a = e.split(' | ', 1); return q + ' | ' + a.split('#')[0].strip()
def dedupe(items):
    seen, out = set(), []
    for x in items:
        k = x.lower()
        if x and k not in seen: seen.add(k); out.append(x)
    return out

def load_grade(gdir):
    books = json.load(open(os.path.join(gdir, 'textbooks.json'), encoding='utf-8'))
    units = {}
    for f in glob.glob(os.path.join(gdir, 'unit_*.json')): u = json.load(open(f, encoding='utf-8')); units[u['id']] = u
    qs = {}
    for f in glob.glob(os.path.join(gdir, 'q_*.json')): qs[os.path.basename(f)[2:-5]] = json.load(open(f, encoding='utf-8'))
    return books, units, qs

def build():
    result = {'generated': datetime.datetime.now().isoformat(timespec='minutes'), 'books': []}
    report = ['# Textbook decks report', '']
    for gdir in sorted(glob.glob(os.path.join(DATA, 'grade*'))):
        grade = int(re.search(r'grade(\d)', gdir).group(1))
        if not os.path.exists(os.path.join(gdir, 'textbooks.json')): continue
        books, units, qs = load_grade(gdir)
        sb = next((b for b in books if re.search(r'\bSB\b|Student', b['title'])), None)
        ab = next((b for b in books if re.search(r'Activity|\bAB\b', b['title'])), None)
        if not sb: report.append(f'## Grade {grade}: NO student book found'); continue
        bookname = re.sub(r'\s*-\s*Second Edition|English Red|\bSB\b', '', sb['title']); bookname = re.sub(r'\s+', ' ', bookname).strip()
        book = {'id': f'tt{grade}', 'name': bookname, 'grade': grade, 'units': []}
        report.append(f'## Grade {grade} — {sb["title"]}  (AB: {ab["title"] if ab else "none"})'); report.append('')
        ab_units = {}
        if ab:
            for u in ab['units']:
                uu = units.get(u['id'])
                if uu is not None: ab_units[uu.get('position')] = uu
        for u in sb['units']:
            uu = units.get(u['id'])
            if uu is None or uu.get('extra') or not uu.get('pdf'): continue
            pos = uu.get('position'); title = uu.get('title') or u.get('title')
            vocab, words, verbs, grammar, review, gdesc = [], [], [], [], [], []
            skipped = [0]
            def scan(unit, is_ab, vocab_terms):
                for sec in unit.get('sections', []):
                    sname = sec.get('name') or ''
                    for ex in sec.get('exercises', []):
                        ql = qs.get(ex['id']) or []
                        mapped = [(k, e) for q in ql for (k, e) in map_question(q, sname)]
                        qa_only = [e for k, e in mapped if k == 'qa' and ' | ' in e]
                        prefix = ''
                        if len(qa_only) >= 3:
                            p = os.path.commonprefix([e.split(' | ')[0] for e in qa_only])
                            p = p[:p.rfind(' ') + 1] if ' ' in p else ''
                            if len(p) >= 12 and '____' not in p: prefix = p
                        if not is_ab and re.search(r'grammar', sname, re.I) and not mapped and ex.get('title') and not re.match(r'^(skim|choose|complete|fill|read|look|listen|write|match|circle|order|say|talk|watch|extra|ask|think|find|now|in pairs|work|create|use|put|make|correct|rewrite|change|answer|discuss|describe|tell|play|practise|record|underline|tick|draw|imagine|decide|compare|check|sort|classify|label|what|which|who|how|where|when|why|do|does|is|are|can|copy|cross|number|pick|study|yes|no|point|plan|role|act|sing|count|colour|color|spell|repeat|go|let)', ex['title'].strip(), re.I) and not re.search(r'partner|tip|notebook', ex['title'], re.I):
                            gdesc.append(clean(ex['title']).rstrip('.'))
                        for q, (kind, e) in [(q, m) for q in ql for m in map_question(q, sname)]:
                            if not e: continue
                            if kind == 'qa':
                                if prefix and e.startswith(prefix): e = e[len(prefix):]
                                if not good_qa(e): skipped[0] += 1; continue
                                e = fix_qa(e)
                            if kind == 'vocab': vocab.append(e); continue
                            if kind == 'word': words.append(e); continue
                            if kind == 'verb': verbs.append(e); continue
                            if is_ab:
                                ans = e.split(' | ', 1)[1].lower()
                                if ans in vocab_terms or q.get('type') == 'matching': review.append(e)
                                elif q.get('type') in ('fill-gap', 'select-fill-gap', 'select-word', 'ordering'): grammar.append(e)
                                else: skipped[0] += 1
                                continue
                            if re.search(r'grammar|verb', sname, re.I): grammar.append(e)
                            elif re.search(r'review|vocab', sname, re.I): review.append(e)
                            else: skipped[0] += 1
            scan(uu, False, set())
            terms = {v.split(' | ')[0].lower() for v in vocab} | {w.lower() for w in words}
            if pos in ab_units: scan(ab_units[pos], True, terms)
            defs = {v.split(' | ', 1)[1].lower() for v in vocab if ' | ' in v}
            vterms = {v.split(' | ')[0].lower() for v in vocab}
            vocab = vocab + [w for w in words if w.lower() not in vterms and w.lower() not in defs]
            seen_t, vv = set(), []
            for v in vocab:
                t0 = v.split(' | ')[0].lower()
                if t0 in seen_t or t0 in defs: continue
                seen_t.add(t0); vv.append(v)
            vocab = vv
            extra_path = os.path.join(ROOT, 'vocab_extra.json')
            if os.path.exists(extra_path):
                extra = json.load(open(extra_path, encoding='utf-8')).get(str(grade), {}).get(str(pos + 1), [])
                have = {v.split(' | ')[0].lower() for v in vocab}
                vocab += [w for w in extra if w.lower() not in have]
            verbs, grammar, review = dedupe(verbs), dedupe(grammar), dedupe(review)
            gdesc = dedupe(gdesc)
            unit = {'n': pos + 1, 'title': title, 'decks': []}
            if vocab: unit['decks'].append({'kind': 'vocab', 'name': f'U{pos+1} Vocabulary · {title}', 'desc': f'Unit {pos+1} words with the definitions used in the book.', 'words': vocab})
            if grammar: unit['decks'].append({'kind': 'grammar', 'name': f'U{pos+1} Grammar · {title}', 'desc': (('Grammar: ' + '; '.join(gdesc) + '. ') if gdesc else '') + 'Questions from the grammar and verb lessons of both books.', 'words': grammar})
            if verbs: unit['decks'].append({'kind': 'verbs', 'name': f'U{pos+1} Irregular verbs · {title}', 'desc': 'Verb | past simple | past participle. Play them as trios in Memory.', 'words': verbs})
            if review: unit['decks'].append({'kind': 'review', 'name': f'U{pos+1} Review · {title}', 'desc': 'Definitions to guess the word, plus the review-quiz questions.', 'words': review})
            book['units'].append(unit)
            report.append(f'- U{pos+1} {title}: ' + ', '.join(f"{d['kind']} {len(d['words'])}" for d in unit['decks']) + f'  (skipped {skipped[0]})' + (f'  · grammar: {"; ".join(gdesc)}' if gdesc else '') + ('' if pos in ab_units else '  · NO ACTIVITY BOOK UNIT'))
        result['books'].append(book)
        report.append('')
    json.dump(result, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    open(OUT_REPORT, 'w', encoding='utf-8').write('\n'.join(report))
    print('\n'.join(report)); print('written', OUT_JSON, os.path.getsize(OUT_JSON), 'bytes')

if __name__ == '__main__':
    build()
