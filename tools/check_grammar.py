"""Validate tools/grammar_data/<book>.json (format written by the grammar writers). usage: python tools/check_grammar.py tt5 [prep4 ...]"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
BAD = re.compile(r'\||\t|\s[-–—]\s|\s:\s|\s=\s')

def check(book):
    path = os.path.join(ROOT, 'grammar_data', book + '.json'); errs = []
    d = json.load(open(path, encoding='utf-8'))
    brief = json.load(open(os.path.join(ROOT, 'grammar_briefs', book + '.json'), encoding='utf-8'))
    want = {u['n'] for u in brief['units']}; got = {u['n'] for u in d['units']}
    if want - got: errs.append(f'missing units {sorted(want - got)}')
    n = 0
    for u in d['units']:
        tag = f'U{u["n"]}'
        if not u.get('title') or not u.get('notes'): errs.append(f'{tag}: title/notes missing')
        if len(u['items']) < 18: errs.append(f'{tag}: only {len(u["items"])} items')
        seen = set()
        for i, it in enumerate(u['items'], 1):
            n += 1; t = it.get('t'); q = it.get('q', ''); w = f'{tag} #{i}'
            if t not in ('choose', 'write', 'fix', 'order'): errs.append(f'{w}: bad type {t}'); continue
            if q.lower() in seen: errs.append(f'{w}: duplicate question')
            seen.add(q.lower())
            ans = [it['a']] if t == 'choose' else it.get('a')
            if not ans or not isinstance(ans, list) or not all(isinstance(a, str) and a.strip() for a in ans): errs.append(f'{w}: answers must be a non-empty list of strings'); continue
            for s in [q] + ans + it.get('opts', []):
                if BAD.search(s): errs.append(f'{w}: forbidden separator in "{s}"')
            if t in ('choose', 'write') and q.count('___') != 1: errs.append(f'{w}: needs exactly one ___')
            if t == 'choose':
                o = it.get('opts', [])
                if not 2 <= len(o) <= 4 or len(set(x.lower() for x in o)) != len(o): errs.append(f'{w}: options')
                if it['a'] not in o: errs.append(f'{w}: answer not among options')
            if t == 'write' and not re.search(r'\([^)]+\)', q): errs.append(f'{w}: write item needs the base word in brackets')
            if t == 'order':
                chunks = sorted(re.sub(r'[^\w\' ]', '', c).lower().split() for c in q.split(' / '))
                flat = sorted(x for c in chunks for x in c)
                for a in ans:
                    if sorted(re.sub(r'[^\w\' ]', '', a).lower().split()) != flat: errs.append(f'{w}: words of "{a}" do not match the chunks')
            if t == 'fix' and any(a.strip().lower() == q.strip().lower() for a in ans): errs.append(f'{w}: correction equals the question')
    print(f'{book}: {len(d["units"])} units, {n} items, {len(errs)} problems')
    for e in errs[:60]: print('  ', e)
    return not errs

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ok = all([check(b) for b in sys.argv[1:]])
    sys.exit(0 if ok else 1)
