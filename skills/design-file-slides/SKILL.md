---
name: design-file-slides
description: >-
  Turn an InDesign, Publisher, QuarkXPress, or PDF file into a PowerPoint
  in reading order. Use when someone asks for slides or a PowerPoint from
  one of those files.
---

# Slides from a design file

Skill version: 1

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using this skill.

Supported sources are InDesign, Publisher, QuarkXPress, and PDF. Password-protected PDFs are not supported. Say so and stop. Write no `.pptx` when OmniMarkz is not connected, when the path is missing, or when `convert_file` returns `password_unsupported`, `license_required`, `allowlist_rejected`, or any other failure.

The path is absolute and in a folder OmniMarkz is allowed to read. Call `probe_path`, then `convert_file` with `formats: ["mzjson"]`. If the server answers `busy`, wait and retry once. A second `busy` stops the run and writes no `.pptx`. If OmniMarkz is not connected, point the user at **OmniMarkz → Preferences → MCP** and write no `.pptx`.

When `convert_file` returns more than one `.mzjson`, use the unsuffixed file unless the user names a layout. Name that file in the reply when more than one was returned.

If a qualifying frame’s `content.href` is not a local file after that convert, call `convert_file` once more with `formats: ["mzjson", "png"]`. If the local file is still missing, skip that frame. Do not invent a path.

Write the deck only by running `scripts/pptx.py` next to this file, with Python’s standard library. Do not use PowerPoint, Keynote, Google Slides, or a Microsoft account. Do not pip install. Do not upload the `.pptx`. Do not create a WordPress post from the design file.

The path is `{source-basename}_slides.pptx` in the source file’s folder. `{source-basename}` is the source file name without its extension. When that file exists, use `_2`, then `_3`. Leave the existing file in place. When `_3` also exists, stop and tell the user. The script refuses to overwrite. Tell the user the path it wrote.

One slide per section, in reading order: the cover or title first, then left to right and top to bottom. Copy the source wording, including typos. Do not summarize. The canvas shows the title and that section’s qualifying photos. The title stays visible. The body, including a list of short labels, is only in the speaker notes.

A heading is a text block of at most two lines that has a paragraph style whose name contains Heading or Title, or that is larger or bolder than the following text. A section starts at that heading and runs through the body before the next heading. The first heading is slide 1. A file with no heading is one slide per page, not one slide per text frame. A title-only file is one slide with that title and empty notes. A file with no text and no qualifying photo is one slide titled with the source filename, empty notes, and a reply that says the file had no text.

A qualifying photo is an `imageFrame` whose `content.type` is `preview`, whose `content.href` is a local file, and whose width and height are each at least 100 pixels. Skip `empty`, `missing`, a `linked` URL, a page PNG, and a second frame with the same bytes. Those bytes go on the earliest section. A section with no such photo still has its slide.

Field notes, the heading rule, the photo rule, and the `slides.json` shape are in [reference.md](reference.md).
