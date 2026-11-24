# Don't let this be your Deathwish – Website

Every change on `main` publishes the site automatically via GitHub Actions (takes about a minute).

## Editing on your phone (GitHub app or browser)

| What | File |
|---|---|
| Termine (shows) | [`content/shows.yml`](content/shows.yml) |
| Musik (releases) | [`content/releases.yml`](content/releases.yml) |
| Links in the footer | [`content/links.yml`](content/links.yml) |
| Name and e-mail for Impressum/Datenschutz | [`content/legal.yml`](content/legal.yml) |
| Images, cover art | [`static/`](static/) |

1. Open the file and tap the pencil icon (Edit).
2. Copy an existing block and change the values. The comments at the top of each file explain every field.
3. Commit directly to `main`.
4. Check the **Actions** tab: green means the site is live. Red means a typo; the run shows which file and entry, e.g. `content/shows.yml: show 3: unknown canceled`. Fix it and commit again. The site stays on the last good version until then.

YAML tips: indentation matters (two spaces, no tabs); put text in `"quotes"`; dates go without quotes (`date: 2026-12-05`).

Past shows don't need to be deleted: the page moves them to "Vergangene Termine" on its own.

New cover image: upload it to `static/` (Add file → Upload files), then reference it in `releases.yml` with `cover: "filename.webp"` and its pixel width as `cover_size`.

## On a computer

Needs [uv](https://docs.astral.sh/uv/).

    ./build.py           # builds into _site/
    ./serve.py           # preview on http://localhost:8000, reloads on every save

## Setup (once)

Repository settings → Pages → Source: **GitHub Actions**.
