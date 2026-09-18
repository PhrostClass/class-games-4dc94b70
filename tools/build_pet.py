"""Build ../pet.json (B1 Preliminary practice pack used by the app's Exam prep area) from tools/pet/*.txt + exam.json,
and write the printable pack + Anki import file to the Desktop.
Headwords come from the official B1 Preliminary vocabulary list (tools/pet/list_alt.pdf, August 2025 edition,
see headwords_ranked.json); translations, sentences, texts, questions and tips are written for this app.
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'pet')
OUT = os.path.join(ROOT, '..', 'pet.json')
DESK = r'C:\Users\fepsi\Desktop\Carlos Polo - PET'
PAIR_SEP = re.compile(r'\s*\|\s*|\t+|\s+=\s+|\s+[-–—]\s+|\s+:\s+')   # same as the app: these would split an entry
CATS = {'art': 'Articles', 'prep': 'Prepositions', 'aux': 'Auxiliaries & modals', 'pron': 'Pronouns, it & there', 'rel': 'Relative pronouns',
        'quant': 'Quantifiers', 'conj': 'Linking words', 'phr': 'Phrasal verbs & fixed phrases', 'comp': 'Comparisons', 'verb': 'Verb collocations'}

def lines(name):
    for ln in open(os.path.join(SRC, name), encoding='utf-8').read().split('\n'):
        yield ln.rstrip()

def build_vocab():
    hw = os.path.join(SRC, 'headwords_ranked.json')   # extracted from the official PDF; not in the repo, so the check is optional
    official = {x['w'].lower() for x in json.load(open(hw, encoding='utf-8'))} if os.path.exists(hw) else set()
    flat = ' | '.join(sorted(official))
    out, topic, seen, missing = [], '', set(), []
    for ln in lines('vocab.txt'):
        if ln.startswith('## '): topic = ln[3:].strip(); continue
        if ln.startswith('#') or '||' not in ln: continue
        p = [x.strip() for x in ln.split('||')]
        assert len(p) == 4, ln
        m = re.match(r'^(.*?)\s*\(([^)]*)\)$', p[0]); assert m, ln
        w, pos = m.group(1), m.group(2)
        assert w.lower() not in seen, 'duplicate ' + w
        seen.add(w.lower())
        for f in p[1:] + [w]:
            assert not PAIR_SEP.search(f), f'separator inside field: {f}'
        first = w.lower().split()[0]
        if official and w.lower() not in official and not re.search(r'(^| \| )' + re.escape(first) + r'\b', flat) and not re.search(r'\b' + re.escape(w.lower().split()[-1]) + r'\b', flat): missing.append(w)
        out.append({'w': w, 'pos': pos, 'es': p[1], 'ex_es': p[2], 'ex_en': p[3], 'topic': topic})
    if missing: print('NOT in the official list:', missing)
    return out

def build_cloze():
    texts, cur = [], None
    for ln in lines('cloze.txt'):
        if ln.startswith('# ') and not re.match(r'^# (B1|A gap|Categories)', ln):
            cur = {'id': 'c%02d' % (len(texts) + 1), 'title': ln[2:].strip(), 'text': '', 'gaps': []}; texts.append(cur); continue
        if ln.startswith('#') or not ln.strip() or cur is None: continue
        def gap(m):
            f = [x.strip() for x in m.group(1).split('#')]
            assert f[1] in CATS, f
            cur['gaps'].append({'a': [a.strip() for a in f[0].split('/')], 'cat': f[1], 'why': f[2] if len(f) > 2 else ''})
            return '{%d}' % len(cur['gaps'])
        cur['text'] += (' ' if cur['text'] else '') + re.sub(r'\{\{(.*?)\}\}', gap, ln.strip())
    for t in texts: assert len(t['gaps']) == 6, (t['title'], len(t['gaps']))
    return texts

def build_drills():
    out = []
    for ln in lines('drills.txt'):
        if ln.startswith('#') or '|' not in ln: continue
        p = [x.strip() for x in ln.split('|')]
        assert len(p) == 4 and p[0] in CATS and p[1].count('___') == 1, ln
        out.append({'cat': p[0], 's': p[1], 'a': [a.strip() for a in p[2].split('/')], 'why': p[3]})
    return out

def main():
    vocab, cloze, drills = build_vocab(), build_cloze(), build_drills()
    exam = json.load(open(os.path.join(SRC, 'exam.json'), encoding='utf-8'))
    for ex in exam['reading'] + exam['listening']:
        for it in ex['items']:
            assert ('opts' in it and 0 <= it['a'] < len(it['opts'])) or it.get('ans'), it
    data = {'v': 1, 'list': 'Cambridge B1 Preliminary vocabulary list, August 2025', 'cats': CATS, 'vocab': vocab, 'cloze': cloze, 'drills': drills,
            'reading': exam['reading'], 'listening': exam['listening'], 'guide': exam['guide']}
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    from collections import Counter
    print(f'vocab {len(vocab)} · cloze texts {len(cloze)} ({sum(len(t["gaps"]) for t in cloze)} gaps) · drills {len(drills)} · reading {len(exam["reading"])} · listening {len(exam["listening"])}')
    print('gaps by category:', dict(Counter(g['cat'] for t in cloze for g in t['gaps'])))
    print('pet.json', os.path.getsize(OUT), 'bytes')
    os.makedirs(DESK, exist_ok=True)
    with open(os.path.join(DESK, 'PET hardest words - Anki import.txt'), 'w', encoding='utf-8') as f:
        f.write('#separator:tab\n#html:true\n#deck:PET B1 hardest words\n#notetype:Basic\n')
        for v in vocab:
            f.write(f'{html.escape(v["w"])} <small>({v["pos"]})</small>\t<b>{html.escape(v["es"])}</b><br><br>{html.escape(v["ex_es"])}<br><i>{html.escape(v["ex_en"])}</i>\n')
    open(os.path.join(DESK, 'pack.html'), 'w', encoding='utf-8').write(print_html(data))
    print('Desktop files written to', DESK)

def print_html(d):
    e = html.escape
    def gaps(text, n0=1): return re.sub(r'\{(\d+)\}', lambda m: f'<b>({int(m.group(1)) + n0 - 1})</b> ________', e(text))
    h = ['<!doctype html><meta charset="utf-8"><title>B1 Preliminary practice pack</title><style>',
         'body{font:11.5pt/1.5 Georgia,serif;margin:0;color:#111}h1{font:700 20pt Arial;margin:0 0 4pt}h2{font:700 14pt Arial;margin:18pt 0 6pt;border-bottom:2px solid #333;page-break-after:avoid}',
         'h3{font:700 11.5pt Arial;margin:12pt 0 3pt;page-break-after:avoid}.t{page-break-inside:avoid;margin-bottom:10pt}.pb{page-break-before:always}li{margin:2pt 0}',
         '.q{page-break-inside:avoid;margin:5pt 0}.box{border:1px solid #888;padding:6pt 9pt;margin:5pt 0;white-space:pre-line;page-break-inside:avoid}table{border-collapse:collapse;width:100%;font-size:9.5pt}td{border-bottom:1px solid #ccc;padding:2pt 4pt;vertical-align:top}.k{font-size:9.5pt;columns:2}.small{font-size:9.5pt;color:#444}',
         '</style><h1>B1 Preliminary (PET) practice pack</h1><div class="small">Carlos Polo · Reading Part 6 in depth, a taste of the other reading parts, listening scripts and the hardest words of the August 2025 word list. Interactive version (with audio and spaced-repetition flashcards): Phunzies Classroom → Home students → Exam prep.</div>']
    for g in d['guide']:
        h.append(f'<h3>{e(g["title"])}</h3><ul>' + ''.join(f'<li>{e(p)}</li>' for p in g['points']) + '</ul>')
    h.append('<h2 class="pb">Reading Part 6 · 24 open cloze texts</h2><div class="small">Write ONE word in each gap.</div>')
    for i, t in enumerate(d['cloze'], 1):
        h.append(f'<div class="t"><h3>{i}. {e(t["title"])}</h3>{gaps(t["text"])}</div>')
    h.append('<h2 class="pb">Reading Part 6 · one-gap training by type</h2>')
    n = 0
    for c, name in d['cats'].items():
        h.append(f'<h3>{e(name)}</h3>')
        for x in [x for x in d['drills'] if x['cat'] == c]:
            n += 1; h.append(f'<div class="q">{n}. {e(x["s"]).replace("___", "________")}</div>')
    h.append('<h2 class="pb">The other reading parts</h2>')
    for ex in d['reading']:
        h.append(f'<h3>{e(ex["title"])}</h3><div class="small">{e(ex["intro"])}</div>')
        if ex.get('text'): h.append(f'<div class="box">{e(ex["text"])}</div>')
        if ex.get('bank'): h.append(''.join(f'<div class="q"><b>{b["k"]}</b> {e(b["t"])}</div>' for b in ex['bank']))
        for i, it in enumerate(ex['items'], 1):
            if it.get('text'): h.append(f'<div class="box">{e(it["text"])}</div>')
            opts = '' if ex.get('bank') else '<br>' + ' &nbsp; '.join(f'<b>{"ABCD"[j]}</b> {e(o)}' for j, o in enumerate(it['opts']))
            h.append(f'<div class="q">{i}. {e(it["q"])}{opts}{" &nbsp; ____" if ex.get("bank") else ""}</div>')
    h.append('<h2 class="pb">Listening · questions</h2><div class="small">The teacher reads the script (or plays it in the app). Play everything twice.</div>')
    for ex in d['listening']:
        h.append(f'<h3>{e(ex["title"])}</h3><div class="small">{e(ex["intro"])}</div>')
        for i, it in enumerate(ex['items'], 1):
            opts = '<br>' + ' &nbsp; '.join(f'<b>{"ABC"[j]}</b> {e(o)}' for j, o in enumerate(it['opts'])) if it.get('opts') else ''
            h.append(f'<div class="q">{i}. {e(it["q"])}{opts}</div>')
    h.append('<h2 class="pb">Listening · scripts (teacher)</h2>')
    sp = lambda s: ''.join(f'<div class="q"><b>{x["v"]}:</b> {e(x["t"])}</div>' for x in s)
    for ex in d['listening']:
        h.append(f'<h3>{e(ex["title"])}</h3>')
        if ex.get('script'): h.append(sp(ex['script']))
        for i, it in enumerate(ex['items'], 1):
            if it.get('script'): h.append(f'<div class="small">Recording {i}</div>' + sp(it['script']))
    h.append('<h2 class="pb">Answer key</h2><h3>Part 6 texts</h3><div class="k">')
    for i, t in enumerate(d['cloze'], 1):
        h.append(f'<div class="q"><b>{i}. {e(t["title"])}</b><br>' + '<br>'.join(f'({j}) <b>{e(" / ".join(g["a"]))}</b>' + (f' <span class="small">{e(g["why"])}</span>' if g['why'] else '') for j, g in enumerate(t['gaps'], 1)) + '</div>')
    h.append('</div><h3>One-gap training</h3><div class="k">')
    n = 0
    for c in d['cats']:
        for x in [x for x in d['drills'] if x['cat'] == c]:
            n += 1; h.append(f'<div>{n}. <b>{e(" / ".join(x["a"]))}</b> <span class="small">{e(x["why"])}</span></div>')
    h.append('</div><h3>Other reading parts and listening</h3>')
    for ex in d['reading'] + d['listening']:
        h.append(f'<div class="q"><b>{e(ex["title"])}</b><br>' + '<br>'.join(f'{i}. <b>{e(it["opts"][it["a"]] if it.get("opts") else it["ans"][0])}</b> <span class="small">{e(it.get("why", ""))}</span>' for i, it in enumerate(ex['items'], 1)) + '</div>')
    h.append(f'<h2 class="pb">The hardest words · {len(d["vocab"])} cards</h2><div class="small">Headwords from the Cambridge B1 Preliminary vocabulary list (August 2025). English → Spanish (Spain), with an example in both languages.</div>')
    topic = None
    for v in d['vocab']:
        if v['topic'] != topic:
            if topic is not None: h.append('</table>')
            topic = v['topic']; h.append(f'<h3>{e(topic)}</h3><table>')
        h.append(f'<tr><td style="width:17%"><b>{e(v["w"])}</b> <span class="small">{e(v["pos"])}</span></td><td style="width:20%">{e(v["es"])}</td><td>{e(v["ex_es"])}<br><i>{e(v["ex_en"])}</i></td></tr>')
    h.append('</table>')
    return '\n'.join(h)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
