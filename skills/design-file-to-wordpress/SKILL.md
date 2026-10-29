---
name: design-file-to-wordpress
description: >-
  Converts an Adobe InDesign, Microsoft Publisher, QuarkXPress, or PDF file
  with OmniMarkz and creates a WordPress draft through the REST API. Use when
  the user wants a design file, brochure, magazine, or INDD, PUB, QXP, or PDF
  turned into a WordPress post, or when a Google font can stand in for a font
  the design file uses, or when setting up a WordPress application password
  for that workflow.
compatibility: >-
  Requires OmniMarkz, network access, and a WordPress site with the REST API
  and application passwords. The password stays in a local file.
---

# Design file to WordPress draft

Skill version: 4

Install this skill in Cursor:

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-to-wordpress -g
```

ChatGPT installs this skill by downloading the zip: https://markzware.com/downloads/skills/design-file-to-wordpress.zip?v=4

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using this skill.

Convert a supported design file with OmniMarkz, then create a **draft** WordPress post with the REST API. Write the Gutenberg blocks yourself. Do not use a WordPress MCP. Do not publish unless the user explicitly says to publish.

The helper next to this file is [scripts/wp.py](scripts/wp.py). Run it with `python3`. It reads the application password from a local file and never prints it.

## Remembered setup

Config path: `~/.config/design-file-to-wordpress/config.json`

It stores the site URL, the WordPress login, and the path to the password file. It does not store the password.

If the config file exists, use it and do not ask again. If a later request fails authentication, run the connection test again.

If the config file is missing, set it up before converting anything:

1. Ask for the WordPress site URL (the site root, such as `https://example.com`).
2. Tell the user to create an application password:
   - Sign in to WordPress.
   - Open Users → Profile.
   - Under Application Passwords, name it `Design file drafts` and add it.
   - WordPress shows the password once. Copy it then.
3. Tell them to save that password in a local text file, preferably `~/Documents/wordpress-app-password.txt`. The file must not be in a git repo. If Documents syncs through iCloud, say so and offer a local-only folder instead.
4. Ask for the WordPress **login** (the account username, not the display name) and the password **file path**. If they paste the password into chat, stop. Tell them to revoke it in WordPress, save a new one in the file, and send only the path.
5. Test and save:

```bash
python3 scripts/wp.py test --site https://example.com --username LOGIN --password-file ~/Documents/wordpress-app-password.txt --save
```

A successful test prints the user id and login. Leave the password out of every reply.

## OmniMarkz

Supported sources: Adobe InDesign, Microsoft Publisher, QuarkXPress, and PDF. Password-protected PDFs are not supported.

The file must be an absolute path in a folder OmniMarkz is allowed to read. Call `probe_path`, then `convert_file` with `formats: ["mzjson", "png"]` and `resolution: 144`. Only one conversion can run at a time. If the server answers `busy`, wait and retry once.

If OmniMarkz is not connected, tell the user to install it and point the MCP command at the `OmniMarkzMCPServer` helper inside the app bundle. When that path contains a space, `args` must be `[""]`. An empty args list makes some clients split the command on the space and launch the wrong path.

The conversion folder contains the MZJSON, a PNG preview for each page (`_pg1.png`, `_pg2.png`, and so on), and an `_assets` folder of the linked images. Open each page PNG and use it as the picture of how that page is arranged. Do not upload the page PNG, and do not put it in the post.

Text comes from `storyRef` plus `textRange`. Position comes from the item transform. Keep the source wording, including typos and odd capitalization. If the story text itself contains line breaks, keep them. Skip empty image frames, tiny decorative frames, ornamental flourishes, and a second copy of the same story or the same image bytes.

For each page, in page order, read the preview and note:

- What sits behind the type: a photograph, or a flat color or simple graphic field.
- The text color, so light type stays light and dark type stays dark.
- Whether regions sit side by side or stack.
- Where the real photographs sit relative to the text.

Rebuild that page with Gutenberg from the wording and the linked photos:

1. A photograph behind the type becomes a `wp:cover` using that linked photo. Put the page’s headings, text, and inset photos inside the cover. Add a dim overlay only when the type in the preview would be hard to read on the photo.
2. A flat color or a simple graphic field becomes a `wp:group` with a background color close to the preview and the same text color. Do not upload that graphic.
3. A colored box behind one block of text becomes a nested group with that box color.
4. Side-by-side regions become one `wp:columns` block, one column per region, left to right in the same order as the preview.
5. An inset photograph becomes a `wp:image` in that same relative place: beside the text, or in a row under it.

Use the first real photograph that carries the opening page as `featured`. That is a linked photo, not the page PNG.

## Fonts

Look for a Google font that can stand in for a font the design file uses. Set that family on the draft text. List the mapping in the reply.

Read the face from the text frame’s `composition.lines[].runs[]` (`text`, `fontRef`, `fontWeight`, `fontStyle`). Stories and paragraph or character styles do not carry a font. The runs for a heading or paragraph are the ones whose `text` concatenates to that block. A composition line break is a wrap, not a new paragraph.

Before creating the draft, print the mapping. This command does not read the WordPress password:

```bash
python3 scripts/wp.py map-fonts --mzjson /path/to/file.mzjson
```

`map-fonts --offline` skips the Google catalog. Substitute rows still apply. Exact matches do not.

Then install the Latin files and activate those faces for the current theme when the account can add fonts. There is no second confirmation. The command reuses the saved config and does not print the password:

```bash
python3 scripts/wp.py install-fonts --mzjson /path/to/file.mzjson
```

An active face uses `fontFamily` `var:preset|font-family|{slug}` and the class `has-{slug}-font-family`. The JSON from `install-fonts` gives both, and `active` is true. A face that was not installed, or that stayed inactive, uses the raw stack, such as `"Arimo", sans-serif`. Do not put the source desktop family in the stack. Do not add a stylesheet tag. Do not upload an embedded font file. Do not change the theme’s default text font.

The reply names each source family, the web font, the generic, and the kind (exact, metric, or approximate), or that no web font was found. It names a weight other than 400, a nearest weight, and when italic was not available. It says which families were added, which were already on the site, which were activated for this theme, which were already active, and which files were not added. Font rules, the substitute table, and the block markup are in [reference.md](reference.md).

If the conversion returns no page PNG, upload each unique photo as a JPEG and build the post in reading order without inventing columns or background colors: title first, then left to right and top to bottom.

## Photos and the draft

Resize each unique linked photo to a JPEG whose long side is about 1600 pixels. The helper sets `Content-Type` from the file extension. Look at the photograph before writing its text. A flat color field or ornamental flourish is not a photograph, so leave it out of the upload.

- **Alt text:** one or two sentences of what is actually visible.
- **Caption:** a short line.
- **Description:** a fuller sentence or two.

Upload and set that text in one step:

```bash
python3 scripts/wp.py upload --file /tmp/photo.jpg --filename photo-name.jpg \
  --title "Short title" --alt "..." --caption "..." --description "..."
```

The command prints the media id and `source_url`. Use the same alt text on the image block. Caption and description stay on the media item.

Write Gutenberg block markup, not a raw HTML blob. Save it to a file, then:

```bash
python3 scripts/wp.py create-post --title "Post title" --content-file /tmp/post.html \
  --slug post-slug --excerpt "One line from the piece." --featured MEDIA_ID
```

Confirm the reply says `status` is `draft` and `content_match` is true. Give the user the draft link.

Block shapes and the reading-order rules are in [reference.md](reference.md).

## Later files

Read the config and repeat the conversion, upload, and draft steps. Do not ask for the site, login, or password path again unless the config is missing or the test fails. Keep every new post a draft unless the user explicitly says to publish. Never print the password, and never commit the password file.
