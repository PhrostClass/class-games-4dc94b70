"""Shared by build_images.py and build_audio.py: the vocabulary of every built-in deck, and the key normalisation
that index.html uses too (mediaKey)."""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, '..')
PAIR_SEP = re.compile(r'\s*\|\s*|\t+|\s+=\s+|\s+[-–—]\s+|\s+:\s+')

def media_key(term):
    """lower case, no trailing bracket such as (v.) or (sth/sb), single spaces  — keep identical to mediaKey() in index.html"""
    t = re.sub(r'\s*\([^)]*\)\s*$', '', str(term).strip().lower())
    return re.sub(r'\s+', ' ', t).strip()

def first_part(entry):
    return PAIR_SEP.split(entry)[0].strip()

def all_terms():
    """-> list of (key, kind) with kind in vocab|verbs|preset|pet, unique by key, in a stable order"""
    out, seen = [], set()
    def add(term, kind):
        k = media_key(term)
        if k and k not in seen and len(k) <= 60: seen.add(k); out.append((k, kind))
    html = open(os.path.join(APP, 'index.html'), encoding='utf-8').read()
    block = html[html.index('const PRESET_DECKS = ['):html.index('const PRESET_FOLDER')]
    for words in re.findall(r"words: \[(.*?)\] \}", block):
        for w in re.findall(r"'((?:[^'\\]|\\.)*)'", words): add(w.replace("\\'", "'"), 'preset')
    tb = json.load(open(os.path.join(APP, 'textbooks.json'), encoding='utf-8'))
    for b in tb['books']:
        for u in b['units']:
            for d in u['decks']:
                if d['kind'] == 'vocab':
                    for w in d['words']: add(first_part(w), 'vocab')
                elif d['kind'] == 'verbs':
                    for w in d['words']:
                        for form in PAIR_SEP.split(w): add(form, 'verbs')
    pet = json.load(open(os.path.join(APP, 'pet.json'), encoding='utf-8'))
    for v in pet['vocab']: add(v['w'], 'pet')
    return out
