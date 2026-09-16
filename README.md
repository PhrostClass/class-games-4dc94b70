# Class Games

Classroom games as an installable web app for the iPad. Pure static files, no build step, no server, no accounts.
Everything the teacher creates (decks, folders, settings) is stored **on the iPad only**, inside the app's own storage.

All games share one deck library: 16 preset English-vocabulary decks plus your own decks in folders.
Import lists by pasting or from .txt / .csv / .json files, export decks, full backup/restore.
An entry can be a single word (`dog`) or a pair (`dog | perro`, also `dog<tab>perro`, `dog = perro`, `dog - perro`),
optionally with a third part (`dog | perro | 🐶`). Charades only shows the first part.

Games:

- **Charades** – act it out; timer, teams, pass, no-repeats, sounds.
- **Yahtzee** – category board: each selected deck is a column (choose how many columns and cards per column, 100–500 points,
  one colour per column shading darker as the points go up). A **turn question** (simple maths, "touch your…", Simon says,
  capital cities, or your own `question | answer` lines, `#group` = whole team answers, capped at 20%) with its own timer
  decides which team picks a card. Some cards hide a monster 👹 (eats points), a gift 🎁 or double points ✨.
- **Futaba** – 1–8 players sit around the iPad, one rotated panel each (two per side above 4); first correct tap wins the round.
  Question types: Mix (tick any of Pairs, Listen, Scramble, Gaps) or a single type. Pairs needs `word | translation` entries;
  Listen speaks the word with the best installed voice (install an Enhanced/Premium voice in iPad Settings → Accessibility →
  Spoken Content → Voices). Scoring: 2 players = +1 / −1; 3+ players = first +2, second +1 (3-second window), wrong −2;
  not answering costs nothing; negative scores allowed.
- **Memory** – pairs (2 cards) or trios (3 cards); pick how many sets are on the board; with pairs in the deck the
  cards show word / translation; otherwise the other card shows the same word, mixed-up letters or missing letters. 1–4 teams.

## Sign-in

The app asks for a username and password (checked on the device against a PBKDF2 hash in `index.html`; there is no server).
"Keep me signed in" remembers the device for 30 days; Settings → Sign out forgets it. Sign in once in Safari and let it
save the password so Face ID autofills it in the Home Screen app. To change the password, compute a new hash:
`python -c "import hashlib;print(hashlib.pbkdf2_hmac('sha256', b'user:password', b'classgames-v1', 100000, 32).hex())"`
(username lower-case) and paste it into `AUTH.hash`.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The whole app (HTML + CSS + JS in one file). |
| `sw.js` | Service worker: caches the app so it opens instantly and works offline. |
| `manifest.webmanifest` | Name, icon and "standalone" display for Add to Home Screen. |
| `icons/` | App icons (generated). |
| `deploy.ps1` | Bumps the version, commits and pushes. Use it for every update. |

## Publish on GitHub Pages (first time)

1. Create the GitHub account (students: apply for the Student Developer Pack for GitHub Pro, which allows Pages on a *private* repo).
2. In this folder, run once:
   ```powershell
   gh auth login                       # browser login
   gh repo create classgames-<random> --private --source . --push
   gh api -X POST repos/{owner}/classgames-<random>/pages -f "source[branch]=main" -f "source[path]=/"
   ```
   Pick an unguessable repo name: the URL becomes `https://<user>.github.io/<repo>/` and that is the only thing protecting it.
   If the account is a free one, use `--public` instead (Pages on a private repo needs Pro).
3. Wait about a minute, then open the URL on the iPad in **Safari** → Share → **Add to Home Screen**.

## Updates

```powershell
.\deploy.ps1 "added a new game"
```

On the iPad the new version downloads in the background; close the app fully (swipe it away) and reopen it.

## Privacy notes

- The published site only contains the game and the preset decks. Your own decks never leave the iPad.
- Add to Home Screen creates a separate storage area from Safari, so data added in the app is not visible in Safari and vice versa.
- Deleting the app from the Home Screen deletes its data. Use **Settings → Export backup** first.
- For a real login gate, host on Cloudflare Pages instead and put Cloudflare Access (free, email one-time-PIN) in front of it.

## Developer notes

- `index.html?selftest=1` runs the built-in unit tests (word parsing, import detection, backup merge, game engine).
- `index.html?demo=word|ready|roundEnd|over|buzz|buzzq|buzzcard|futaba|futaba2|futaba3|memory` opens a game screen directly for screenshots; `?dev=1` skips the sign-in for screenshots. Both also skip the lock (the lock is client-side anyway).
- Local preview: `python -m http.server 8765` in this folder, then <http://127.0.0.1:8765/>.
