---
name: design-file-what-changed
description: >-
  Compares two versions of an Adobe InDesign, Microsoft Publisher,
  QuarkXPress, or PDF file with OmniMarkz and writes a local markdown report
  of the text and photos that changed. Use when someone asks what changed
  between two versions of an INDD, PUB, QXP, or PDF file.
compatibility: >-
  Requires OmniMarkz on macOS, connected as an MCP server. Password-protected
  PDFs are not supported. The report stays on the Mac.
---

# What changed between two versions

Skill version: 1

Install this skill in Cursor:

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-what-changed -g
```

ChatGPT installs this skill by downloading the zip: https://markzware.com/downloads/skills/design-file-what-changed.zip

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using this skill.

Compare two design files by converting each one to MZJSON with OmniMarkz, then write one local markdown report. Do not upload the report. Do not create a WordPress post. Do not request any format other than `mzjson`.

The comparison steps are in [reference.md](reference.md). Follow them. Do not compare the two documents by eye.

## Before converting

Supported sources are Adobe InDesign, Microsoft Publisher, QuarkXPress, and PDF. If a file is not one of those, say so and stop.

If OmniMarkz is not connected, tell the user to connect it from **OmniMarkz → Preferences → MCP**. Do not invent a hand-edited config.

Guess which file is newer with the version-token rules in reference.md.

- A version token is case-insensitive. It sits at the end of the filename stem, or it is set off by a space, `_`, or `-`.
- Tokens that count: `v` plus an integer (`v2`, `v02`, `v.2`, `v_2`, `v-2`); `ver` or `version` plus an integer; `rev` or `revision` plus an integer; `rev` plus one letter (`revA`, `rev B`); `round` plus an integer; `r` plus an integer only when a space, `_`, or `-` comes immediately before the `r` (`_r2`, `-r2`).
- `v02` and `v2` are the same integer. When a name has more than one token, the token closest to the extension is the version. `Brochure_v2_revB.indd` is `rev B`.
- These are not version tokens: `copy`, `final`, `new`, `old`, `draft`, `wip`, `proof`, a date in the name, and a bare trailing number such as `Brochure2`.
- The names pick a winner only when both tokens are the same kind. `v`, `ver`, and `version` are one kind. `rev` and `revision` integers are another. `rev` letters are another. `round` is another. A delimited `r` is another. The greater token is newer. `v2` and `rev3` do not pick a winner.
- When the names do not pick a winner, the later modification date is the guess. When those dates are equal or cannot be read, name either file in the question.

Ask exactly:

`Is {filename} the newer version?`

Use the file’s name, including its extension. Wait for yes or no. Yes keeps that file as the newer one. No makes the other file the newer one. Do not convert until the user answers.

## Convert

Each path must be absolute and in a folder OmniMarkz is allowed to read. If the two path strings are the same, do not call `convert_file`. Write the report described in reference.md for that case and stop.

Otherwise call `probe_path`, then `convert_file` with `formats: ["mzjson"]`, one file at a time. Convert the earlier file, then the newer file. If the server answers `busy`, wait and retry that call once. If it is still `busy`, stop. Do not write a report that uses the six headings.

If `convert_file` returns more than one `.mzjson`, compare the unsuffixed file, which is the default layout, unless the user names a layout. Mention that file in the report.

If either conversion fails, including `password_unsupported`, `license_required`, `conversion_failed`, or `allowlist_rejected`, say what failed and stop. A password-protected PDF is unsupported. Do not leave a report that uses the six headings.

Two different strings that `probe_path` resolves to the same file are still two conversions.

## Report

Run the comparison program in reference.md. It writes `what-changed.md` in the newer file’s folder when that folder is writable, and prints the path. If that folder is not writable, ask for a folder and do not write the report until the user gives one.

The report lists added text, removed text, reworded text, added photos, removed photos, and linked photos whose URL changed. Spaces and line breaks are differences. Unpaired wording is added or removed. Do not pair passages by meaning.
