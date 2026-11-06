# OmniMarkz skills

Agent skills for OmniMarkz. This repository is the install and usage page.

Connect OmniMarkz from **OmniMarkz → Preferences → MCP** on a Mac, or from **File → Settings… → MCP** on Windows, before using a skill. OmniMarkz MCP is the local app you connect there. This repository does not give a remote URL for that MCP server.

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

- [WordPress draft from a design file](#wordpress-draft-from-a-design-file)
- [What changed between two versions](#what-changed-between-two-versions)
- [Social image and caption](#social-image-and-caption)
- [Slides from a design file](#slides-from-a-design-file)
- [Canva design from a design file](#canva-design-from-a-design-file)

## WordPress draft from a design file

The WordPress skill sends a draft to the site the user names. The application password stays in a file on that computer.

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

The Cursor command above is not the ChatGPT install. The report stays on that computer.

## Social image and caption

Make a social image and a caption from an InDesign, Publisher, QuarkXPress, or PDF file. You name the social site. The image stays on that computer. This skill does not post to a social network.

### Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-social-image -g
```

### ChatGPT

ChatGPT installs the skill by downloading the zip:

https://markzware.com/downloads/skills/design-file-social-image.zip

The Cursor command above is not the ChatGPT install. The image stays on that computer.


## Slides from a design file

Turn an InDesign, Publisher, QuarkXPress, or PDF file into a PowerPoint in reading order. The deck stays on that computer. This skill does not upload it.

### Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-slides -g
```

### ChatGPT

ChatGPT installs the skill by downloading the zip:

https://markzware.com/downloads/skills/design-file-slides.zip

The Cursor command above is not the ChatGPT install. The PowerPoint file stays on that computer.

## Canva design from a design file

Turn an InDesign, Publisher, QuarkXPress, or PDF file into a Canva design. Connect OmniMarkz from **OmniMarkz → Preferences → MCP** on a Mac, or from **File → Settings… → MCP** on Windows, and connect the Canva MCP. The Canva skill sends the design to the Canva account the user connects. The link includes the source wording and the file’s photographs. Those edits are saved as part of the run.

### Cursor

```bash
npx skills add markzware/omnimarkz-skills --skill design-file-to-canva -g
```

### ChatGPT

ChatGPT installs the skill by downloading the zip:

https://markzware.com/downloads/skills/design-file-to-canva.zip

The Cursor command above is not the ChatGPT install.

## Changes

See [CHANGELOG.md](CHANGELOG.md).

## License

Apache-2.0. See [LICENSE](LICENSE).

The privacy page for these skills is https://markzware.com/legal/omnimarkz-agent-skills/. The license agreement is https://markzware.com/legal/license-agreement/.
