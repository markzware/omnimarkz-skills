# REST and block reference

## Endpoints

The helper calls these. Do not send the password yourself.

| Action | Request |
|---|---|
| Test | `GET /wp-json/wp/v2/users/me` |
| Upload | `POST /wp-json/wp/v2/media` with the raw image bytes. A photograph uses `Content-Type: image/jpeg`. A `.png` uses `Content-Type: image/png`. Send `Content-Disposition: attachment; filename="name.jpg"`. |
| Media text | `POST /wp-json/wp/v2/media/{id}` with JSON `title`, `alt_text`, `caption`, `description` |
| Create draft | `POST /wp-json/wp/v2/posts` with `status: "draft"`, Gutenberg markup in `content`, and `featured_media` |
| Check | `GET /wp-json/wp/v2/posts/{id}?context=edit` and compare `content.raw` |

Every request sends `User-Agent: Mozilla/5.0` and Basic auth for the WordPress login plus the application password, with spaces removed. A blocked response from a host such as Cloudflare usually means the user agent or the network path was rejected. Show the HTTP status and stop. Do not retry by printing the password.

## Gutenberg blocks

```html
<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Section title</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Body text with source wording preserved.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":123,"sizeSlug":"large","linkDestination":"none"} -->
<figure class="wp-block-image size-large"><img src="https://example.com/wp-content/uploads/photo.jpg" alt="What the photograph shows." class="wp-image-123"/></figure>
<!-- /wp:image -->

<!-- wp:cover {"url":"https://example.com/wp-content/uploads/background.jpg","id":124,"dimRatio":30,"customOverlayColor":"#000000","isUserOverlayColor":true,"minHeight":520,"minHeightUnit":"px","isDark":true,"align":"full","style":{"color":{"text":"#ffffff"}}} -->
<div class="wp-block-cover alignfull is-dark" style="min-height:520px;color:#ffffff"><span aria-hidden="true" class="wp-block-cover__background has-background-dim-30 has-background-dim" style="background-color:#000000"></span><img class="wp-block-cover__image-background wp-image-124" alt="" src="https://example.com/wp-content/uploads/background.jpg" data-object-fit="cover"/><div class="wp-block-cover__inner-container"><!-- wp:paragraph {"style":{"color":{"text":"#ffffff"}}} -->
<p class="has-text-color" style="color:#ffffff">Text that sits on the photograph.</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover -->

<!-- wp:group {"align":"full","style":{"color":{"background":"#c2185b","text":"#ffffff"},"spacing":{"padding":{"top":"2em","bottom":"2em","left":"1.5em","right":"1.5em"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull has-text-color has-background" style="color:#ffffff;background-color:#c2185b;padding-top:2em;padding-right:1.5em;padding-bottom:2em;padding-left:1.5em"><!-- wp:paragraph {"style":{"color":{"text":"#ffffff"}}} -->
<p class="has-text-color" style="color:#ffffff">Text on a flat color taken from the preview.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:columns -->
<div class="wp-block-columns"><!-- wp:column -->
<div class="wp-block-column"><!-- wp:paragraph -->
<p>Left region, top to bottom.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column"><!-- wp:image {"id":125,"sizeSlug":"large","linkDestination":"none"} -->
<figure class="wp-block-image size-large"><img src="https://example.com/wp-content/uploads/inset.jpg" alt="The photograph beside that text." class="wp-image-125"/></figure>
<!-- /wp:image --></div>
<!-- /wp:column --></div>
<!-- /wp:columns -->
```

Match the preview: a cover when a photograph is the background, a group when the background is a flat color, and columns when regions sit side by side. Set the text color on the heading and paragraph, not only on the cover or group. Keep line breaks that are in the story text with `<br>`. Use one paragraph when the story is one paragraph and the preview only wraps it. Use a heading for a section title and a list only when the source is a set of short labels. Put the alt text in the `img` tag. The image block does not keep alt text in its JSON. Leave the cover background `img` alt empty; the description belongs on that media item.

## What to leave out

Skip empty image frames, icon-sized frames, rules, letter shapes, and ornamental flourishes. A graphic that is only a color field is a background color, not an upload. If two assets are the same file, use one media item. A photo that appears twice in the design appears once in the post. Do not upload the page PNG.

## Publish

`create-post` always sends `draft`. Publishing is a separate, explicit request. Do not change a draft to published while creating it.

## Fonts

`map-fonts` reads a local MZJSON file and prints one line per resolved face. It contacts Google for an exact match. It does not read the WordPress password and does not call WordPress. `install-fonts` uploads the Latin files, activates those faces for the current theme, and prints JSON. Omitted MZJSON fields are absent, not null.

### Where the face lives

`document.resources.fonts` is an object keyed by `font-{id}`. Each font has `family`, `postscriptName`, and `embedded`. A text frame has `composition.lines[].runs[]`. A run has `text`, `fontRef`, `fontWeight`, and `fontStyle` (`italic` or `normal`). `document.stories` has `content` only. Paragraph styles and character styles have `name` and `basedOn` only.

Join a heading or paragraph to the runs whose `text` concatenates to that block’s wording. A composition line break is a wrap. Use one paragraph when the story is one paragraph and the preview only wraps it.

`fontRef` wins when that id is a key in `fonts`. `font-0`, or any other missing id, is no font for that run. A missing `fonts` object is the same as an empty one. When no run resolves:

- No fonts listed: skip the font step. The reply says no fonts were listed.
- One family: use it for every text block.
- More than one family: list a substitute for each, set no `font-family`, and say the file did not say which text uses which font.

A normal conversion writes `fontRef` on every run. The empty and two-family cases are hand-edited files.

### Cleanup

Do this before matching:

1. Remove one leading subset tag of six ASCII letters and a plus sign. `ABCDEF+MinionPro-Regular` becomes `MinionPro-Regular`.
2. Remove one trailing `MT` token. `Arial Bold MT` becomes `Arial Bold`. `Arial-BoldMT` becomes `Arial-Bold`. `TimesNewRomanPS-BoldMT` becomes `TimesNewRomanPS-Bold`. `MT` is not a face word.
3. From `family`, remove up to two trailing face words: Regular, Roman, Book, Bold, Italic, Oblique, Light, Medium, Semibold, SemiBold, Demi, DemiBold, Black, Heavy. Stop when the name already matches a catalog family or a substitute row, so `Times New Roman` stays whole. `Minion Pro Bold Italic` and `Minion Pro Italic Bold` both become `Minion Pro`.
4. When `family` is missing, the match name is `postscriptName` after the subset tag, the trailing `MT`, and one trailing face suffix: `-Regular`, `-Roman`, `-Book`, `-Bold`, `-Italic`, `-BoldItalic`, `-BoldOblique`, `-Oblique`, `-Light`, `-Medium`, `-Semibold`, `-SemiBold`, `-Demi`, `-DemiBold`, `-Black`, `-Heavy`. `TimesNewRomanPS-BoldMT` then matches `timesnewromanps` as well as `timesnewromanpsmt`.

The reply shows the original `family`, or the original `postscriptName` when `family` is missing.

The run’s `fontWeight` number wins when it is present. A live conversion writes 300, 400, 500, 700, or 900. That number wins over a face word, so a live Semibold file is not weight 600. When `fontWeight` is absent, a removed face word or a PostScript suffix sets the weight, even if `family` is present. Bold is 700. Semibold, SemiBold, Demi, and DemiBold are 600. Black and Heavy are 900. Medium is 500. Light is 300. Regular, Roman, Book, or anything else is 400. `Minion Pro` with `MinionPro-Bold` and no `fontWeight` is 700. The same pair with `fontWeight` 400 stays 400.

Italic is set when `fontStyle` is `italic` or `oblique`. When `fontStyle` is absent, a removed face word or the PostScript name that contains Italic or Oblique sets italic. `fontStyle` `normal` does not.

### Match order

Normalize by ignoring case, spaces, hyphens, and underscores.

1. Exact. The family is in the Google catalog. The catalog category strings map as `Serif` → `serif`, `Sans Serif` → `sans-serif`, `Monospace` → `monospace`, `Display` → `sans-serif`, `Handwriting` → `cursive`. An exact match uses that generic.
2. Substitute. Use this table. A substitute row uses the generic in the table.

| Normalized source family | Web font | Generic | Kind |
|---|---|---|---|
| `times`, `timesnewroman`, `timesnewromanps`, `timesnewromanpsmt` | Tinos | serif | metric |
| `georgia` | Gelasio | serif | metric |
| `arial`, `arialmt`, `helvetica`, `helveticanue`, `helveticaneue` | Arimo | sans-serif | metric |
| `calibri` | Carlito | sans-serif | metric |
| `cambria` | Caladea | serif | metric |
| `courier`, `couriernew` | Cousine | monospace | metric |
| `palatino`, `palatinolinotype`, `bookantiqua` | EB Garamond | serif | approximate |
| `garamond`, `adobegaramond`, `garamondpremier`, `minion`, `minionpro` | EB Garamond | serif | approximate |
| `caslon`, `adobecaslon` | Libre Caslon Text | serif | approximate |
| `baskerville`, `baskervilleoldface`, `itcbaskerville` | Libre Baskerville | serif | approximate |
| `bodoni`, `bodonimt`, `didot` | Bodoni Moda | serif | approximate |
| `verdana` | Open Sans | sans-serif | approximate |
| `tahoma` | Noto Sans | sans-serif | approximate |
| `candara` | Nunito Sans | sans-serif | approximate |
| `trebuchet`, `trebuchetms` | Mulish | sans-serif | approximate |
| `segoeui` | Open Sans | sans-serif | approximate |
| `impact` | Anton | sans-serif | approximate |
| `comicsans`, `comicsansms` | Comic Neue | cursive | approximate |
| `futura`, `futurapt`, `futurastd` | Jost | sans-serif | approximate |
| `gillsans`, `gillsansmt` | Cabin | sans-serif | approximate |
| `myriad`, `myriadpro` | Source Sans 3 | sans-serif | approximate |
| `frutiger`, `frutigernext` | Source Sans 3 | sans-serif | approximate |
| `univers` | Roboto | sans-serif | approximate |
| `franklingothic`, `itcfranklingothic` | Libre Franklin | sans-serif | approximate |
| `gotham` | Montserrat | sans-serif | approximate |
| `proximanova` | Montserrat | sans-serif | approximate |
| `avenir`, `avenirnext` | Nunito Sans | sans-serif | approximate |
| `optima` | Philosopher | sans-serif | approximate |
| `rockwell` | Roboto Slab | serif | approximate |

3. Symbol. `wingdings`, `webdings`, `symbol`, `zapfdingbats`, and any normalized name containing `dingbat` get no web font.
4. Anything else gets no web font.

An exact catalog family wins over the table. `Montserrat` stays Montserrat and the kind is exact.

Catalog faces are keys such as `400` and `400i`. The `i` suffix is italic. When the requested weight is missing on that axis, use the nearest weight by numeric distance. A tie uses the lower weight. Requested 600 against 400 and 700 becomes 400, and the reply names 400. Carlito and Philosopher have 400 and 700, so a Semibold face with no `fontWeight` requests 600 and uses 400. When the family has no italic, use the roman file, do not set `font-style`, and say italic was not available.

The family stack is the web font, then the generic. The web font name is quoted: `"Arimo", sans-serif` and `"EB Garamond", serif`. The source desktop family is not in the stack.

The catalog is `https://fonts.google.com/metadata/fonts`. It names families and categories. It has no woff2 URLs. When it cannot be loaded, exact matches are skipped, substitute rows still apply, and the reply says the full font list could not be loaded.

### Latin files

`install-fonts` downloads each face from `https://fonts.googleapis.com/css2` with this User-Agent:

`Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`

Keep the `/* latin */` block only. Do not upload `latin-ext`, cyrillic, greek, vietnamese, or any other subset. A variable file whose `font-weight` is a range that covers the chosen weights on that roman or italic axis is uploaded once. A static family is one file per weight and italic.

WordPress 6.5 or later, and an account that can edit theme options, can add fonts. Creating the draft installs the faces and activates them for the current theme. There is no second confirmation. A family already on the site is reused. A missing face of that family is uploaded. An existing face is not replaced. Activation writes each installed face onto that theme’s active font list. A face already on the list stays there, and other active families stay as they are. One failed face uses the raw stack. A face that is active keeps the preset. The theme’s default text font stays as it was. Embedded font binaries stay out of WordPress.

### Block markup

When every run in the block resolves to the same family, weight, and italic, set that family on the block. Set `font-weight` only when the weight is not 400. Set `font-style` `italic` only when the chosen face is italic.

When runs differ in family, weight, or italic, the block takes the first run. Each later run that differs is a span with its own family, weight, and italic. The wording stays the source wording.

Active face. The block attribute `fontFamily` is the preset, and the element carries the class. Use this only when `install-fonts` reports `active` true:

```html
<!-- wp:paragraph {"fontFamily":"var:preset|font-family|arimo"} -->
<p class="has-arimo-font-family">Source wording.</p>
<!-- /wp:paragraph -->
```

Same family at 400 and at 700. The block stays at 400, so it has no `font-weight`. The bold span carries 700:

```html
<!-- wp:paragraph {"fontFamily":"var:preset|font-family|arimo"} -->
<p class="has-arimo-font-family">Regular words <span class="has-arimo-font-family" style="font-weight:700">bold words</span></p>
<!-- /wp:paragraph -->
```

A face that is not installed, or that is installed but not activated, uses the raw stack and does not use `has-{slug}-font-family`:

```html
<!-- wp:paragraph {"style":{"typography":{"fontFamily":"\"Arimo\", sans-serif","fontWeight":"700"}}} -->
<p style="font-family:&quot;Arimo&quot;, sans-serif;font-weight:700">Source wording.</p>
<!-- /wp:paragraph -->
```

`"EB Garamond", serif` is the same shape when the name contains a space.

`content.raw` must still contain the preset or the raw stack, and the visible wording must match the source. Do not put a Google Fonts stylesheet tag in the post. An unmatched or symbol family stays on the theme font, and the reply names it.

The reply lists every used source family once. It includes a weight of 400 when that family is also used at another weight. It says which families were added, which were already on the site, which were activated for this theme, which were already active, and which files were not added.
