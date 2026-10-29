# What changed between two versions

Compare two versions of an InDesign, Publisher, QuarkXPress, or PDF file and report the text and photos that changed.

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using a skill. OmniMarkz MCP is the local app you connect there. This repository does not give a remote URL for that MCP server.

## Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-what-changed -g
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

https://markzware.com/downloads/skills/design-file-what-changed.zip

The Cursor, Claude, and Codex commands above are not the ChatGPT install.

The report stays on the Mac. This skill does not publish the report.
