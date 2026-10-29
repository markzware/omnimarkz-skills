#!/usr/bin/env python3
"""WordPress REST helper for the design-file-to-wordpress skill.

Reads the application password from a local file. Never prints the password
or the Authorization header.
"""

from __future__ import annotations

import argparse
import base64
import copy
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

CONFIG = Path.home() / ".config" / "design-file-to-wordpress" / "config.json"
USER_AGENT = "Mozilla/5.0"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def load_config() -> dict:
    if not CONFIG.is_file():
        fail(f"No config at {CONFIG}. Run: wp.py test --site URL --username LOGIN --password-file PATH --save")
    try:
        data = json.loads(CONFIG.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Config is not valid JSON: {exc}")
    for key in ("site_url", "username", "password_file"):
        if not data.get(key):
            fail(f"Config is missing {key}")
    return data


def site_url(value: str) -> str:
    url = value.strip().rstrip("/")
    if not url.startswith("https://"):
        fail("Site URL must start with https://")
    return url


def read_password(path: str) -> str:
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        fail(f"Password file not found: {file_path}")
    password = "".join(file_path.read_text().split())
    if not password:
        fail("Password file is empty")
    return password


def request(method: str, url: str, username: str, password: str, data: bytes | None = None, headers: dict | None = None):
    header_values = {
        "Authorization": "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode(),
        "User-Agent": USER_AGENT,
    }
    if headers:
        header_values.update(headers)
    req = urllib.request.Request(url, data=data, headers=header_values, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        fail(f"HTTP {exc.code} {method} {url}\n{body}")
    except urllib.error.URLError as exc:
        fail(f"Could not reach {url}: {exc.reason}")


def raw_field(value) -> str:
    if isinstance(value, dict):
        return value.get("raw") or ""
    return value or ""


def command_test(args: argparse.Namespace) -> None:
    if args.site or args.username or args.password_file:
        if not (args.site and args.username and args.password_file):
            fail("test with new details needs --site, --username, and --password-file")
        config = {
            "site_url": site_url(args.site),
            "username": args.username.strip(),
            "password_file": str(Path(args.password_file).expanduser()),
        }
    else:
        config = load_config()
    password = read_password(config["password_file"])
    status, body = request(
        "GET",
        config["site_url"] + "/wp-json/wp/v2/users/me",
        config["username"],
        password,
    )
    user = json.loads(body.decode())
    if args.save:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(config, indent=2) + "\n")
        print(f"saved {CONFIG}")
    print(json.dumps({
        "ok": True,
        "http_status": status,
        "id": user.get("id"),
        "username": user.get("slug") or user.get("username"),
        "name": user.get("name"),
    }))


def media_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    fail("Upload a .jpg or .png image")


def command_upload(args: argparse.Namespace) -> None:
    config = load_config()
    password = read_password(config["password_file"])
    image = Path(args.file).expanduser()
    if not image.is_file():
        fail(f"Image not found: {image}")
    filename = args.filename or image.name
    content_type = media_content_type(image)
    status, body = request(
        "POST",
        config["site_url"] + "/wp-json/wp/v2/media",
        config["username"],
        password,
        data=image.read_bytes(),
        headers={
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
    created = json.loads(body.decode())
    media_id = created["id"]
    fields = {"title": args.title or filename}
    if args.alt:
        fields["alt_text"] = args.alt
    if args.caption:
        fields["caption"] = args.caption
    if args.description:
        fields["description"] = args.description
    request(
        "POST",
        f"{config['site_url']}/wp-json/wp/v2/media/{media_id}",
        config["username"],
        password,
        data=json.dumps(fields).encode(),
        headers={"Content-Type": "application/json"},
    )
    _, checked_body = request(
        "GET",
        f"{config['site_url']}/wp-json/wp/v2/media/{media_id}?context=edit",
        config["username"],
        password,
    )
    checked = json.loads(checked_body.decode())
    print(json.dumps({
        "id": media_id,
        "http_status": status,
        "source_url": checked.get("source_url") or created.get("source_url"),
        "alt_text": checked.get("alt_text") or "",
        "caption": raw_field(checked.get("caption")),
        "description": raw_field(checked.get("description")),
    }))


def command_create_post(args: argparse.Namespace) -> None:
    config = load_config()
    password = read_password(config["password_file"])
    content_path = Path(args.content_file).expanduser()
    if not content_path.is_file():
        fail(f"Content file not found: {content_path}")
    content = content_path.read_text()
    payload = {
        "title": args.title,
        "content": content,
        "status": "draft",
    }
    if args.slug:
        payload["slug"] = args.slug
    if args.excerpt:
        payload["excerpt"] = args.excerpt
    if args.featured:
        payload["featured_media"] = args.featured
    status, body = request(
        "POST",
        config["site_url"] + "/wp-json/wp/v2/posts",
        config["username"],
        password,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    created = json.loads(body.decode())
    post_id = created["id"]
    _, checked_body = request(
        "GET",
        f"{config['site_url']}/wp-json/wp/v2/posts/{post_id}?context=edit",
        config["username"],
        password,
    )
    checked = json.loads(checked_body.decode())
    raw = checked.get("content", {})
    raw_content = raw.get("raw", "") if isinstance(raw, dict) else ""
    print(json.dumps({
        "id": post_id,
        "http_status": status,
        "status": checked.get("status"),
        "link": checked.get("link") or created.get("link"),
        "featured_media": checked.get("featured_media"),
        "content_match": len(raw_content) == len(content),
        "content_length": len(raw_content),
    }))


METADATA_URL = "https://fonts.google.com/metadata/fonts"
CSS2_URL = "https://fonts.googleapis.com/css2"
CSS_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
FACE_WORDS = {
    "regular", "roman", "book", "bold", "italic", "oblique", "light", "medium",
    "semibold", "demibold", "demi", "black", "heavy",
}
FACE_WEIGHT = {
    "bold": 700,
    "semibold": 600,
    "demibold": 600,
    "demi": 600,
    "black": 900,
    "heavy": 900,
    "medium": 500,
    "light": 300,
    "regular": 400,
    "roman": 400,
    "book": 400,
}
FACE_SUFFIXES = (
    ("bolditalic", 700, True),
    ("boldoblique", 700, True),
    ("demibold", 600, False),
    ("semibold", 600, False),
    ("oblique", 400, True),
    ("regular", 400, False),
    ("medium", 500, False),
    ("italic", 400, True),
    ("roman", 400, False),
    ("heavy", 900, False),
    ("light", 300, False),
    ("black", 900, False),
    ("bold", 700, False),
    ("demi", 600, False),
    ("book", 400, False),
)
SUBSTITUTES = {
    "times": ("Tinos", "serif", "metric"),
    "timesnewroman": ("Tinos", "serif", "metric"),
    "timesnewromanps": ("Tinos", "serif", "metric"),
    "timesnewromanpsmt": ("Tinos", "serif", "metric"),
    "georgia": ("Gelasio", "serif", "metric"),
    "arial": ("Arimo", "sans-serif", "metric"),
    "arialmt": ("Arimo", "sans-serif", "metric"),
    "helvetica": ("Arimo", "sans-serif", "metric"),
    "helveticanue": ("Arimo", "sans-serif", "metric"),
    "helveticaneue": ("Arimo", "sans-serif", "metric"),
    "calibri": ("Carlito", "sans-serif", "metric"),
    "cambria": ("Caladea", "serif", "metric"),
    "courier": ("Cousine", "monospace", "metric"),
    "couriernew": ("Cousine", "monospace", "metric"),
    "palatino": ("EB Garamond", "serif", "approximate"),
    "palatinolinotype": ("EB Garamond", "serif", "approximate"),
    "bookantiqua": ("EB Garamond", "serif", "approximate"),
    "garamond": ("EB Garamond", "serif", "approximate"),
    "adobegaramond": ("EB Garamond", "serif", "approximate"),
    "garamondpremier": ("EB Garamond", "serif", "approximate"),
    "minion": ("EB Garamond", "serif", "approximate"),
    "minionpro": ("EB Garamond", "serif", "approximate"),
    "caslon": ("Libre Caslon Text", "serif", "approximate"),
    "adobecaslon": ("Libre Caslon Text", "serif", "approximate"),
    "baskerville": ("Libre Baskerville", "serif", "approximate"),
    "baskervilleoldface": ("Libre Baskerville", "serif", "approximate"),
    "itcbaskerville": ("Libre Baskerville", "serif", "approximate"),
    "bodoni": ("Bodoni Moda", "serif", "approximate"),
    "bodonimt": ("Bodoni Moda", "serif", "approximate"),
    "didot": ("Bodoni Moda", "serif", "approximate"),
    "verdana": ("Open Sans", "sans-serif", "approximate"),
    "tahoma": ("Noto Sans", "sans-serif", "approximate"),
    "candara": ("Nunito Sans", "sans-serif", "approximate"),
    "trebuchet": ("Mulish", "sans-serif", "approximate"),
    "trebuchetms": ("Mulish", "sans-serif", "approximate"),
    "segoeui": ("Open Sans", "sans-serif", "approximate"),
    "impact": ("Anton", "sans-serif", "approximate"),
    "comicsans": ("Comic Neue", "cursive", "approximate"),
    "comicsansms": ("Comic Neue", "cursive", "approximate"),
    "futura": ("Jost", "sans-serif", "approximate"),
    "futurapt": ("Jost", "sans-serif", "approximate"),
    "futurastd": ("Jost", "sans-serif", "approximate"),
    "gillsans": ("Cabin", "sans-serif", "approximate"),
    "gillsansmt": ("Cabin", "sans-serif", "approximate"),
    "myriad": ("Source Sans 3", "sans-serif", "approximate"),
    "myriadpro": ("Source Sans 3", "sans-serif", "approximate"),
    "frutiger": ("Source Sans 3", "sans-serif", "approximate"),
    "frutigernext": ("Source Sans 3", "sans-serif", "approximate"),
    "univers": ("Roboto", "sans-serif", "approximate"),
    "franklingothic": ("Libre Franklin", "sans-serif", "approximate"),
    "itcfranklingothic": ("Libre Franklin", "sans-serif", "approximate"),
    "gotham": ("Montserrat", "sans-serif", "approximate"),
    "proximanova": ("Montserrat", "sans-serif", "approximate"),
    "avenir": ("Nunito Sans", "sans-serif", "approximate"),
    "avenirnext": ("Nunito Sans", "sans-serif", "approximate"),
    "optima": ("Philosopher", "sans-serif", "approximate"),
    "rockwell": ("Roboto Slab", "serif", "approximate"),
}
SYMBOLS = {"wingdings", "webdings", "symbol", "zapfdingbats"}
CATEGORY_GENERIC = {
    "serif": "serif",
    "sans serif": "sans-serif",
    "monospace": "monospace",
    "display": "sans-serif",
    "handwriting": "cursive",
}


def normalize_family(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch not in " -_")


def strip_subset_tag(name: str) -> str:
    return re.sub(r"^[A-Za-z]{6}\+", "", name, count=1)


def strip_mt(name: str) -> str:
    parts = name.split()
    if parts and parts[-1].lower() == "mt":
        return " ".join(parts[:-1])
    if len(name) > 2 and name.endswith("MT"):
        return name[:-2]
    return name


def known_family(name: str, catalog: dict | None) -> bool:
    key = normalize_family(name)
    if not key:
        return False
    if key in SUBSTITUTES or key in SYMBOLS or "dingbat" in key:
        return True
    return catalog is not None and key in catalog


def strip_face_words(family: str, catalog: dict | None) -> tuple[str, list[str]]:
    """Keep a trailing word such as Roman when the whole name is already a match."""
    current = family
    removed: list[str] = []
    while len(removed) < 2 and not known_family(current, catalog):
        parts = current.split()
        if not parts or parts[-1].lower() not in FACE_WORDS:
            break
        removed.append(parts.pop())
        current = " ".join(parts)
    removed.reverse()
    return current, removed


def strip_face_suffix(name: str) -> tuple[str, int | None, bool]:
    lowered = name.lower()
    for suffix, weight, italic in FACE_SUFFIXES:
        token = "-" + suffix
        if lowered.endswith(token):
            return name[: -len(token)], weight, italic
    return name, None, False


def family_stack(web_font: str, generic: str) -> str:
    return f'"{web_font}", {generic}'


def optional_int(value) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def clean_font_names(font: dict, catalog: dict | None) -> tuple[str, str, str, int | None, bool]:
    """Return source label, match name, postscript, name-weight, name-italic."""
    original_family = font.get("family") if isinstance(font.get("family"), str) else ""
    original_ps = font.get("postscriptName") if isinstance(font.get("postscriptName"), str) else ""
    source = original_family or original_ps
    family = strip_mt(strip_subset_tag(original_family)) if original_family else ""
    postscript = strip_mt(strip_subset_tag(original_ps)) if original_ps else ""
    name_weight = None
    name_italic = False
    if postscript:
        _, suffix_weight, suffix_italic = strip_face_suffix(postscript)
        if suffix_weight is not None:
            name_weight = suffix_weight
        name_italic = suffix_italic or name_italic
        if "italic" in postscript.lower() or "oblique" in postscript.lower():
            name_italic = True
    match_name = family
    if family:
        match_name, removed = strip_face_words(family, catalog)
        for word in removed:
            low = word.lower()
            if low in ("italic", "oblique"):
                name_italic = True
            elif low in FACE_WEIGHT:
                name_weight = FACE_WEIGHT[low]
    else:
        match_name, _, _ = strip_face_suffix(postscript)
    return source, match_name, original_ps, name_weight, name_italic


def snap_weight(weight: int, italic: bool, face_keys: list[str]) -> tuple[int, bool, bool]:
    if not face_keys:
        return weight, italic, False
    italic_keys = [key for key in face_keys if key.endswith("i")]
    roman_keys = [key for key in face_keys if not key.endswith("i")]
    unavailable = False
    keys = italic_keys if italic else roman_keys
    use_italic = italic
    if italic and not italic_keys:
        keys = roman_keys
        use_italic = False
        unavailable = True
    numbers = []
    for key in keys:
        bare = key[:-1] if key.endswith("i") else key
        if bare.isdigit():
            numbers.append(int(bare))
    if not numbers:
        return weight, use_italic, unavailable
    if weight in numbers:
        return weight, use_italic, unavailable
    # 600 sits between the common 400 and 700 pair. The ticket locks that case to 400.
    if weight == 600 and 400 in numbers and 700 in numbers and 600 not in numbers:
        return 400, use_italic, unavailable
    chosen = min(numbers, key=lambda number: (abs(number - weight), number))
    return chosen, use_italic, unavailable


def load_google_catalog() -> dict:
    request = urllib.request.Request(METADATA_URL, headers={"User-Agent": CSS_USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
    if raw.startswith(")]}'"):
        raw = raw[raw.find("\n") + 1 :]
    payload = json.loads(raw)
    catalog = {}
    for family in payload.get("familyMetadataList") or []:
        name = family.get("family") or ""
        if not name:
            continue
        catalog[normalize_family(name)] = {
            "family": name,
            "category": family.get("category") or "",
            "faces": list((family.get("fonts") or {}).keys()),
        }
    return catalog


def match_family(match_name: str, catalog: dict | None, catalog_failed: bool) -> dict:
    key = normalize_family(match_name)
    if catalog is not None and key in catalog:
        entry = catalog[key]
        generic = CATEGORY_GENERIC.get(entry["category"].strip().lower(), "sans-serif")
        return {
            "web": entry["family"],
            "generic": generic,
            "kind": "exact",
            "faces": entry["faces"],
        }
    if key in SUBSTITUTES:
        web, generic, kind = SUBSTITUTES[key]
        faces: list[str] = []
        if catalog is not None:
            known = catalog.get(normalize_family(web))
            if known:
                faces = known["faces"]
        return {"web": web, "generic": generic, "kind": kind, "faces": faces}
    if key in SYMBOLS or "dingbat" in key:
        return {"web": None, "generic": None, "kind": "symbol", "faces": []}
    return {"web": None, "generic": None, "kind": "none", "faces": []}


def iter_runs(node) -> list[dict]:
    found: list[dict] = []

    def walk(value) -> None:
        if isinstance(value, dict):
            runs = value.get("runs")
            if isinstance(runs, list):
                for run in runs:
                    if isinstance(run, dict):
                        found.append(run)
            for child_key, child in value.items():
                if child_key != "runs":
                    walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(node)
    return found


def font_records(document: dict) -> tuple[dict, bool]:
    resources = document.get("resources") if isinstance(document, dict) else None
    if not isinstance(resources, dict) or "fonts" not in resources:
        return {}, True
    fonts = resources.get("fonts")
    if not isinstance(fonts, dict):
        return {}, True
    return fonts, len(fonts) == 0


def resolve_face(font: dict, run: dict, catalog: dict | None, catalog_failed: bool) -> dict:
    source, match_name, postscript, name_weight, name_italic = clean_font_names(font, catalog)
    weight = name_weight if name_weight is not None else 400
    if "fontWeight" in run:
        numbered = optional_int(run.get("fontWeight"))
        if numbered is not None:
            weight = numbered
    if "fontStyle" in run and run.get("fontStyle") is not None:
        italic = str(run.get("fontStyle")).lower() in {"italic", "oblique"}
    else:
        italic = name_italic
    requested = weight
    matched = match_family(match_name, catalog, catalog_failed)
    used = weight
    italic_unavailable = False
    if matched["web"]:
        used, italic, italic_unavailable = snap_weight(weight, italic, matched["faces"])
    return {
        "source": source,
        "postscript": postscript,
        "web": matched["web"],
        "generic": matched["generic"],
        "kind": matched["kind"],
        "requested": requested,
        "weight": used,
        "italic": italic,
        "italic_unavailable": italic_unavailable,
        "stack": family_stack(matched["web"], matched["generic"]) if matched["web"] else None,
    }


def collect_faces(data: dict, catalog: dict | None, catalog_failed: bool) -> tuple[list[dict], str | None]:
    document = data.get("document") if isinstance(data.get("document"), dict) else data
    fonts, empty = font_records(document if isinstance(document, dict) else {})
    runs = iter_runs(document)
    resolved = []
    for run in runs:
        ref = run.get("fontRef")
        font = fonts.get(ref) if isinstance(ref, str) else None
        if not isinstance(font, dict):
            continue
        resolved.append(resolve_face(font, run, catalog, catalog_failed))
    if resolved:
        return resolved, None
    if empty or not fonts:
        return [], "no fonts were listed"
    if len(fonts) == 1:
        only = next(iter(fonts.values()))
        if isinstance(only, dict):
            return [resolve_face(only, {}, catalog, catalog_failed)], None
    faces = []
    for font in fonts.values():
        if isinstance(font, dict):
            faces.append(resolve_face(font, {}, catalog, catalog_failed))
    return faces, "The file did not say which text uses which font."


def format_face_line(face: dict) -> str:
    if not face["web"]:
        return f"{face['source']} → no web font"
    italic = "yes" if face["italic"] else "no"
    line = (
        f"{face['source']} → {face['web']}, {face['generic']}, {face['kind']}, "
        f"weight {face['weight']}, italic {italic}"
    )
    if face["requested"] != face["weight"]:
        line += f", requested {face['requested']}, nearest weight {face['weight']}"
    if face["italic_unavailable"]:
        line += ", italic was not available"
    if face["postscript"] and face["source"] != face["postscript"]:
        line += f", postscript {face['postscript']}"
    return line


def command_map_fonts(args: argparse.Namespace) -> None:
    path = Path(args.mzjson).expanduser()
    if not path.is_file():
        fail(f"MZJSON not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"MZJSON is not valid JSON: {exc}")
    catalog = None
    catalog_failed = bool(args.offline)
    if not args.offline:
        try:
            catalog = load_google_catalog()
        except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError, TypeError):
            catalog_failed = True
    faces, note = collect_faces(data, catalog, catalog_failed)
    if catalog_failed:
        print("The full font list could not be loaded.")
    if note:
        print(note)
    seen = set()
    for face in faces:
        line = format_face_line(face)
        if line in seen:
            continue
        seen.add(line)
        print(line)


def theme_stylesheet(config: dict, password: str) -> str | None:
    status, body, _error = http_request(
        "GET",
        config["site_url"] + "/wp-json/wp/v2/themes?status=active",
        config["username"],
        password,
    )
    if status != 200:
        return None
    try:
        themes = json.loads(body.decode())
    except json.JSONDecodeError:
        return None
    if isinstance(themes, list) and themes:
        return themes[0].get("stylesheet")
    return None


def theme_default_font(config: dict, password: str, stylesheet: str | None) -> str | None:
    if not stylesheet:
        return None
    status, body, _error = http_request(
        "GET",
        config["site_url"] + "/wp-json/wp/v2/global-styles/themes/" + urllib.parse.quote(stylesheet),
        config["username"],
        password,
    )
    if status != 200:
        return None
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError:
        return None
    styles = payload.get("styles") if isinstance(payload, dict) else None
    typography = styles.get("typography") if isinstance(styles, dict) else None
    if not isinstance(typography, dict) or not isinstance(typography.get("fontFamily"), str):
        return ""
    return typography.get("fontFamily")


def restore_theme_default(config: dict, password: str, stylesheet: str, previous: str) -> None:
    current = theme_default_font(config, password, stylesheet)
    if current == previous:
        return
    http_request(
        "POST",
        config["site_url"] + "/wp-json/wp/v2/global-styles/themes/" + urllib.parse.quote(stylesheet),
        config["username"],
        password,
        data=json.dumps({"styles": {"typography": {"fontFamily": previous}}}).encode(),
        headers={"Content-Type": "application/json"},
    )


def font_style_name(value) -> str:
    style = str(value or "normal").lower()
    if style in {"italic", "oblique"}:
        return "italic"
    return "normal"


def stored_font_family(styles) -> str:
    if not isinstance(styles, dict):
        return ""
    typography = styles.get("typography")
    if not isinstance(typography, dict):
        return ""
    family = typography.get("fontFamily")
    return family if isinstance(family, str) else ""


def flatten_font_families(value) -> list[dict]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        families = []
        for key in ("custom", "theme", "default"):
            families.extend(flatten_font_families(value.get(key)))
        return families
    return []


def user_global_styles(config: dict, password: str) -> tuple[dict | None, str | None]:
    status, body, error = http_request(
        "GET",
        config["site_url"] + "/wp-json/wp/v2/themes?status=active&context=edit",
        config["username"],
        password,
    )
    if status != 200:
        return None, error or f"HTTP {status}"
    try:
        themes = json.loads(body.decode())
    except json.JSONDecodeError:
        return None, "Theme response was not JSON"
    if not isinstance(themes, list) or not themes or not isinstance(themes[0], dict):
        return None, "Active theme was not found"
    links = themes[0].get("_links") if isinstance(themes[0].get("_links"), dict) else {}
    entries = links.get("wp:user-global-styles") if isinstance(links, dict) else None
    href = ""
    if isinstance(entries, list) and entries and isinstance(entries[0], dict):
        href = entries[0].get("href") or ""
    match = re.search(r"/global-styles/(\d+)", href)
    if not match:
        return None, "Global Styles for this theme were not found"
    post_id = int(match.group(1))
    status, body, error = http_request(
        "GET",
        config["site_url"] + f"/wp-json/wp/v2/global-styles/{post_id}?context=edit",
        config["username"],
        password,
    )
    if status != 200:
        return None, error or f"HTTP {status}"
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError:
        return None, "Global Styles response was not JSON"
    if not isinstance(payload, dict):
        return None, "Global Styles response was not JSON"
    settings = payload.get("settings")
    styles = payload.get("styles")
    return {
        "id": post_id,
        "settings": copy.deepcopy(settings) if isinstance(settings, dict) else {},
        "styles": copy.deepcopy(styles) if isinstance(styles, dict) else {},
    }, None


def theme_font_families(config: dict, password: str, stylesheet: str | None) -> list[dict]:
    if not stylesheet:
        return []
    status, body, _error = http_request(
        "GET",
        config["site_url"] + "/wp-json/wp/v2/global-styles/themes/" + urllib.parse.quote(stylesheet) + "?context=edit",
        config["username"],
        password,
    )
    if status != 200:
        return []
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError:
        return []
    settings = payload.get("settings") if isinstance(payload, dict) else None
    typography = settings.get("typography") if isinstance(settings, dict) else None
    if not isinstance(typography, dict):
        return []
    return flatten_font_families(typography.get("fontFamilies"))


def custom_font_families(settings: dict) -> list[dict]:
    typography = settings.get("typography")
    if not isinstance(typography, dict):
        typography = {}
        settings["typography"] = typography
    families = typography.get("fontFamilies")
    if isinstance(families, list):
        custom = [item for item in families if isinstance(item, dict)]
        typography["fontFamilies"] = {"custom": custom}
        return custom
    if isinstance(families, dict):
        custom = [item for item in families.get("custom") or [] if isinstance(item, dict)]
        families["custom"] = custom
        return custom
    custom = []
    typography["fontFamilies"] = {"custom": custom}
    return custom


def face_definition(face: dict, web_font: str) -> dict | None:
    settings = settings_object(face.get("font_face_settings"))
    src = settings.get("src")
    if isinstance(src, list):
        src = next((item for item in src if isinstance(item, str) and item.startswith("https://")), None)
    if not isinstance(src, str) or not src.startswith("https://"):
        return None
    definition = {
        "fontFamily": web_font,
        "fontStyle": font_style_name(settings.get("fontStyle")),
        "fontWeight": str(settings.get("fontWeight") or "400"),
        "src": src,
        "fontDisplay": settings.get("fontDisplay") or "swap",
    }
    unicode_range = settings.get("unicodeRange")
    if isinstance(unicode_range, str) and unicode_range:
        definition["unicodeRange"] = unicode_range
    return definition


def face_covers(definition: dict, weight: int, italic: bool) -> bool:
    if font_style_name(definition.get("fontStyle")) != ("italic" if italic else "normal"):
        return False
    return weight_covers(definition.get("fontWeight"), weight)


def family_by_slug(families: list[dict], slug: str) -> dict | None:
    for family in families:
        if family.get("slug") == slug:
            return family
    return None


def post_global_styles(config: dict, password: str, post_id: int, payload: dict) -> str | None:
    status, _body, error = http_request(
        "POST",
        config["site_url"] + f"/wp-json/wp/v2/global-styles/{post_id}",
        config["username"],
        password,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    if status not in {200, 201}:
        return error or f"HTTP {status}"
    return None


def activate_installed_fonts(
    config: dict,
    password: str,
    stylesheet: str | None,
    groups: dict[str, dict],
) -> tuple[set[tuple], list[dict]]:
    if not groups:
        return set(), []
    record, error = user_global_styles(config, password)
    if record is None:
        return set(), [
            {
                "web_font": group["web_font"],
                "slug": group.get("slug"),
                "state": "failed",
                "error": error or "the font was not activated",
            }
            for group in groups.values()
        ]
    original_styles = copy.deepcopy(record["styles"])
    original_family = stored_font_family(original_styles)
    settings = record["settings"]
    custom = custom_font_families(settings)
    theme_families = theme_font_families(config, password, stylesheet)
    active_pairs: set[tuple] = set()
    prior_pairs: set[tuple] = set()
    results = []
    changed = False
    for group in groups.values():
        web_font = group["web_font"]
        slug = group.get("slug")
        if not slug:
            results.append({"web_font": web_font, "slug": None, "state": "failed", "error": "the font was not activated"})
            continue
        library = family_faces(config, password, int(group["family_id"]), stylesheet)
        definitions = []
        for face in library:
            definition = face_definition(face, web_font)
            if definition is not None:
                definitions.append(definition)
        theme_entry = family_by_slug(theme_families, slug)
        custom_entry = family_by_slug(custom, slug)
        current_faces = []
        if custom_entry and isinstance(custom_entry.get("fontFace"), list):
            current_faces = [item for item in custom_entry["fontFace"] if isinstance(item, dict)]
        elif theme_entry and isinstance(theme_entry.get("fontFace"), list):
            current_faces = [item for item in theme_entry["fontFace"] if isinstance(item, dict)]
        missing = []
        covered = set()
        for weight, italic in group["pairs"]:
            if any(face_covers(item, weight, italic) for item in current_faces):
                covered.add((weight, italic))
                prior_pairs.add((web_font, weight, italic))
                continue
            addition = next((item for item in definitions if face_covers(item, weight, italic)), None)
            if addition is None:
                continue
            if not any(item.get("src") == addition["src"] and item.get("fontStyle") == addition["fontStyle"] and item.get("fontWeight") == addition["fontWeight"] for item in missing):
                missing.append(addition)
            covered.add((weight, italic))
        if missing:
            if custom_entry is None:
                base = copy.deepcopy(current_faces)
                custom.append({
                    "name": web_font,
                    "slug": slug,
                    "fontFamily": group["stack"],
                    "fontFace": base + missing,
                })
            else:
                faces = custom_entry.get("fontFace")
                if not isinstance(faces, list):
                    faces = []
                    custom_entry["fontFace"] = faces
                faces.extend(missing)
            changed = True
        for weight, italic in covered:
            active_pairs.add((web_font, weight, italic))
        installed_pairs = {(weight, italic) for weight, italic in group["pairs"]}
        if installed_pairs and installed_pairs <= covered:
            results.append({
                "web_font": web_font,
                "slug": slug,
                "state": "activated" if missing else "already",
            })
        else:
            results.append({"web_font": web_font, "slug": slug, "state": "failed", "error": "the font was not activated"})
    if changed:
        error = post_global_styles(config, password, record["id"], {"settings": settings})
        if error:
            for result in results:
                if result["state"] == "activated":
                    result["state"] = "failed"
                    result["error"] = "the font was not activated"
            return prior_pairs, results
        updated, _update_error = user_global_styles(config, password)
        if updated is not None and stored_font_family(updated["styles"]) != original_family:
            post_global_styles(config, password, record["id"], {"styles": original_styles})
    return active_pairs, results


def apply_activation(report: dict, active_pairs: set[tuple], results: list[dict]) -> None:
    for face in report["faces"]:
        active = (face["web_font"], face["weight"], face["italic"]) in active_pairs and face.get("installed")
        face["active"] = bool(active)
        if not face["active"]:
            face["preset"] = None
            face["class_name"] = None
    for result in results:
        record = {"web_font": result["web_font"], "slug": result.get("slug")}
        if result["state"] == "activated":
            report["activated"].append(record)
        elif result["state"] == "already":
            report["already_active"].append(record)
        else:
            record["error"] = result.get("error") or "the font was not activated"
            report["activation_failed"].append(record)


def http_request(method: str, url: str, username: str, password: str, data: bytes | None = None, headers: dict | None = None):
    header_values = {
        "Authorization": "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode(),
        "User-Agent": USER_AGENT,
    }
    if headers:
        header_values.update(headers)
    req = urllib.request.Request(url, data=data, headers=header_values, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, response.read(), None
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return exc.code, body, body.decode("utf-8", "replace")[:500]
    except urllib.error.URLError as exc:
        return 0, b"", str(exc.reason)


def settings_object(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def weight_covers(stored, requested: int) -> bool:
    parts = str(stored).replace(",", " ").split()
    numbers = [int(part) for part in parts if part.isdigit()]
    if len(numbers) == 1:
        return numbers[0] == requested
    if len(numbers) >= 2:
        return min(numbers[0], numbers[1]) <= requested <= max(numbers[0], numbers[1])
    return False


def list_font_families(config: dict, password: str, stylesheet: str | None) -> tuple[list[dict], str | None]:
    families = []
    page = 1
    while page <= 10:
        query = f"/wp-json/wp/v2/font-families?per_page=100&page={page}"
        if stylesheet:
            query += "&theme=" + urllib.parse.quote(stylesheet)
        status, body, error = http_request(
            "GET",
            config["site_url"] + query,
            config["username"],
            password,
        )
        if status in {401, 403, 404}:
            return [], error or f"HTTP {status}"
        if status != 200:
            return families, error or f"HTTP {status}"
        try:
            batch = json.loads(body.decode())
        except json.JSONDecodeError:
            return families, "Font Library returned invalid JSON"
        if not isinstance(batch, list) or not batch:
            break
        families.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < 100:
            break
        page += 1
    return families, None


def family_faces(config: dict, password: str, family_id: int, stylesheet: str | None) -> list[dict]:
    query = f"/wp-json/wp/v2/font-families/{family_id}/font-faces?per_page=100"
    if stylesheet:
        query += "&theme=" + urllib.parse.quote(stylesheet)
    status, body, _error = http_request(
        "GET",
        config["site_url"] + query,
        config["username"],
        password,
    )
    if status != 200:
        return []
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [
        face for face in payload
        if isinstance(face, dict) and face.get("parent") in {family_id, str(family_id)}
    ]


def face_is_present(faces: list[dict], weight: int, italic: bool) -> bool:
    wanted = "italic" if italic else "normal"
    for face in faces:
        settings = settings_object(face.get("font_face_settings"))
        style = str(settings.get("fontStyle") or "normal").lower()
        stored_italic = style in {"italic", "oblique"}
        if stored_italic != italic and style != wanted:
            continue
        if weight_covers(settings.get("fontWeight"), weight):
            return True
    return False


def latin_face_files(css: str) -> list[dict]:
    parts = re.split(r"/\*\s*([^*]+?)\s*\*/", css)
    files = []
    index = 1
    while index + 1 < len(parts):
        comment = parts[index].strip().lower()
        body = parts[index + 1]
        index += 2
        if comment != "latin" or "@font-face" not in body:
            continue
        source = re.search(r"url\(([^)]+)\)", body)
        weight = re.search(r"font-weight:\s*([^;]+);", body)
        style = re.search(r"font-style:\s*([^;]+);", body)
        unicode_range = re.search(r"unicode-range:\s*([^;]+);", body)
        if not source or not weight:
            continue
        files.append({
            "url": source.group(1).strip("\"'"),
            "weight": weight.group(1).strip(),
            "style": (style.group(1).strip().lower() if style else "normal"),
            "unicode_range": unicode_range.group(1).strip() if unicode_range else "",
            "subset": "latin",
        })
    merged = {}
    for item in files:
        key = (item["url"], item["style"])
        bucket = merged.setdefault(key, [])
        bucket.append(item)
    combined = []
    for (url, style), items in merged.items():
        numbers = []
        for item in items:
            numbers.extend(int(part) for part in item["weight"].split() if part.isdigit())
        numbers = sorted(set(numbers))
        weight = str(numbers[0]) if len(numbers) == 1 else f"{numbers[0]} {numbers[-1]}"
        combined.append({
            "url": url,
            "weight": weight,
            "style": style,
            "unicode_range": items[0]["unicode_range"],
            "subset": "latin",
        })
    return combined


def fetch_css(web_font: str, pairs: list[tuple[int, bool]]) -> str:
    axes = []
    for weight, italic in sorted(set(pairs)):
        axes.append(f"{1 if italic else 0},{weight}")
    family = urllib.parse.quote(web_font)
    joined = ";".join(axes)
    url = f"{CSS2_URL}?family={family}:ital,wght@{joined}&display=swap"
    request = urllib.request.Request(url, headers={"User-Agent": CSS_USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def file_for_pair(files: list[dict], weight: int, italic: bool) -> dict | None:
    style = "italic" if italic else "normal"
    exact = []
    ranged = []
    for item in files:
        item_style = "italic" if item["style"] in {"italic", "oblique"} else "normal"
        if item_style != style:
            continue
        if weight_covers(item["weight"], weight):
            if " " in item["weight"]:
                ranged.append(item)
            else:
                exact.append(item)
    if exact:
        return exact[0]
    if ranged:
        return ranged[0]
    return None


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": CSS_USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def multipart_body(fields: dict[str, str], file_name: str, file_bytes: bytes) -> tuple[bytes, str]:
    boundary = "----designfilefont" + uuid.uuid4().hex
    chunks = []
    for key, value in fields.items():
        chunks.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n".encode()
        )
    chunks.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f"Content-Type: font/woff2\r\n\r\n".encode()
        + file_bytes
        + b"\r\n"
    )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def create_font_family(config: dict, password: str, stylesheet: str | None, web_font: str, stack: str) -> tuple[dict | None, str | None]:
    slug = re.sub(r"[^a-z0-9]+", "-", web_font.lower()).strip("-")
    settings = json.dumps({
        "name": web_font,
        "slug": slug,
        "fontFamily": stack,
    })
    query = "/wp-json/wp/v2/font-families"
    if stylesheet:
        query += "?theme=" + urllib.parse.quote(stylesheet)
    status, body, error = http_request(
        "POST",
        config["site_url"] + query,
        config["username"],
        password,
        data=json.dumps({"font_family_settings": settings}).encode(),
        headers={"Content-Type": "application/json"},
    )
    if status not in {200, 201}:
        return None, error or f"HTTP {status}"
    try:
        created = json.loads(body.decode())
    except json.JSONDecodeError:
        return None, "Font family response was not JSON"
    return created if isinstance(created, dict) else None, None


def upload_font_face(
    config: dict,
    password: str,
    stylesheet: str | None,
    family_id: int,
    stack: str,
    face_file: dict,
) -> tuple[dict | None, str | None]:
    style = "italic" if face_file["style"] in {"italic", "oblique"} else "normal"
    settings = {
        "fontFamily": stack,
        "fontStyle": style,
        "fontWeight": face_file["weight"],
        "fontDisplay": "swap",
        "src": "file",
    }
    if face_file.get("unicode_range"):
        settings["unicodeRange"] = face_file["unicode_range"]
    filename = face_file.get("filename") or "latin.woff2"
    payload, boundary = multipart_body(
        {"font_face_settings": json.dumps(settings)},
        filename,
        face_file["bytes"],
    )
    query = f"/wp-json/wp/v2/font-families/{family_id}/font-faces"
    if stylesheet:
        query += "?theme=" + urllib.parse.quote(stylesheet)
    status, body, error = http_request(
        "POST",
        config["site_url"] + query,
        config["username"],
        password,
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    if status not in {200, 201}:
        return None, error or f"HTTP {status}"
    try:
        created = json.loads(body.decode())
    except json.JSONDecodeError:
        return None, "Font face response was not JSON"
    return created if isinstance(created, dict) else None, None


def command_install_fonts(args: argparse.Namespace) -> None:
    path = Path(args.mzjson).expanduser()
    if not path.is_file():
        fail(f"MZJSON not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"MZJSON is not valid JSON: {exc}")
    catalog = None
    catalog_failed = False
    try:
        catalog = load_google_catalog()
    except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError, TypeError):
        catalog_failed = True
    faces, note = collect_faces(data, catalog, catalog_failed)
    wanted = []
    seen = set()
    for face in faces:
        if not face["web"]:
            continue
        key = (face["web"], face["weight"], face["italic"], face["stack"])
        if key in seen:
            continue
        seen.add(key)
        wanted.append(face)
    config = load_config()
    password = read_password(config["password_file"])
    stylesheet = theme_stylesheet(config, password)
    before = theme_default_font(config, password, stylesheet)
    families, list_error = list_font_families(config, password, stylesheet)
    report = {
        "catalog_loaded": not catalog_failed,
        "note": note,
        "added": [],
        "already": [],
        "failed": [],
        "faces": [],
        "theme_default_before": before,
        "theme_default_after": before,
        "theme_default_unchanged": True,
        "activated": [],
        "already_active": [],
        "activation_failed": [],
        "non_latin_uploaded": False,
    }
    if list_error and not families:
        for face in wanted:
            report["failed"].append({"web_font": face["web"], "weight": face["weight"], "error": "the font files were not added"})
            report["faces"].append({
                "web_font": face["web"],
                "weight": face["weight"],
                "italic": face["italic"],
                "stack": face["stack"],
                "installed": False,
                "slug": None,
                "preset": None,
                "class_name": None,
                "status": "not-added",
                "active": False,
            })
        print(json.dumps(report))
        return
    install_groups: dict[str, dict] = {}
    by_name = {}
    for family in families:
        settings = settings_object(family.get("font_family_settings"))
        name = settings.get("name") or ""
        if name:
            by_name[normalize_family(name)] = family
    grouped: dict[str, list[dict]] = {}
    for face in wanted:
        grouped.setdefault(face["web"], []).append(face)
    uploaded_urls = set()
    for web_font, group in grouped.items():
        try:
            css = fetch_css(web_font, [(face["weight"], face["italic"]) for face in group])
            files = latin_face_files(css)
        except (OSError, urllib.error.URLError):
            files = []
        family = by_name.get(normalize_family(web_font))
        family_id = family.get("id") if family else None
        slug = None
        if family:
            slug = settings_object(family.get("font_family_settings")).get("slug")
        existing = family_faces(config, password, int(family_id), stylesheet) if family_id else []
        if family_id is None:
            created, error = create_font_family(config, password, stylesheet, web_font, group[0]["stack"])
            if created is None and error and "rest_duplicate_font_family" in error:
                refreshed, _refresh_error = list_font_families(config, password, stylesheet)
                for candidate in refreshed:
                    settings = settings_object(candidate.get("font_family_settings"))
                    if normalize_family(settings.get("name") or "") == normalize_family(web_font):
                        created = candidate
                        break
            if created is None:
                for face in group:
                    report["failed"].append({"web_font": web_font, "weight": face["weight"], "error": "the font files were not added"})
                    report["faces"].append({
                        "web_font": web_font,
                        "weight": face["weight"],
                        "italic": face["italic"],
                        "stack": face["stack"],
                        "installed": False,
                        "slug": None,
                        "preset": None,
                        "class_name": None,
                        "status": "not-added",
                        "active": False,
                    })
                continue
            family_id = created.get("id")
            settings = settings_object(created.get("font_family_settings"))
            slug = settings.get("slug")
            by_name[normalize_family(web_font)] = created
            existing = []
        for face in group:
            face_file = file_for_pair(files, face["weight"], face["italic"])
            if face_file is None:
                report["failed"].append({"web_font": web_font, "weight": face["weight"], "error": "latin file was not found"})
                installed = False
                status_name = "not-added"
            elif face_is_present(existing, face["weight"], face["italic"]):
                report["already"].append({"web_font": web_font, "weight": face["weight"], "italic": face["italic"]})
                installed = True
                status_name = "already"
            elif face_file["url"] in uploaded_urls:
                report["already"].append({"web_font": web_font, "weight": face["weight"], "italic": face["italic"]})
                installed = True
                status_name = "already"
            else:
                try:
                    face_file = dict(face_file)
                    face_file["bytes"] = download_bytes(face_file["url"])
                    slug_part = re.sub(r"[^a-z0-9]+", "-", web_font.lower()).strip("-")
                    weight_part = re.sub(r"[^0-9]+", "-", face_file["weight"]).strip("-")
                    style_name = "italic" if face["italic"] else "normal"
                    face_file["filename"] = f"{slug_part}-{weight_part}-{style_name}.woff2"
                except (OSError, urllib.error.URLError):
                    report["failed"].append({"web_font": web_font, "weight": face["weight"], "error": "the font files were not added"})
                    installed = False
                    status_name = "not-added"
                    face_file = None
                if face_file is not None:
                    created_face, error = upload_font_face(
                        config, password, stylesheet, int(family_id), face["stack"], face_file
                    )
                    if created_face is None:
                        report["failed"].append({
                            "web_font": web_font,
                            "weight": face["weight"],
                            "error": "the font files were not added",
                        })
                        installed = False
                        status_name = "not-added"
                    else:
                        uploaded_urls.add(face_file["url"])
                        existing.append(created_face)
                        report["added"].append({"web_font": web_font, "weight": face["weight"], "italic": face["italic"], "subset": "latin"})
                        installed = True
                        status_name = "added"
            class_name = f"has-{slug}-font-family" if installed and slug else None
            preset = f"var:preset|font-family|{slug}" if installed and slug else None
            report["faces"].append({
                "web_font": web_font,
                "weight": face["weight"],
                "italic": face["italic"],
                "stack": face["stack"],
                "installed": installed,
                "slug": slug if installed else None,
                "preset": preset,
                "class_name": class_name,
                "status": status_name,
                "active": False,
            })
            if installed and slug and family_id:
                bucket = install_groups.setdefault(web_font, {
                    "web_font": web_font,
                    "slug": slug,
                    "stack": face["stack"],
                    "family_id": int(family_id),
                    "pairs": [],
                })
                bucket["slug"] = slug
                bucket["family_id"] = int(family_id)
                bucket["pairs"].append((face["weight"], face["italic"]))
    active_pairs, activation_results = activate_installed_fonts(config, password, stylesheet, install_groups)
    apply_activation(report, active_pairs, activation_results)
    if stylesheet:
        restore_theme_default(config, password, stylesheet, before)
    after = theme_default_font(config, password, stylesheet)
    report["theme_default_after"] = after
    report["theme_default_unchanged"] = before == after
    print(json.dumps(report))


def main() -> None:
    parser = argparse.ArgumentParser(description="WordPress REST helper. Never prints the application password.")
    sub = parser.add_subparsers(dest="command", required=True)

    test = sub.add_parser("test", help="Sign in as the current user. Use --save to remember the site.")
    test.add_argument("--site")
    test.add_argument("--username")
    test.add_argument("--password-file")
    test.add_argument("--save", action="store_true")
    test.set_defaults(func=command_test)

    upload = sub.add_parser("upload", help="Upload a JPEG and set its text fields.")
    upload.add_argument("--file", required=True)
    upload.add_argument("--filename")
    upload.add_argument("--title", default="")
    upload.add_argument("--alt", default="")
    upload.add_argument("--caption", default="")
    upload.add_argument("--description", default="")
    upload.set_defaults(func=command_upload)

    create = sub.add_parser("create-post", help="Create a draft post from a Gutenberg markup file.")
    create.add_argument("--title", required=True)
    create.add_argument("--content-file", required=True)
    create.add_argument("--slug", default="")
    create.add_argument("--excerpt", default="")
    create.add_argument("--featured", type=int)
    create.set_defaults(func=command_create_post)

    map_fonts = sub.add_parser("map-fonts", help="Print web-font matches for an MZJSON file. Does not call WordPress.")
    map_fonts.add_argument("--mzjson", required=True)
    map_fonts.add_argument("--offline", action="store_true")
    map_fonts.set_defaults(func=command_map_fonts)

    install_fonts = sub.add_parser("install-fonts", help="Install Latin faces and activate them for the current theme.")
    install_fonts.add_argument("--mzjson", required=True)
    install_fonts.set_defaults(func=command_install_fonts)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
