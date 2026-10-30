# Slides reference

Skill version: 1

## Before converting

The user asks for slides or a PowerPoint and provides one design file. Supported sources are InDesign, Publisher, QuarkXPress, and PDF.

Stop and write no `.pptx` when any of these are true:

- OmniMarkz is not connected. Point the user at **OmniMarkz → Preferences → MCP**.
- The path is missing, relative, or outside a folder OmniMarkz is allowed to read.
- The PDF is password-protected, or `convert_file` returns `password_unsupported`, `license_required`, or `allowlist_rejected`.
- Any other convert failure.
- The server answers `busy` twice. Wait and retry once after the first `busy`.

## Conversion

`probe_path`, then `convert_file` with `formats: ["mzjson"]`.

More than one `.mzjson`: the unsuffixed file is the default layout. A layout the user names is that layout’s `.mzjson`. Say which file you used when more than one came back. Do not mix pages from two layouts.

Pages follow the MZJSON page order. On a page, order frames left to right, then top to bottom. Text comes from `storyRef` plus `textRange`: use that frame’s range of the story, not the whole story on every frame. Keep line breaks that are in the story text. Copy the wording. A typo stays a typo.

## Drop before you look for headings

These are not slides and they are not copied into notes:

- A page number: a short line that is only a number, or a folio such as `3 / 12`.
- A running header or footer: the same line repeated from another page.

A caption is a short line that sits with a photo. It stays in the notes of the section that holds that photo. It does not start a slide.

## Headings and sections

A heading is a text block of at most two lines that also matches one of these:

- Its paragraph style name contains `Heading` or `Title`, ignoring case.
- Its point size is larger than the following text block.
- It is bold and the following text block is not.

The only text block in the file is the title even when it has no style, size, or weight signal. That file is one slide, that title, and empty notes.

A series of short labels is body copy. Keep it as a list in the notes, one label per line. Do not start a slide per label.

A section starts at a heading and includes the body before the next heading. Order blocks by `storyRef` plus `textRange`, then left to right and top to bottom. Text and photos that sit before the first heading belong to slide 1. The first heading is slide 1.

When the file has no heading, make one slide per page. The title is the first non-empty line on that page, or the source filename without its extension when the page has no text. The rest of that page’s wording is the notes. Do not make one slide per text frame.

When the file has no text and no qualifying photo, make one slide. The title is the source filename without its extension. The notes are empty. Say in the reply that the file had no text.

## Photos

A qualifying photo is an `imageFrame` whose `content.type` is `preview`, whose `content.href` is a local file, and whose pixel width and pixel height are each at least 100. Open the file and read its pixels. A 100×100 image is kept.

Skip `empty`, `missing`, a frame under 100 pixels on either side, a `linked` URL, and a page PNG (`_pg1.png` and the like). Do not download a `linked` URL.

If `content.href` is missing after the `mzjson` convert, call `convert_file` once more with `formats: ["mzjson", "png"]`. If it is still missing, skip that frame. Do not invent a path.

Compare file bytes. The same bytes go on one slide, the earliest section in reading order. A later frame with those bytes is skipped. Every other qualifying photo in that section goes on that same slide. A section with no qualifying photo still has its slide, with the title and notes and no picture.

The title stays visible. Photos sit under the title. They do not cover it. The slide is not a picture of the original page.

## Write the file

Build a JSON file of the slides, in order:

```json
{
  "slides": [
    {
      "title": "Section title",
      "notes": "Body wording, including a typo.\n• Short label\n• Short label",
      "images": ["/absolute/path/photo.jpg"]
    }
  ]
}
```

`title` is the section title only. `notes` is the body only. An empty body is `""`. A list of short labels is one line per label in `notes`. `images` lists that section’s qualifying photos, earliest duplicate bytes already removed. Use absolute paths.

From this skill’s folder:

```bash
python3 scripts/pptx.py --out "/path/Source Name_slides.pptx" --slides /tmp/design-file-slides.json
```

The script uses the standard library. It does not call PowerPoint, Keynote, or a Microsoft account. It does not upload. It exits 2 and writes nothing when `--out` already exists.

`{source-basename}` keeps the source name’s spaces. `Brochure.indd` writes `Brochure_slides.pptx` beside `Brochure.indd`. When that name exists, write `Brochure_slides_2.pptx`, then `Brochure_slides_3.pptx`. When `_3` exists, stop and tell the user. Do not overwrite.

The canvas shows the title and the photos. The body is only in speaker notes.

Tell the user the path. Do not upload the deck. Do not create a WordPress post from the design file.
