# OmniMarkz skills

Agent skills for OmniMarkz. This repository is the install and usage page.

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** before using a skill. OmniMarkz MCP is the local app you connect there. This repository does not give a remote URL for that MCP server.

## Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill '*' -g -y
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

Those commands install every skill in this repository. Each skill section below has the Cursor command for that skill alone.

## WordPress draft from a design file

### Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-to-wordpress -g
```

### ChatGPT

ChatGPT installs the skill by downloading the zip:

https://markzware.com/downloads/skills/design-file-to-wordpress.zip?v=4

The Cursor, Claude, and Codex commands above are not the ChatGPT install.

### Guide

The published guide for this skill is https://markzware.com/omnimarkz/agent-skills/design-file-to-wordpress/

The skill can be installed and used without opening that page.

## What changed between two versions

Compare two versions of an InDesign, Publisher, QuarkXPress, or PDF file and report the text and photos that changed.

### Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-what-changed -g
```

### ChatGPT

ChatGPT installs the skill by downloading the zip:

https://markzware.com/downloads/skills/design-file-what-changed.zip

The Cursor command above is not the ChatGPT install. The report stays on the Mac.

## License

Apache-2.0. See [LICENSE](LICENSE).
