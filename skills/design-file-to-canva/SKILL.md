---
name: design-file-to-canva
description: >-
  Turn an InDesign, Publisher, QuarkXPress, or PDF file into a Canva design.
  Use when someone asks to turn one of those files into a Canva design.
---

# Canva design from a design file

Skill version: 1

Connect OmniMarkz from **OmniMarkz → Preferences → MCP**, and connect the Canva MCP, before using this skill. Canva work goes through the Canva MCP. Do not call the Canva REST API. Do not use a Canva token. OmniMarkz does not call Canva.

Supported sources are InDesign, Publisher, QuarkXPress, and PDF. Password-protected PDFs are not supported. Create no Canva design when OmniMarkz is not connected, when the Canva MCP is not connected, when the path is missing, or when `convert_file` returns `password_unsupported`, `license_required`, `license_expired`, `feature_locked`, `allowlist_rejected`, `permission_denied`, `unsupported_format`, `conversion_failed`, or any other failure. A second `busy` also stops the run with no Canva design. If the Canva MCP is missing, say so. Do not create a WordPress draft of the design file.

The path is absolute and in a folder OmniMarkz is allowed to read. Call `probe_path`, then `convert_file` with `formats: ["mzjson", "png"]` and `resolution: 144`. If the server answers `busy`, wait and retry once. If OmniMarkz is not connected, point the user at **OmniMarkz → Preferences → MCP** and stop.

When `convert_file` returns more than one `.mzjson`, use the unsuffixed file unless the user names a layout. Name that file in the reply when more than one was returned. Do not mix pages from two layouts.

`create-design` makes the document and its pages together. Ask for one page per source page, in that order. A presentation passes an outline with one section per source page. A doc, flyer, card, or other non-presentation format passes no outline. The brief carries the source wording and the layout notes. Pass a named Canva format, and include the orientation in that name. A 5 by 7 inch portrait page uses a portrait card format. Name the format string in the reply. Pages that differ in size use the first page’s format. Name any later page that differs. Do not call `resize-design`. Do not use `generate-design` when `create-design` is available.

If the create job fails, say so, do not call the design finished, and do not save. When Canva returns exactly one more page than the source, open the editing transaction and inspect page 1. If that page has no text and no images, it is Canva’s blank page. Cancel that transaction. Delete page 1 with `merge-designs`, using `modify_existing_design` and one `delete_pages` operation for page 1. Do not ask the user. The request to create the design is the approval for removing that one blank page. Then open a new editing transaction. Match each remaining page to a source page by the wording on it. Canva may return those pages in reverse order. Say that the blank page was removed. Continue the wording and photograph edits on the matched pages. Any other page-count difference stops the run with no save. Do not add a blank page. Do not call `merge-designs` to copy a page, reorder pages, or delete any page other than that one leading blank page.

Page PNG files are a layout guide. Do not upload a page PNG as the page. A photograph is an image frame whose `content.type` is `preview`. Its file is the PNG at `content.href`, beside the MZJSON. Upload that PNG once, as local bytes, through `create-upload-url`. Do not use `upload-asset-from-url`. Do not put the file on a public host. Place that upload in every spot the preview shows it. `content.type` `linked` is a URL. Do not download it and do not upload it. Leave an original TIFF or PSD alone.

After generation, put the source wording back on each existing text box and set that box’s color to the color noted for that block. A missing text box, a missing flat background, or a missing image frame is reported. Leave the rest of the page. Do not add a text box, draw a colored shape, or upload the page PNG to stand in for the background.

Show the pages and give the user the design link. Call `commit-editing-transaction` in the same turn, as soon as the wording and photograph edits are applied. The link includes those edits. The request to create the design is the approval for that save. Do not ask the user to save. If a page-count mismatch means the run must stop, and an editing transaction is already open, call `cancel-editing-transaction` and do not save. A pasted Canva URL is not edited. Say that this run created a new design.

Do not publish the design, order a print, or export a file unless the user asks for that export in the same request.

Field notes and the Canva MCP calls are in [reference.md](reference.md).
