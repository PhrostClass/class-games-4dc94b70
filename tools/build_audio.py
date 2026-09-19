"""Natural voices for the app: every built-in word and sentence is recorded once with the Kokoro neural TTS
(open model, Apache 2.0, runs locally: tools/tts_models/, not in the repo) and shipped as small mp3 files, so the iPad's
robotic system voice is only a fallback for the teacher's own decks.
Output: ../audio/<key>.mp3 and ../audio/index.json {"keys": "<16 hex chars per clip, concatenated>"}.
Clip key = two FNV-1a hashes of "<voice>|<rate>|<normalised text>"  (voice F, M or ES; rate 1 or s = slow) — same as
clipKey() in index.html.  Incremental.  usage: python build_audio.py [words|pet|names|all]
"""
import json, os, re, subprocess, sys, time
import numpy as np
from media_terms import all_terms, APP, ROOT

OUT = os.path.join(APP, 'audio')
VOICES = {'F': ('bf_emma', 'en-gb'), 'M': ('bm_george', 'en-gb'), 'ES': ('ef_dora', 'es')}
SPEED = {'1': 1.0, 's': 0.78}

def norm(text): return re.sub(r'\s+', ' ', str(text).strip().lower())
def fnv(data, basis):
    h = basis
    for b in data: h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h
def clip_key(voice, rate, text):
    d = f'{voice}|{rate}|{norm(text)}'.encode('utf-8')
    return '%08x%08x' % (fnv(d, 0x811C9DC5), fnv(d, 0x050C5D1F))

def spoken(text):
    """what the voice actually says: no brackets, slashes read as commas"""
    t = re.sub(r'\([^)]*\)', ' ', text); t = re.sub(r'\s*/\s*', ', ', t)
    return re.sub(r'\s+', ' ', t).strip(' ,')

def jobs(which):
    out = []
    if which in ('words', 'all'):
        for term, kind in all_terms(): out.append(('F', '1', term))
    if which in ('pet', 'all'):
        pet = json.load(open(os.path.join(APP, 'pet.json'), encoding='utf-8'))
        for ex in pet['listening']:
            for ln in (ex.get('script') or []) + [l for it in ex['items'] for l in (it.get('script') or [])]:
                for r in ('1', 's'): out.append((ln['v'] if ln['v'] in ('F', 'M') else 'F', r, ln['t']))
        for i, v in enumerate(pet['vocab']):
            out.append(('F', '1', v['ex_en'])); out.append(('F', 's', v['ex_en'])); out.append(('M', '1', v['ex_en']))
    if which in ('names', 'all'):
        html = open(os.path.join(APP, 'index.html'), encoding='utf-8').read()
        seed = html[html.index('const Q_SEED'):html.index('function qSeed')]
        names = set(re.findall(r"'([^']+)'", ' '.join(re.findall(r'students: \[(.*?)\]', seed)))) | set(re.findall(r"'([^']+)'", re.search(r'const HOME_STUDENTS = \[(.*?)\]', html).group(1)))
        for n in sorted(names): out.append(('ES', '1', n))
    seen, uniq = set(), []
    for j in out:
        k = clip_key(*j)
        if k not in seen: seen.add(k); uniq.append(j + (k,))
    return uniq

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    os.makedirs(OUT, exist_ok=True)
    todo = [j for j in jobs(which) if not os.path.exists(os.path.join(OUT, j[3] + '.mp3'))]
    print(f'{len(todo)} clips to record', flush=True)
    if todo:
        from kokoro_onnx import Kokoro
        k = Kokoro(os.path.join(ROOT, 'tts_models', 'kokoro-v1.0.onnx'), os.path.join(ROOT, 'tts_models', 'voices-v1.0.bin'))
        t0 = time.time(); secs = 0
        for n, (voice, rate, text, key) in enumerate(todo, 1):
            say = spoken(text)
            if not say: continue
            if len(say.split()) == 1 and voice != 'ES': say = say[0].upper() + say[1:] + '.'     # a full stop gives single words a natural falling tone
            try:
                a, sr = k.create(say, voice=VOICES[voice][0], speed=SPEED[rate], lang=VOICES[voice][1])
            except Exception as e:
                print('FAILED', repr(text), e, flush=True); continue
            a = a.astype(np.float32); peak = float(np.max(np.abs(a))) or 1.0; a = a * (0.89 / peak)   # same loudness for every clip
            a = np.concatenate([np.zeros(int(sr * 0.06), dtype=np.float32), a.astype(np.float32), np.zeros(int(sr * 0.12), dtype=np.float32)])
            pcm = (np.clip(a, -1, 1) * 32767).astype('<i2').tobytes(); secs += len(a) / sr
            p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(sr), '-ac', '1', '-i', 'pipe:0', '-ar', '24000', '-b:a', '32k', os.path.join(OUT, key + '.mp3')], input=pcm)
            if p.returncode: print('ffmpeg failed for', repr(text), flush=True)
            if n % 100 == 0: print(f'{n}/{len(todo)} · {secs / 60:.1f} min of audio · {time.time() - t0:.0f} s', flush=True)
    keys = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith('.mp3'))
    json.dump({'keys': ''.join(keys)}, open(os.path.join(OUT, 'index.json'), 'w'))
    size = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f'DONE {len(keys)} clips, {size // 1024} KB', flush=True)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
