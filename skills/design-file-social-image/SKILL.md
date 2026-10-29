---
name: design-file-social-image
description: >-
  Make a social image and a caption from an InDesign, Publisher, QuarkXPress,
  or PDF file. Use when someone asks for a social image, a square image, or a
  caption from one of those files. The user names the social site.
---

# Social image and caption

Skill version: 1

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using this skill.

The user specifies the social site, such as Instagram. Do not choose, default, or guess a site. If the request does not name one, write no files and tell the user to name the site. Do not convert first.

If that site has more than one current image size, the user specifies which one. If they do not, write no files and tell them to name the size. Do not convert first.

The first time that site and size are needed in this chat, look up the current recommended pixel width and height. Reuse those two numbers for the rest of this chat. A later file for the same site and size does not look them up again. If the lookup fails, write no files and do not substitute 1080 or any other size.

Supported sources are InDesign, Publisher, QuarkXPress, and PDF. Password-protected PDFs are not supported. Say so and stop. A missing path, an unsupported file, or any convert failure other than one `busy` retry writes no files.

The path is absolute and in a folder OmniMarkz is allowed to read. Call `probe_path`, then `convert_file` with `formats: ["mzjson"]`. If the server answers `busy`, wait and retry once. A second `busy` writes no files and stops. If OmniMarkz is not connected, point the user at **OmniMarkz → Preferences → MCP** and write no files.

When `convert_file` returns more than one `.mzjson`, use the unsuffixed file unless the user names a layout. A named layout uses that layout’s `.mzjson`.

Page 1 is the first page. The user may name a layout, a page number, or both.

- A named page is the only page searched. If that page has no meaningful image, write no files, tell the user, and stop.
- A named layout and no page uses page 1 of that layout. If page 1 has no meaningful image, use the first meaningful image later in that layout. If the layout has none, write no files, tell the user, and stop.
- No layout and no page uses page 1 of the unsuffixed layout, then the first meaningful image later in that layout. If it has none, write no files, tell the user, and stop.

A meaningful image is an `imageFrame` whose `content.type` is `preview` and whose `content.href` is a local image file. Open that file. Its width and height are that file’s pixel size. An image whose width is under 100 or whose height is under 100 is ignored. A 100×100 image is kept. `content.type` `empty` and `missing` are ignored. `content.type` `linked` is a URL. Do not download it. A page PNG (`_pg1.png` and the like) is not the social image. If an `mzjson`-only convert does not write `content.href`, stop and do not invent a path. Request `formats: ["mzjson", "png"]` once. If the local file is still missing, write no files.

The photo is the first meaningful image in that search, left to right and then top to bottom on the chosen page, then later pages only when the page was not named. A later frame with the same bytes as the chosen photo is not a second file. A frame of at least 100×100 is still eligible when an earlier copy under 100×100 was ignored.

The title is the first text on the page the photo came from that is not a page number or a running header, in that same order. If that page has no such text, use the source file name and say so in the text file.

Look at the chosen photo file before writing the caption. The caption is one or two sentences in the piece’s voice, using the source’s wording where it quotes the piece. It has no hashtag and no URL.

Center-crop that photo to the site’s aspect ratio, then scale it to the site’s pixel width and height. Do not stretch, pad, or letterbox, and do not generate a different scene. When either side of the crop is smaller than the site size, upscale and tell the user that the source was smaller.

Write both files in the source file’s folder. The JPEG name is `{source-basename}_{Site}_{YYYYMMDDHHMMSS}.jpg`. `{Site}` is the site name the user said, with spaces removed, as in `Instagram`. The timestamp is the local time when the file is written, 14 digits, as in `myDesignFile_Instagram_20261029155323.jpg`. The text file uses that same basename with `.txt`. If either name already exists, append `_2`, then `_3`, and so on, before the extension, and use that suffix for both files. The first file has no `_1`.

The text file contains `Title:` and `Caption:`. When the title is the file name, it says the file has no title. Tell the user both paths. When the image was upscaled, say so in the reply.

Do not post, upload, or create a WordPress draft from the design file.

Field notes, the crop, and the filename are in [reference.md](reference.md).
