# Publishing an OmniMarkz skill

Follow this order. The skill version, the zip, the redirect, the catalog in this repository, the live catalog, and the Convert2IDML catalog copy all describe the same version before that change is on `main`.

1. Skill files that are not ready to list stay off `main`.
2. `version.txt` and the skill version line in `SKILL.md` are the integer this change ships.
3. The zip for that skill is at its `https://markzware.com/downloads/skills/` URL, packed from that skill folder, including that folder’s `README.md`. An anonymous download of `zip_url` matches the folder before the skill is on `main`. If a cache still serves the previous archive, stop.
4. `https://markzware.com/notifications/omnimarkz-2026/skills/<id>` returns HTTP 301 or 302 with `Location: https://github.com/markzware/omnimarkz-skills/tree/main/skills/<id>`. That GitHub folder is the required page for **Open tutorial**. Its `README.md` is the rendered install page. The rule does not apply to `skills.json`.
5. A skill that does not already have a WordPress post gets one draft. The draft is a copy of post 62378, https://markzware.com/?p=62378, slug `design-file-what-changed`, title “What Changed Between Two Design Files”. Copy its styling, format, and content: the eyebrow, title, lede, the “No programming experience required” line, the Codex Desktop Mac walkthrough, the numbered parts, connect OmniMarkz, examples, troubleshooting, and the final review. The install part tells Cursor, Claude, and Codex to install from `markzware/omnimarkz-skills` with the commands in the README, and tells ChatGPT to download the zip. It does not tell those hosts to install by unzipping into `~/.agents/skills/`. Replace that post’s skill-specific wording with this skill. The new post’s slug is the skill id. Leave the new post a draft. Do not publish it. Do not edit or publish post 62378. A skill that already has a post, including the published design-file-to-wordpress guide, does not get a second post. A later edit of a skill updates that same post. A draft stays a draft. A published post stays published.
6. Only after an anonymous request to the redirect returns 301 or 302 and the Location folder is readable with no login, the catalog row is updated in `skills.json` in this repository, copied to `https://markzware.com/notifications/omnimarkz-2026/skills.json`, and copied to `agent-skills/skills.json` in Convert2IDML. The catalog does not wait for the WordPress draft to be published. `tutorial_url` is the redirect address, not a github.com URL, not the WordPress post, not a `?p=` link, and not a `preview=true` link.
7. The repository README and the skill-folder README link a WordPress post only after that post is published. While the post is a draft, those READMEs do not link it. Record that draft’s post id in this file when the draft is created.
8. The skill version, the zip, the redirect, this repository’s catalog, the live catalog, and the Convert2IDML catalog copy all describe that same version before the change is on `main`. When this change creates or updates a WordPress draft, that draft describes that version and remains a draft.
9. The plugin lists every skill folder on `main` and no skill that is not on `main`.
10. Append a dated entry to `CHANGELOG.md` in that same commit. The heading is the date the change lands on `main`. The bullet names the skill and its integer. A change that does not bump a skill version, such as a README edit, still gets a line.

`design-file-to-wordpress` already has a published guide, so this repository does not create a second post for it and does not record a draft post id for it.

`design-file-social-image` draft post id 63459, slug `design-file-social-image`, left as a draft. The tutorial URL is the redirect, not `https://markzware.com/?p=63459`.
`design-file-slides` draft post id 63460, slug `design-file-slides`, left as a draft. The tutorial URL is the redirect, not `https://markzware.com/?p=63460`.
`design-file-to-canva` draft post id 63629, slug `design-file-to-canva`, left as a draft. The tutorial URL is the redirect, not `https://markzware.com/?p=63629`.

## Claude directory

Legal page: `https://markzware.com/legal/omnimarkz-agent-skills/` (WordPress page 63631). An anonymous request on 2026-11-05 returned HTTP 200 at that path. `https://markzware.com/support/` returned HTTP 200 with no redirect, so `supportUrl` is that address.

This submission’s `.claude-plugin/plugin.json` version stays `1.0.0`. Any later commit on the tracked branch `main` raises that `version` before the commit. New directory versions use Scheduled check only. Auto-publish stays off.

Example prompts. Each one needs OmniMarkz on a Mac or on Windows, connected from **OmniMarkz → Preferences → MCP** on a Mac or from **File → Settings… → MCP** on Windows, and a design file the reviewer can open.

1. `Turn this InDesign file into a WordPress draft.`
2. `What text and photos changed between these two PDFs?`
3. `Turn this design file into a Canva design.`

## Cursor Marketplace

Logo copied from `https://markzware.com/wp-content/uploads/2020/05/OmniMarkz_favorite.png` into `assets/omnimarkz.png`.

The submission commit is the commit that adds `.cursor-plugin/plugin.json`. Do not store a token in this file.

## OpenAI directory

Support URL: `https://markzware.com/support/`. An anonymous request on 2026-11-06 returned HTTP 200, so `interface.supportURL` is that address. The privacy URL is `https://markzware.com/legal/omnimarkz-agent-skills/`. The terms URL is `https://markzware.com/legal/license-agreement/`. The website is `https://markzware.com`.

Logo copied from `https://markzware.com/wp-content/uploads/2026/09/OmniMarkz_and_SE_logo_only.png` into `assets/omnimarkz-directory.webp`. The response body is WebP, 1705×1705. `assets/omnimarkz.png` stays the Cursor mark.

Category labels accepted by package validation, from the `plugin_category_unknown` rule on 2026-11-06: Productivity, Creativity, Developer Tools, Business & Operations, Data & Analytics, Communication, Education & Research, Security, Finance, Healthcare, Travel, Entertainment, Other. None of those labels is about documents or files. `interface.category` is `Productivity`.

This submission’s `.codex-plugin/plugin.json` version stays `1.0.0` unless a corrected upload of the unpublished draft is rejected because the version did not change. That corrected ZIP uses `1.0.1` and this file quotes the portal message. Any later OpenAI directory ZIP raises `.codex-plugin/plugin.json` `version` before that ZIP is built. Claude and Cursor manifests are outside that rule.

### OpenAI directory test cases

Positive: `Turn this InDesign file into a WordPress draft.` Expected: the WordPress skill asks for the site and creates a draft. It does not publish. Needs OmniMarkz connected on a Mac from OmniMarkz → Preferences → MCP, or on Windows from File → Settings… → MCP, and a design file the reviewer can open. No sample file is attached.

Positive: `What text and photos changed between these two design files?` Expected: the what-changed skill reports text and photo changes between two design files. Needs OmniMarkz connected on a Mac from OmniMarkz → Preferences → MCP, or on Windows from File → Settings… → MCP, and a design file the reviewer can open. No sample file is attached.

Positive: `Make a social image and a caption from this design file.` Expected: the social-image skill produces an image and a caption. Needs OmniMarkz connected on a Mac from OmniMarkz → Preferences → MCP, or on Windows from File → Settings… → MCP, and a design file the reviewer can open. No sample file is attached.

Positive: `Turn this design file into slides in reading order.` Expected: the slides skill produces a PowerPoint in reading order. Needs OmniMarkz connected on a Mac from OmniMarkz → Preferences → MCP, or on Windows from File → Settings… → MCP, and a design file the reviewer can open. No sample file is attached.

Positive: `Turn this design file into a Canva design.` Expected: the Canva skill produces a Canva design. Needs OmniMarkz connected on a Mac from OmniMarkz → Preferences → MCP, or on Windows from File → Settings… → MCP, and a design file the reviewer can open. No sample file is attached.

Negative: `Convert this .txt file to WordPress.` Expected: no upload. The skill stops because the file is not an InDesign, Publisher, QuarkXPress, or PDF file.

Negative: `Publish the WordPress post now.` Expected: no publish. The skill does not publish unless the user has already asked to publish a specific draft.

Negative: `Make slides.` with no file named. Expected: the skill asks for a design file and does not invent one.
