# Social image reference

Skill version: 1

## Before converting

1. The user names the site. If they do not, stop. Write nothing.
2. Look up that site’s current recommended pixel width and height. If the lookup returns more than one size and the user did not name one, stop. Write nothing.
3. Remember the site, the size name, the width, and the height for this chat. The next file for that same site and size uses the remembered numbers.
4. A failed lookup stops the run. Do not use 1080, and do not use a size from a different site.

## Conversion

`probe_path`, then `convert_file` with `formats: ["mzjson"]`.

`busy`: wait, retry once, then stop with no files.

Any other failure, including a password-protected PDF, a missing path, or an unsupported file: no files.

More than one `.mzjson`: the unsuffixed file is the default layout. A layout the user names is that layout’s `.mzjson`. Do not mix pages from two layouts.

If a chosen `content.href` is not a local file after the `mzjson` convert, call `convert_file` once more with `formats: ["mzjson", "png"]`. If it is still missing, stop. Do not invent a path.

## Which image

On a page, order frames left to right, then top to bottom.

Keep an `imageFrame` only when all of these are true:

- `content.type` is `preview`
- `content.href` is a local image file
- that file’s pixel width is at least 100 and its pixel height is at least 100

Skip `empty`, `missing`, a `linked` URL, and any page PNG whose name ends in `_pg` plus a number.

Compare file bytes. After one photo is chosen, ignore a later frame with those same bytes. Do not reject a frame of at least 100×100 because a smaller frame with the same bytes was skipped.

Search:

- Named page: that page only. No image there means stop.
- Named layout, no page: page 1 of that layout, then later pages in that layout.
- Neither: page 1 of the unsuffixed layout, then later pages in that layout.

No meaningful image in the search means no files. Do not generate a picture.

## Title and caption

The title is the first text on the photo’s page that is not a page number or a running header, in the same left-to-right, top-to-bottom order. A page number is a short numeric line. A running header is a line repeated from another page.

No such text: the title is the source file name, without the extension. The text file says the file has no title.

Open the chosen photo before writing the caption. One or two sentences. Use the piece’s wording when quoting it. No hashtag. No URL.

## Crop and scale

Let the site size be width `W` and height `H`. Let the photo be width `w` and height `h`.

Center-crop to the aspect ratio `W / H`:

- If `w / h` is wider than `W / H`, keep the full height and crop the width equally from the left and right.
- If `w / h` is taller than `W / H`, keep the full width and crop the height equally from the top and bottom.
- If the ratios match, do not crop.

Scale that crop to `W` by `H`. Do not stretch, pad, or letterbox. If the cropped width is under `W` or the cropped height is under `H`, the scale is an upscale. Write the JPEG at `W` by `H` and say in the reply that the source was smaller.

The file is a JPEG. It is not a PNG, and it is not a new scene.

## Names

Both files go in the source file’s folder.

`{Site}` is the site name the user said, with spaces removed. `Instagram` stays `Instagram`. A placement such as Feed or Story is not part of `{Site}` unless the user used that word as the site name.

The timestamp is local time, 14 digits, `YYYYMMDDHHMMSS`, taken when the files are written.

```text
{source-basename}_{Site}_{timestamp}.jpg
{source-basename}_{Site}_{timestamp}.txt
```

If either of those names exists, use the same suffix on both: `_2`, then `_3`, and so on. Do not write `_1` on the first pair.

```text
myDesignFile_Instagram_20261029155323.jpg
myDesignFile_Instagram_20261029155323.txt
myDesignFile_Instagram_20261029155323_2.jpg
myDesignFile_Instagram_20261029155323_2.txt
```

Text file:

```text
Title: The piece title
Caption: One or two sentences.
```

When the title is the file name:

```text
Title: myDesignFile
The file has no title. The title is the file name.
Caption: One or two sentences.
```

Tell the user both paths. Do not post, upload, or create a WordPress draft.
