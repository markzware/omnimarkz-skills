# What changed — comparison steps

Run these steps on the Mac. Do not compare the MZJSON by reading it in the prompt. Do not request `png` or any format other than `mzjson`.

## 1. Guess the newer file

Save the program below and run:

```bash
python3 /tmp/what-changed.py guess "/absolute/path/one.indd" "/absolute/path/two.indd"
```

The program prints the question `Is {filename} the newer version?` and nothing else. Ask the user that question. Wait for yes or no before converting.

Yes: that filename is the newer file. No: the other file is the newer file.

## 2. Same path

If the two path strings are the same, do not convert. Run:

```bash
python3 /tmp/what-changed.py same "/absolute/path/file.indd"
```

That writes `what-changed.md` beside the file. Every heading says `Nothing changed.` Stop.

## 3. Convert

`probe_path`, then `convert_file` with `formats: ["mzjson"]`, earlier file first, then newer file. One conversion at a time. On `busy`, wait and retry that call once. On a second `busy`, or any other error (`password_unsupported`, `license_required`, `conversion_failed`, `allowlist_rejected`), stop and do not write the six headings.

When several `.mzjson` files come back, pass the unsuffixed one unless the user named a layout.

## 4. Compare

```bash
python3 /tmp/what-changed.py compare \
  --earlier "/absolute/earlier.mzjson" \
  --newer "/absolute/newer.mzjson" \
  --earlier-source "/absolute/earlier.indd" \
  --newer-source "/absolute/newer.indd" \
  --confirmed "newer.indd" \
  --out "/absolute/folder/what-changed.md"
```

`--out` defaults to `what-changed.md` in the newer source file’s folder. If that folder is not writable, ask for a folder and do not write until the user gives one.

The program reads `document.stories` `content`, splits paragraphs on `\r\n`, `\r`, or `\n`, and hashes each preview file with SHA-256. It does not trim or collapse spaces or line breaks.

## Program

Save this as `/tmp/what-changed.py`.

```python
#!/usr/bin/env python3
import argparse, hashlib, json, os, re, sys
from collections import Counter

INT_KINDS = (
    ("v", re.compile(r"(?i)(?<![A-Za-z])(?:version|ver)[ _.\-]*(\d+)")),
    ("v", re.compile(r"(?i)(?<![A-Za-z])v[ _.\-]*(\d+)")),
    ("rev-num", re.compile(r"(?i)(?<![A-Za-z])(?:revision|rev)[ _.\-]*(\d+)")),
    ("round", re.compile(r"(?i)(?<![A-Za-z])round[ _.\-]*(\d+)")),
    ("r", re.compile(r"(?i)(?:(?<=^)|(?<=[\s_\-]))r(\d+)")),
)
LETTER = re.compile(r"(?i)(?<![A-Za-z])rev[ _.\-]*([A-Za-z])(?![A-Za-z0-9])")

def tokens(stem):
    found = []
    for kind, pattern in INT_KINDS:
        for match in pattern.finditer(stem):
            found.append((match.end(), match.start(), kind, int(match.group(1))))
    for match in LETTER.finditer(stem):
        found.append((match.end(), match.start(), "rev-letter", match.group(1).upper()))
    found.sort(key=lambda item: (item[0], item[0] - item[1]))
    if not found:
        return None
    _end, _start, kind, value = found[-1]
    return kind, value

def guess(path_a, path_b):
    name_a = os.path.basename(path_a)
    name_b = os.path.basename(path_b)
    stem_a = os.path.splitext(name_a)[0]
    stem_b = os.path.splitext(name_b)[0]
    token_a = tokens(stem_a)
    token_b = tokens(stem_b)
    chosen = None
    if token_a and token_b and token_a[0] == token_b[0] and token_a[1] != token_b[1]:
        if token_a[1] > token_b[1]:
            chosen = name_a
        else:
            chosen = name_b
    if chosen is None:
        try:
            mtime_a = os.stat(path_a).st_mtime
            mtime_b = os.stat(path_b).st_mtime
        except OSError:
            mtime_a = mtime_b = None
        if mtime_a is not None and mtime_a != mtime_b:
            chosen = name_a if mtime_a > mtime_b else name_b
    if chosen is None:
        chosen = name_a
    print(f"Is {chosen} the newer version?")

def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)

def split_paragraphs(content):
    if content is None or content == "":
        return []
    return re.split(r"\r\n|\r|\n", content)

def bounds_of(item):
    bounds = item.get("bounds") or {}
    return float(bounds.get("y") or 0), float(bounds.get("x") or 0)

def walk_items(items, page, out):
    ordered = sorted(items or [], key=bounds_of)
    for item in ordered:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "group":
            walk_items(item.get("children"), page, out)
        else:
            out.append((page, item))

def frames(data):
    document = data.get("document") or {}
    found = []
    page_number = 1
    for spread in document.get("spreads") or []:
        pages = spread.get("pages") or [{}]
        width = 0
        if pages and isinstance(pages[0], dict):
            width = float((pages[0].get("bounds") or {}).get("width") or 0)
        items = spread.get("items") or []
        if len(pages) <= 1 or width <= 0:
            walk_items(items, page_number, found)
            page_number += max(len(pages), 1)
            continue
        buckets = {index: [] for index in range(len(pages))}
        for item in items:
            if not isinstance(item, dict):
                continue
            x = float((item.get("bounds") or {}).get("x") or 0)
            slot = int(x // width)
            if slot < 0:
                slot = 0
            if slot >= len(pages):
                slot = len(pages) - 1
            buckets[slot].append(item)
        for index in range(len(pages)):
            walk_items(buckets[index], page_number, found)
            page_number += 1
    return found

def story_pages(data):
    pages = {}
    for page, item in frames(data):
        if item.get("type") != "textFrame":
            continue
        ref = item.get("storyRef")
        if ref and ref not in pages:
            pages[ref] = page
    return pages

def paragraphs(data):
    document = data.get("document") or {}
    stories = document.get("stories") or {}
    pages = story_pages(data)
    rows = []
    if isinstance(stories, dict):
        pairs = stories.items()
    else:
        pairs = []
    ordered = []
    for key, story in pairs:
        if isinstance(story, dict):
            ordered.append((pages.get(key) or pages.get(story.get("id")) or 10**9, key, story))
    for page, _key, story in sorted(ordered, key=lambda row: (row[0], row[1])):
        text_page = None if page == 10**9 else page
        for paragraph in split_paragraphs(story.get("content")):
            rows.append((paragraph, text_page))
    return rows

def surplus(earlier, later):
    earlier_counts = Counter(text for text, _page in earlier)
    later_counts = Counter(text for text, _page in later)
    shared = {text: min(earlier_counts[text], later_counts[text]) for text in earlier_counts}
    kept_earlier = []
    used = Counter()
    for text, page in earlier:
        if used[text] < shared.get(text, 0):
            used[text] += 1
        else:
            kept_earlier.append((text, page))
    kept_later = []
    used = Counter()
    for text, page in later:
        if used[text] < shared.get(text, 0):
            used[text] += 1
        else:
            kept_later.append((text, page))
    return kept_earlier, kept_later

def words(text):
    return text.split()

def runs(word_list, length):
    if length < 1 or len(word_list) < length:
        return []
    return [tuple(word_list[index:index + length]) for index in range(len(word_list) - length + 1)]

def rewords(earlier, later):
    earlier_words = [(text, page, words(text)) for text, page in earlier]
    later_words = [(text, page, words(text)) for text, page in later]
    candidates = []
    for e_index, (e_text, e_page, e_words) in enumerate(earlier_words):
        for l_index, (l_text, l_page, l_words) in enumerate(later_words):
            shorter = min(len(e_words), len(l_words))
            if shorter == 0:
                continue
            need = max(8, shorter / 2)
            length = int(need) if need == int(need) else int(need) + 1
            unique = None
            while length <= shorter:
                e_runs = set(runs(e_words, length))
                l_runs = set(runs(l_words, length))
                shared = e_runs & l_runs
                for run in shared:
                    e_hits = sum(1 for _t, _p, words_ in earlier_words if run in set(runs(words_, length)))
                    l_hits = sum(1 for _t, _p, words_ in later_words if run in set(runs(words_, length)))
                    if e_hits == 1 and l_hits == 1:
                        unique = run
                        break
                if unique:
                    break
                length += 1
            if unique:
                candidates.append((e_index, l_index, len(unique)))
    best = {}
    for e_index, l_index, size in candidates:
        key = (e_index, l_index)
        if key not in best or size > best[key]:
            best[key] = size
    pairs = list(best)
    conflicted = set()
    e_seen = {}
    l_seen = {}
    for e_index, l_index in pairs:
        if e_index in e_seen or l_index in l_seen:
            conflicted.add(e_index)
            conflicted.add(("l", l_index))
            if e_index in e_seen:
                conflicted.add(e_seen[e_index][0])
                conflicted.add(("l", e_seen[e_index][1]))
            if l_index in l_seen:
                conflicted.add(l_seen[l_index][0])
                conflicted.add(("l", l_index))
        e_seen[e_index] = (e_index, l_index)
        l_seen[l_index] = (e_index, l_index)
    chosen = []
    used_e = set()
    used_l = set()
    for e_index, l_index in pairs:
        if e_index in used_e or l_index in used_l:
            continue
        others_e = [pair for pair in pairs if pair[0] == e_index]
        others_l = [pair for pair in pairs if pair[1] == l_index]
        if len(others_e) > 1 or len(others_l) > 1:
            continue
        chosen.append((earlier_words[e_index][0], earlier_words[e_index][1], later_words[l_index][0], later_words[l_index][1]))
        used_e.add(e_index)
        used_l.add(l_index)
    rest_e = [earlier[index] for index in range(len(earlier)) if index not in used_e]
    rest_l = [later[index] for index in range(len(later)) if index not in used_l]
    return chosen, rest_e, rest_l

def resolve(mzjson_path, href):
    if not href:
        return ""
    if os.path.isabs(href):
        return href
    return os.path.join(os.path.dirname(os.path.abspath(mzjson_path)), href)

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def photos(data, mzjson_path):
    previews = []
    linked = []
    for page, item in frames(data):
        if item.get("type") != "imageFrame":
            continue
        content = item.get("content") or {}
        kind = content.get("type")
        href = content.get("href") or ""
        if kind == "preview":
            file_path = resolve(mzjson_path, href)
            if not os.path.isfile(file_path):
                continue
            previews.append((sha256(file_path), os.path.basename(href), page))
        elif kind == "linked" and href:
            linked.append((href, page))
    return previews, linked

def photo_surplus(earlier, later):
    earlier_counts = Counter(item[0] for item in earlier)
    later_counts = Counter(item[0] for item in later)
    shared = {key: min(earlier_counts[key], later_counts[key]) for key in earlier_counts}
    used = Counter()
    kept_e = []
    for item in earlier:
        if used[item[0]] < shared.get(item[0], 0):
            used[item[0]] += 1
        else:
            kept_e.append(item)
    used = Counter()
    kept_l = []
    for item in later:
        if used[item[0]] < shared.get(item[0], 0):
            used[item[0]] += 1
        else:
            kept_l.append(item)
    return kept_e, kept_l

def linked_changes(earlier, later):
    pages = sorted(set([page for _href, page in earlier] + [page for _href, page in later]))
    changed = []
    removed = []
    added = []
    for page in pages:
        e_urls = [href for href, item_page in earlier if item_page == page]
        l_urls = [href for href, item_page in later if item_page == page]
        e_left, l_left = photo_surplus([(url, page) for url in e_urls], [(url, page) for url in l_urls])
        e_only = [url for url, _page in e_left]
        l_only = [url for url, _page in l_left]
        if len(e_only) == 1 and len(l_only) == 1:
            changed.append((page, e_only[0], l_only[0]))
        else:
            removed.extend((page, url) for url in e_only)
            added.extend((page, url) for url in l_only)
    return added, removed, changed

def fence(text):
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}\n{text}\n{ticks}"

def page_label(page):
    return f"Page {page}\n\n" if page else ""

def section(title, body):
    if not body:
        body = "Nothing changed.\n"
    return f"## {title}\n\n{body}"

def write_report(path, header, added, removed, reworded, photos_added, photos_removed, photos_changed):
    def text_blocks(rows):
        parts = []
        for text, page in rows:
            parts.append(page_label(page) + fence(text) + "\n")
        return "".join(parts)

    def reword_blocks(rows):
        parts = []
        for earlier_text, earlier_page, later_text, later_page in rows:
            page = earlier_page or later_page
            parts.append(
                page_label(page)
                + "Earlier:\n\n"
                + fence(earlier_text)
                + "\n\nLater:\n\n"
                + fence(later_text)
                + "\n"
            )
        return "".join(parts)

    def photo_lines(rows):
        return "".join(f"- Page {page}: `{name}`\n" for _key, name, page in rows)

    def url_lines(rows):
        return "".join(f"- Page {page}: `{url}`\n" for page, url in rows)

    changed = ""
    for page, earlier_url, later_url in photos_changed:
        changed += f"Page {page}\n\nEarlier: `{earlier_url}`\n\nLater: `{later_url}`\n\n"
    report = (
        header
        + section("Text added", text_blocks(added))
        + "\n"
        + section("Text removed", text_blocks(removed))
        + "\n"
        + section("Text reworded", reword_blocks(reworded))
        + "\n"
        + section("Photos added", photo_lines(photos_added))
        + "\n"
        + section("Photos removed", photo_lines(photos_removed))
        + "\n"
        + section("Photos changed", changed)
    )
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        raise SystemExit(f"Folder does not exist: {folder}")
    if folder and not os.access(folder, os.W_OK):
        raise SystemExit(f"Folder is not writable: {folder}")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(report)
    print(path)

def header_for(earlier_source, newer_source, confirmed, earlier_data, newer_data, layout_note):
    e_source = earlier_data.get("source") or {}
    n_source = newer_data.get("source") or {}
    lines = [
        "# What changed",
        "",
        f"Earlier: `{earlier_source}`",
        f"Newer: `{newer_source}`",
        f"Confirmed newer: `{confirmed}`",
        f"Pages: {e_source.get('pages', '')} earlier, {n_source.get('pages', '')} newer",
        f"Formats: {e_source.get('format', '')} earlier, {n_source.get('format', '')} newer",
    ]
    if layout_note:
        lines.append(f"Layout file: `{layout_note}`")
    lines.append("")
    return "\n".join(lines) + "\n"

def compare(args):
    earlier_data = load(args.earlier)
    newer_data = load(args.newer)
    e_left, l_left = surplus(paragraphs(earlier_data), paragraphs(newer_data))
    reworded, removed, added = rewords(e_left, l_left)
    e_prev, e_link = photos(earlier_data, args.earlier)
    n_prev, n_link = photos(newer_data, args.newer)
    prev_removed, prev_added = photo_surplus(e_prev, n_prev)
    link_added, link_removed, link_changed = linked_changes(e_link, n_link)
    photos_added = [(digest, name, page) for digest, name, page in prev_added]
    photos_added += [("", url, page) for page, url in link_added]
    photos_removed = [(digest, name, page) for digest, name, page in prev_removed]
    photos_removed += [("", url, page) for page, url in link_removed]
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.newer_source)), "what-changed.md")
    write_report(
        out,
        header_for(args.earlier_source, args.newer_source, args.confirmed, earlier_data, newer_data, args.layout),
        added,
        removed,
        reworded,
        photos_added,
        photos_removed,
        link_changed,
    )

def same(path):
    name = os.path.basename(path)
    header = (
        "# What changed\n\n"
        f"The two paths are the same: `{path}`\n\n"
        f"Earlier: `{path}`\n"
        f"Newer: `{path}`\n"
        f"Confirmed newer: `{name}`\n\n"
    )
    out = os.path.join(os.path.dirname(os.path.abspath(path)), "what-changed.md")
    write_report(out, header, [], [], [], [], [], [])

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    guess_cmd = sub.add_parser("guess")
    guess_cmd.add_argument("path_a")
    guess_cmd.add_argument("path_b")
    same_cmd = sub.add_parser("same")
    same_cmd.add_argument("path")
    compare_cmd = sub.add_parser("compare")
    compare_cmd.add_argument("--earlier", required=True)
    compare_cmd.add_argument("--newer", required=True)
    compare_cmd.add_argument("--earlier-source", required=True)
    compare_cmd.add_argument("--newer-source", required=True)
    compare_cmd.add_argument("--confirmed", required=True)
    compare_cmd.add_argument("--out")
    compare_cmd.add_argument("--layout", default="")
    args = parser.parse_args()
    if args.command == "guess":
        guess(args.path_a, args.path_b)
    elif args.command == "same":
        same(args.path)
    else:
        compare(args)

if __name__ == "__main__":
    main()
```
