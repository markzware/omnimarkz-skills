# Canva design from a design file

Turn an InDesign, Publisher, QuarkXPress, or PDF file into a Canva design.

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using this skill. OmniMarkz MCP is the local app you connect there. This repository does not give a remote URL for that MCP server.

Connect the Canva MCP as well. This skill creates the design through that connection. It does not call the Canva REST API.

The design link includes the source wording and the file’s photographs. Those edits are saved as part of the run.

## Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-to-canva -g
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

https://markzware.com/downloads/skills/design-file-to-canva.zip

The Cursor, Claude, and Codex commands above are not the ChatGPT install.
