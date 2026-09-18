"""Merge the Prepare (ESO) levels into ../textbooks.json and write the summary .txt files into Desktop\\prepare.
Input: tools/prepare_data/level{N}.json  (unit word lists + grammar topics from the book; definitions, grammar
notes and practice questions written for this app, not copied from the book).
Run AFTER build_decks.py (which rewrites textbooks.json with the Time Travellers books).
"""
import json, os, glob, re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'prepare_data')
TB = os.path.join(ROOT, '..', 'textbooks.json')
DESK = r'C:\Users\fepsi\Desktop\prepare'

IRREGULAR = ['be | was/were | been', 'become | became | become', 'begin | began | begun', 'break | broke | broken', 'bring | brought | brought', 'build | built | built', 'buy | bought | bought', 'catch | caught | caught', 'choose | chose | chosen', 'come | came | come', 'cost | cost | cost', 'cut | cut | cut', 'do | did | done', 'draw | drew | drawn', 'drink | drank | drunk', 'drive | drove | driven', 'eat | ate | eaten', 'fall | fell | fallen', 'feel | felt | felt', 'find | found | found', 'fly | flew | flown', 'forget | forgot | forgotten', 'get | got | got', 'give | gave | given', 'go | went | gone', 'grow | grew | grown', 'have | had | had', 'hear | heard | heard', 'hide | hid | hidden', 'hit | hit | hit', 'hold | held | held', 'keep | kept | kept', 'know | knew | known', 'learn | learnt | learnt', 'leave | left | left', 'lend | lent | lent', 'lose | lost | lost', 'make | made | made', 'meet | met | met', 'pay | paid | paid', 'put | put | put', 'read | read | read', 'ride | rode | ridden', 'ring | rang | rung', 'run | ran | run', 'say | said | said', 'see | saw | seen', 'sell | sold | sold', 'send | sent | sent', 'sing | sang | sung', 'sit | sat | sat', 'sleep | slept | slept', 'speak | spoke | spoken', 'spend | spent | spent', 'stand | stood | stood', 'steal | stole | stolen', 'swim | swam | swum', 'take | took | taken', 'teach | taught | taught', 'tell | told | told', 'think | thought | thought', 'throw | threw | thrown', 'understand | understood | understood', 'wake | woke | woken', 'wear | wore | worn', 'win | won | won', 'write | wrote | written']

def clean(s): return re.sub(r'\s+', ' ', str(s or '').replace('|', '/')).strip()

def main():
    tb = json.load(open(TB, encoding='utf-8'))
    tb['books'] = [b for b in tb['books'] if not str(b.get('id', '')).startswith('prep')]
    for b in tb['books']: b['name'] = re.sub(r'\s+SP$', '', b['name'])
    report = []
    for f in sorted(glob.glob(os.path.join(DATA, 'level*.json'))):
        d = json.load(open(f, encoding='utf-8')); lvl = d['level']
        book = {'id': f'prep{lvl}', 'name': f'Prepare Level {lvl}', 'grade': None, 'units': []}
        vtxt = [f'PREPARE LEVEL {lvl} - VOCABULARY BY UNIT', '(word lists from the book\'s Vocabulary list; short definitions written for class use)', '']
        gtxt = [f'PREPARE LEVEL {lvl} - GRAMMAR BY UNIT', '(topics from the book\'s Grammar reference; notes and practice questions written for class use)', '']
        nwords = nq = 0
        for u in sorted(d['units'], key=lambda x: x['n']):
            n = u['n']; decks = []
            topics = [t for t in (u.get('vocab') or []) if t.get('words')]
            if topics:
                words = []; seen = set()
                for t in topics:
                    for w in t['words']:
                        hw = clean(w.get('w'))
                        if not hw: continue
                        if hw.lower() in seen:                      # same word twice in a unit (noun and verb, two meanings): keep both
                            hw = f"{hw} ({clean(w.get('pos')) or '2'})"
                            if hw.lower() in seen: continue
                        seen.add(hw.lower()); df = clean(w.get('def'))
                        words.append(f'{hw} | {df}' if df else hw)
                title = '; '.join(clean(t['topic']) for t in topics)
                decks.append({'kind': 'vocab', 'name': f'U{n} Vocabulary · {title}'[:90], 'desc': f'Unit {n}: {title}. Word | simple definition.', 'words': words})
                nwords += len(words)
                vtxt.append(f'UNIT {n}')
                for t in topics:
                    vtxt.append(f'  {clean(t["topic"]).upper()}')
                    for w in t['words']:
                        pos = f' ({clean(w.get("pos"))})' if w.get('pos') else ''
                        vtxt.append(f'    {clean(w.get("w"))}{pos} - {clean(w.get("def"))}')
                vtxt.append('')
            g = u.get('grammar')
            if g and g.get('title'):
                qs = [clean_q(q) for q in (g.get('questions') or [])]; qs = [q for q in qs if q]
                pts = [clean(p) for p in (g.get('points') or [])]
                if qs:
                    decks.append({'kind': 'grammar', 'name': f'U{n} Grammar · {clean(g["title"])}'[:90], 'desc': f'Unit {n}: {clean(g["title"])}. ' + short_notes(pts), 'words': qs})
                    nq += len(qs)
                gtxt.append(f'UNIT {n} - {clean(g["title"]).upper()}')
                for p_ in pts: gtxt.append(f'  - {p_}')
                if qs:
                    gtxt.append('  Practice:')
                    for i, q in enumerate(qs, 1):
                        a, b = q.split(' | ', 1); gtxt.append(f'    {i}. {a}   [{b}]')
                gtxt.append('')
            if decks: book['units'].append({'n': n, 'title': '', 'decks': decks})
        if lvl == 4: book['units'].append({'n': 21, 'title': '', 'decks': [{'kind': 'verbs', 'name': 'Irregular verbs · the common ones', 'desc': 'Verb | past simple | past participle. Play them as trios in Memory, or let the games ask for the past forms.', 'words': IRREGULAR}]})
        tb['books'].append(book)
        report.append(f'Level {lvl}: {len(book["units"])} units, {nwords} words, {nq} grammar questions')
        for sub, name, lines in (('Vocabulary', f'Level {lvl} - vocabulary by unit.txt', vtxt), ('Grammar', f'Level {lvl} - grammar by unit.txt', gtxt)):
            folder = os.path.join(DESK, f'Level {lvl}', sub)
            if os.path.isdir(folder): open(os.path.join(folder, name), 'w', encoding='utf-8').write('\n'.join(lines))
    json.dump(tb, open(TB, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('\n'.join(report)); print('textbooks.json', os.path.getsize(TB), 'bytes')

def short_notes(pts, limit=420):
    """Whole points only, as many as fit, so the description never stops mid-sentence."""
    out = ''
    for p_ in pts:
        if len(out) + len(p_) + 1 > limit: break
        out += (' ' if out else '') + p_
    return out or (pts[0][:limit].rsplit(' ', 1)[0] + '…' if pts else '')

def clean_q(q):
    q = re.sub(r'\s+', ' ', str(q or '')).strip()
    if q.count('|') != 1: return ''
    a, b = [x.strip() for x in q.split('|')]
    return f'{a} | {b}' if a and b else ''

if __name__ == '__main__':
    main()
