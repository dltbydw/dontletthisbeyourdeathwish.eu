# Notes for Claude: the dltbydw band site

Sources: `content/*.yml` (data, edited by the band via GitHub mobile), `templates/*.j2`, `static/` (copied as-is). `build.py` renders everything into `_site/` (gitignored), `serve.py` previews it with live reload; `.github/workflows/pages.yml` builds and deploys it to GitHub Pages on every push to `main`. Never put notes into `static/`: all of it is published.

Content files are edited by non-developers on a phone: keep the field comments at the top of each YAML file accurate, and keep build.py's error messages naming the file and entry (in Actions they become `::error` annotations).

## Comments

Shipped files carry no explanatory comments; only the Special Elite license comment in `style.css` and the generated-file marker in the HTML stay. Explanations go into Jinja comments in the templates or into this file.

Jinja comments only between elements, never inside `<script>` or `<style>`: there they break the editor's (Helix) highlighting. Comments for the script sit in one Jinja comment above `<script>`.

## Impressum

`templates/impressum.html.j2`: the Impressum section and the hosting paragraph of the Datenschutz text are placeholders.


Static, edited by hand, not generated; shared by all pages. What isn't obvious from the rules:

- Sepia toggle (`class="sepia"` on `<html>`, `--sepia` 0 = off, 1 = full): a transparent fixed layer (`.sepia body::before`) tints everything behind it with `backdrop-filter`. Elements with a higher z-index lie above it and keep their colors: the red band name on hover (`.bandname:hover`) and the `.sepia-toggle` button. A plain `filter` on `body` can't leave anything out, children can't escape a parent's filter.
- `.sepia-toggle` floats in the bottom right corner while scrolling; its half-transparent black background keeps it readable over text and the photo.
- Hero background anchored at the top: on screens wider than 4:3 the crop takes the ground, not the sky.
- Every screen (hero, sections, footer) is a flex column at least `100svh` tall, so `.section-nav` with `margin-top: auto` sits at the bottom, at the same spot on every screen. The Impressum line below the footer's nav is positioned absolutely in the footer's bottom padding, so it doesn't push the nav up.
- Sections get their side gutter from `main`; the footer sits outside `main` and brings its own.
- Section `h2`s link to themselves, for sharing a section.
- Cancelled (`.cancelled`): the show is struck through, the "abgesagt" label isn't. It stays that way under "Vergangene Termine".
- `.releases` is centered as a block, so the covers line up on the left.
- `.bandcamp` (click-to-load player) has a fixed width from the start, so the release column doesn't jump when the iframe replaces the button. The iframe stays below the sepia layer and gets tinted like the rest.
- Release titles are `h3` for structure but look like body text.
- `.bandname`: plain spelling by default, the stylized one in red on hover.
- `.imprint` (body class of `impressum.html`) scopes that page's rules: a plain text page, no full-screen sections, headings on the left instead of the centered `h2` of the main page.
