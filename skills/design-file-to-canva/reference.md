# Canva design reference

Skill version: 1

## Before converting

The user asks for a Canva design and provides one design file. Supported sources are InDesign, Publisher, QuarkXPress, and PDF.

Stop and create no Canva design when any of these are true:

- OmniMarkz is not connected. Point the user at **OmniMarkz → Preferences → MCP**.
- The Canva MCP is not connected. Say so. Do not call the Canva REST API. Do not create a WordPress draft of the design file.
- The path is missing, relative, or outside a folder OmniMarkz is allowed to read.
- The PDF is password-protected.
- `convert_file` returns `password_unsupported`, `license_required`, `license_expired`, `feature_locked`, `allowlist_rejected`, `permission_denied`, `unsupported_format`, `conversion_failed`, or any other failure.
- The server answers `busy` twice. Wait and retry once after the first `busy`.

A pasted Canva URL is not the destination. Create a new design and say the pasted design was not edited.

## Conversion

`probe_path`, then `convert_file` with `formats: ["mzjson", "png"]` and `resolution: 144`.

More than one `.mzjson`: the unsuffixed file is the default layout. A layout the user names is that layout’s `.mzjson`. Say which file you used when more than one came back. Do not mix pages from two layouts.

Page previews are `_pg1.png`, `_pg2.png`, and so on, beside the MZJSON. Open each one. They show how the page is arranged. They are not the Canva pages. Do not upload a page PNG as the page.

Pages follow the MZJSON page order. On a page, read frames left to right, then top to bottom.

## Text

Text comes from `storyRef` plus `textRange` for frames on this page. Use that frame’s range of the story. Do not paste the whole story onto every page. Keep line breaks that are in the story text. Copy the wording, including typos and odd capitalization.

Wording the page preview shows on this page goes on this Canva page. That includes a footer or other story that already appeared on an earlier page.

For each text block, note the color as it appears on the page preview, as `#RRGGBB`.

## Photographs

A real photograph is an `imageFrame` whose `content.type` is `preview` and whose `content.href` is a local PNG beside the MZJSON. Compare file bytes. Upload each unique PNG once. Place that upload in every spot the preview shows it.

Skip these:

- `content.type` `empty` or `missing`.
- An ornamental flourish. A small placed logo stays.
- A graphic that is only a color field. That color is the background. Do not upload it.
- `content.type` `linked`. That `href` is a URL. Do not download it and do not upload it.
- An original placed TIFF, PSD, or other non-preview file.
- A page PNG (`_pg1.png` and the like).

Do not put a photograph on a public host.

## What to note for each page

In page order, note:

- What sits behind the type: a photograph, or a flat color. Record the flat color as `#RRGGBB`.
- The color of each text block.
- Whether regions sit side by side.
- Where each real photograph sits: full-bleed background, or an inset frame beside or under the text.

## Create the design

Use the Canva MCP `create-design`. That call creates the document and its pages together. Do not use `generate-design` when `create-design` is available. Do not use a brand template. Do not call `resize-design`.

`format` is required. The name includes the orientation, as in `Flyer (Landscape A4)`. A name without orientation comes out square. Read the first page’s width and height in points. Inches are points divided by 72. A page about 5 inches wide and 7 inches tall uses a portrait card format, and the format string includes Portrait. Name the exact format string you passed in the reply.

When a later page’s size differs, still make one design, at the first page’s format. Name that later page in the reply.

Pass `outline` only when the user asked for a presentation or for slides in Canva. Then `outline.sections` has one section per source page, in order. `title` is the first short line on that page, or `Page N` when the page has no short line. `description` is that page’s source wording, not a summary. A doc, flyer, card, or brochure omits `outline`. The brief asks for one page per source page and carries the same wording and layout notes: background, text colors, side-by-side regions, and where each photograph sits. Ask for a text box for each source line and a frame for each photograph. Say the photographs will be replaced with the file’s own photographs after generation.

Every Canva MCP call includes a short `user_intent`.

`create-design` returns a job. When its widget is showing, do not poll. When no widget is showing, poll `get-create-design-async-job` with the job id and continuation token, waiting the number of seconds that response asks for. A failed job stops the run. Do not call the design finished and do not save.

Count the Canva pages. When the count is the source page count plus one, open the editing transaction and inspect page 1. If that page has no text and no images, or `is_empty` is true, it is Canva’s blank page. Cancel that transaction. Call `merge-designs` with `type` `modify_existing_design`, the new design id, and one operation: `delete_pages` with `page_numbers` `[1]`. Do not ask the user. Then open a new editing transaction. Match each remaining page to a source page by the wording on it. Canva may return those pages in reverse order. Say that the blank page was removed. Edit the matched pages. Any other count stops the run. Give the link if one exists. Do not call the design finished and do not save. Do not add a blank page. Do not call `merge-designs` to copy a page, reorder pages, or delete any page other than that one leading blank page.

## Upload photographs

For each unique `preview` PNG:

1. Call `create-upload-url`.
2. POST the raw file bytes to the returned URL with `Content-Type: application/octet-stream`. The body is the file bytes only. No multipart form, no base64, and no JSON wrapper.
3. Read the image id from that POST response. Use it as `asset_id` on `update_fill`.

Each URL accepts one upload. If it is used, expired, or rejected, call `create-upload-url` again. Do not retry a used URL. Do not call `upload-asset-from-url`.

## Edit the draft

Call `start-editing-transaction` with the new design id. Design ids start with `D`.

On each existing text box, `replace_text` with the source wording for that box, then `format_text` with the noted `#RRGGBB`. On each existing image frame that should show a file photograph, `update_fill` with `asset_type` `image`, the uploaded `asset_id`, and a short `alt_text`. Pass `page_index` as the first page you are changing, using one-based numbering. Pass the `pages` array from the latest `start-editing-transaction` or `perform-editing-operations` response.

When a source line has no text box, name that line and leave the page. When the page has no flat color behind the type, say so. When a photograph has no frame, name it as unplaced. Do not add a text box. Do not draw a colored shape. Do not upload the page PNG. Do not call `insert_fill` to invent a frame.

Show the pages. Give the user the design link. Call `commit-editing-transaction` in the same turn, as soon as the wording and photograph edits are applied. The link includes those edits. Do not ask the user to save. Do not leave the transaction open. An open transaction drops the corrections when the session ends.

When a page-count mismatch stops the run and a transaction is already open, call `cancel-editing-transaction`. Do not save. The link, if one exists, stays the generated design.

Do not publish the design, order a print, or export a PDF, PNG, or other file unless the user asks for that export in the same request.

A file with text and colors but no `preview` photograph still gets a design. Say there are no photographs to place.
