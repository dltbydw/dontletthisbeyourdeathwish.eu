#!/usr/bin/env -S uv run --locked --quiet
"""Renders the band site from content/*.yml, templates/ and static/ into _site/.
GitHub Actions runs it on every push; ./serve.py previews locally.

Dependencies: pyproject.toml, pinned in uv.lock.
"""

import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).resolve().parent
CONTENT = HERE / "content"
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"
SITE = HERE / "_site"
# template in templates/ -> page in SITE; all get the same data
PAGES = {
    "index.html.j2": "index.html",
    "impressum.html.j2": "impressum.html",
}

# own tables instead of the locale: the build machine's locale needn't be German
WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]


class ContentError(Exception):
    def __init__(self, file, message):
        super().__init__(f"content/{file}: {message}")
        self.file = file
        self.message = message


def check_keys(file, where, entry, required, optional=()):
    """Typos like canceled would otherwise be ignored silently."""
    missing = [k for k in required if k not in entry]
    unknown = [k for k in entry if k not in required and k not in optional]
    if missing:
        raise ContentError(file, f"{where}: missing {', '.join(missing)}")
    if unknown:
        raise ContentError(file, f"{where}: unknown {', '.join(unknown)}")


def load(file, kind):
    """kind list: a list of entries (an empty file is an empty list);
    kind dict: key: value pairs at the top."""
    try:
        with open(CONTENT / file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ContentError(file, "file is missing") from None
    except yaml.YAMLError as e:
        raise ContentError(file, str(e)) from None
    if data is None and kind is list:
        return []
    if not isinstance(data, kind):
        shape = "a list of entries starting with -" if kind is list else "key: value lines"
        raise ContentError(file, f"must be {shape}")
    if kind is list:
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                raise ContentError(file, f"entry {i + 1}: must be key: value lines")
    return data


def text(file, where, entry, *keys):
    """YAML turns unquoted 2024 or yes into a number or true; quotes keep text text."""
    for k in keys:
        if k in entry and not isinstance(entry[k], str):
            raise ContentError(file, f'{where}: put {k} in quotes, like {k}: "..."')


def show(i, s):
    file, where = "shows.yml", f"show {i + 1}"
    check_keys(file, where, s, ["date", "city", "venue"], ["url", "cancelled"])
    text(file, where, s, "city", "venue", "url")
    d = s["date"]
    # a YAML date, not a string and not a date with time
    if type(d) is not date:
        raise ContentError(file, f"{where}: date must be a date like 2026-12-05, without quotes")
    return {
        "date": d,
        # with year: the list can reach into next year, and past shows span years
        "label": f"{WEEKDAYS[d.weekday()]} {d:%d.%m.%y}",
        "city": s["city"],
        "venue": s["venue"],
        "url": s.get("url"),
        "cancelled": s.get("cancelled", False),
    }


def link(file, where, entry):
    check_keys(file, where, entry, ["name", "url"])
    text(file, where, entry, "name", "url")
    return entry


def release(i, r):
    file, where = "releases.yml", f"release {i + 1}"
    check_keys(file, where, r, ["title"], ["lang", "cover", "cover_size", "released",
                                           "note", "note_lang", "links", "bandcamp_album"])
    text(file, where, r, "title", "lang", "cover", "released", "note", "note_lang")
    if not isinstance(r.get("links", []), list):
        raise ContentError(file, f"{where}: links must be a list of name and url")
    if "cover" in r:
        if "cover_size" not in r:
            raise ContentError(file, f"{where}: cover needs cover_size")
        if not (STATIC / r["cover"]).is_file():
            raise ContentError(file, f"{where}: static/{r['cover']} doesn't exist")
    released = r.get("released")
    if released is not None:
        m = re.fullmatch(r"(\d{4})-(0[1-9]|1[0-2])", released)
        if not m:
            raise ContentError(file, f"{where}: released must look like \"2025-01\"")
        released = {"iso": released,
                    "label": f"{MONTHS[int(m[2]) - 1]} {m[1]}"}
    album = r.get("bandcamp_album")
    # bool is an int too; true would end up in the player URL as "True"
    if album is not None and (type(album) is not int or album <= 0):
        raise ContentError(file, f"{where}: bandcamp_album must be a number like 4064552867")
    return {
        "title": r["title"],
        "lang": r.get("lang"),
        "cover": r.get("cover"),
        "cover_size": r.get("cover_size"),
        "released": released,
        "note": r.get("note"),
        "note_lang": r.get("note_lang"),
        "links": [link(file, f"{where}, link {j + 1}", l)
                  for j, l in enumerate(r.get("links", []))],
        "bandcamp_album": album,
    }


def render():
    """Returns {page name: html} for all pages."""
    shows = load("shows.yml", list)
    releases = load("releases.yml", list)
    links = load("links.yml", list)
    legal = load("legal.yml", dict)
    check_keys("legal.yml", "top level", legal, ["name", "email"])
    text("legal.yml", "top level", legal, "name", "email")

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        # venue names and URLs with & or < end up escaped in the HTML
        autoescape=True,
        # a misspelled variable in the template fails instead of rendering empty
        undefined=StrictUndefined,
        # block tags on their own line leave no empty lines and no indentation behind
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    data = {
        "shows": sorted((show(i, s) for i, s in enumerate(shows)),
                        key=lambda s: s["date"]),
        "releases": [release(i, r) for i, r in enumerate(releases)],
        "links": [link("links.yml", f"link {i + 1}", l) for i, l in enumerate(links)],
        "legal": legal,
    }
    return {page: env.get_template(template).render(data)
            for template, page in PAGES.items()}


def build():
    """Renders first, so an error leaves the previous _site/ untouched."""
    pages = render()
    shutil.rmtree(SITE, ignore_errors=True)
    shutil.copytree(STATIC, SITE)
    for page, html in pages.items():
        (SITE / page).write_text(html, encoding="utf-8")
    print(f"built {SITE}")



def main():
    try:
        build()
    except ContentError as e:
        if os.environ.get("GITHUB_ACTIONS"):
            # shows up as a red box on the run's summary page, also in GitHub mobile
            print(f"::error file=content/{e.file},title=Fehler in content/{e.file}::{e.message}")
        sys.exit(str(e))


if __name__ == "__main__":
    main()
