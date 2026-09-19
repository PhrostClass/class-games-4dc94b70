"""Put the rewritten grammar practice (tools/grammar_data/<book>.json, see grammar_briefs/INSTRUCTIONS.md) into the app:
 - ../textbooks.json: every unit's Grammar deck gets the new questions as "question | answer" entries (for the games)
 - ../grammar.json:   the structured items (choose / write / fix / order + explanations) for the Grammar practice screen
Run AFTER build_decks.py and build_prepare.py (they rewrite textbooks.json). Books without a grammar_data file keep their old deck.
"""
import glob, json, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
TB = os.path.join(ROOT, '..', 'textbooks.json'); OUT = os.path.join(ROOT, '..', 'grammar.json')

def entry(it):
    a = it['a'] if it['t'] == 'choose' else it['a'][0]
    if it['t'] == 'choose': return f"{it['q']} ({' / '.join(it['opts'])}) | {a}"
    if it['t'] == 'fix': return f"Correct it: {it['q']} | {a}"
    if it['t'] == 'order': return f"Put in order: {it['q']} | {a}"
    return f"{it['q']} | {a}"

def notes_desc(notes, limit=420):
    out = ''
    for n in notes:
        if len(out) + len(n) + 1 > limit: break
        out += (' ' if out else '') + n
    return out

def main():
    tb = json.load(open(TB, encoding='utf-8')); decks = {}; report = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'grammar_data', '*.json'))):
        try: d = json.load(open(f, encoding='utf-8'))
        except ValueError: print('skipped (not valid JSON yet):', os.path.basename(f)); continue
        book = next((b for b in tb['books'] if b['id'] == d['book']), None)
        if not book: print('unknown book', d['book']); continue
        n_items = 0
        for u in d['units']:
            unit = next((x for x in book['units'] if x['n'] == u['n']), None)
            if not unit: continue
            deck = next((k for k in unit['decks'] if k['kind'] == 'grammar'), None)
            if not deck:
                deck = {'kind': 'grammar', 'name': '', 'desc': '', 'words': []}
                pos = next((i + 1 for i, k in enumerate(unit['decks']) if k['kind'] == 'vocab'), 0); unit['decks'].insert(pos, deck)
            deck['name'] = f"U{u['n']} Grammar · {u['title']}"[:90]
            deck['desc'] = f"Unit {u['n']}: {u['title']}. " + notes_desc(u['notes'])
            deck['words'] = [entry(it) for it in u['items']]
            decks[f"tb_{d['book']}_u{u['n']}_grammar"] = {'title': u['title'], 'notes': u['notes'], 'items': u['items']}
            n_items += len(u['items'])
        report.append(f"{d['book']}: {len(d['units'])} units, {n_items} questions")
    json.dump(tb, open(TB, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'v': 1, 'decks': decks}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('\n'.join(report) or 'no grammar_data files yet'); print('grammar.json', os.path.getsize(OUT), 'bytes ·', len(decks), 'decks')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
