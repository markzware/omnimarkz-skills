# Slides from a design file

Turn an InDesign, Publisher, QuarkXPress, or PDF file into a PowerPoint in reading order.

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using this skill. OmniMarkz MCP is the local app you connect there. This repository does not give a remote URL for that MCP server.

The PowerPoint file stays on the Mac, beside the design file. This skill does not upload it.

## Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-slides -g
```

## Claude

```text
/plugin marketplace add markzware/omnimarkz-skills
/plugin install omnimarkz@omnimarkz-skills
```

## Codex

```text
codex plugin marketplace add markzware/omnimarkz-skills
codex plugin add omnimarkz@omnimarkz-skills
```

## ChatGPT

ChatGPT installs the skill by downloading the zip:

https://markzware.com/downloads/skills/design-file-slides.zip

The Cursor, Claude, and Codex commands above are not the ChatGPT install.
