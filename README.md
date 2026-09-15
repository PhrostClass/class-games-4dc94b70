# Class Games

Classroom games as an installable web app for the iPad. Pure static files, no build step, no server, no accounts.
Everything the teacher creates (decks, folders, settings) is stored **on the iPad only**, inside the app's own storage.

Games so far:

- **Charades** – preset decks (16 English-vocabulary sets) plus your own decks, organised in folders.
  Import lists by pasting or from .txt / .csv / .json files, export decks, full backup/restore, teams, timer, pass, sounds.

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
- `index.html?demo=word|ready|roundEnd|over` opens a game screen directly for screenshots.
- Local preview: `python -m http.server 8765` in this folder, then <http://127.0.0.1:8765/>.
