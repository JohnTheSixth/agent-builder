Personal project designed to streamline agent skill development.

A collection of Claude Code **skills** and **subagents** written as Markdown prompts, with helper
scripts where a job needs deterministic steps. `npm run link` installs them into `~/.claude/` as
symlinks, so edits here take effect immediately.

## Contents

| Name | Skill | Agent | What it does |
|---|---|---|---|
| bizwiz | `skills/bizwiz/` (`/bizwiz`) | — | Researches the reputation and legitimacy of one named business, then writes a cited Markdown/Obsidian note answering "should I contact this business?" |
| obsidian-plugin-bootstrap | `skills/obsidian-plugin-bootstrap/` (`/obsidian-plugin-bootstrap`) | — | Starts a new Obsidian plugin from the official sample template, with lint and build passing. |
| obsidian-plugin-finder | `skills/obsidian-plugin-finder/` | `agents/obsidian-plugin-finder.md` | Finds Obsidian plugins (or workarounds) for a described workflow. |
| pdf-fix | `skills/pdf-fix/` (`/pdf-fix`) | `agents/pdf-fix.md` | Turns scanned book PDFs into clean, straight, OCR'd, compact PDFs with PdfCraft. |

Skills run in the main conversation and can ask questions, for example before removing pages or
choosing a plugin ID. Agents package the same capability for delegation: they ask nothing and
return one report.

## Install into Claude Code

```bash
npm run link            # symlink agents/*.md and skills/* into ~/.claude
npm run link -- --force # replace existing entries
node bin/link.mjs -n    # dry run: show what would be linked
```

Run it from the main checkout, not from a worktree, so the links point at `master`. Re-run it only
when you add a new skill or agent.

## Skills

### bizwiz

Researches one specific business before you hire, buy from or visit it. It sweeps reviews and
complaints (Google, Yelp, Facebook, Reddit, Trustpilot, BBB, X), industry review sites, licensing,
business registration, courts, regulators and news. It then writes or updates a Markdown note
with a link behind every claim.

- Usage: `/bizwiz <business name> [location] [industry] [concerns] [path/to/note.md] [quick]`.
  `quick` runs a shorter pass without subagents.
- Portable: written for any agent harness (Claude, ChatGPT/Codex, Grok). It needs web search. It
  works better with page fetching, native X search, subagents and file access, and falls back
  when any of these are missing.
- Files: `SKILL.md` (workflow and rules), `sources.md` (search technique, evidence levels,
  sources), `template.md` (note layout).

### obsidian-plugin-bootstrap

Creates a new Obsidian community plugin from
[obsidian-sample-plugin](https://github.com/obsidianmd/obsidian-sample-plugin). It downloads
the template fresh each run and changes only the plugin's own details: `package.json`/lock,
`manifest.json`, `versions.json`, `LICENSE` and `README`. The template's current dependencies,
ESLint config, release workflows and `AGENTS.md` are kept as they are. It checks the ID, name,
description and version against Obsidian's submission rules. It renames the sample classes and
removes the sample code that `eslint-plugin-obsidianmd` flags, so `npm run build` and
`npm run lint` both pass. It ends with a first git commit.

- Usage: `/obsidian-plugin-bootstrap <plugin name> [target folder]`.
- Requires `git`, Node.js 20+ and `npm`, plus network access to GitHub and the npm registry.
- To check the arguments without creating anything:
  `node skills/obsidian-plugin-bootstrap/scripts/bootstrap.mjs --check --dir ./my-thing --id my-thing --name "My Thing" --description "Does a thing." --author Me`
  (`--help` lists every option).

### obsidian-plugin-finder

Searches the official Obsidian plugin directory, the `community-plugins.json` list, the forum and
GitHub for plugins that fit a task. It reports matches, close matches, or a clear "nothing
exists" with workarounds. The agent version also checks downloads, stars and how recently each
plugin was maintained.

- Usage: ask whether a plugin exists for something, or describe an Obsidian workflow you want
  automated.

### pdf-fix

Turns a scanned book PDF (Internet Archive, photocopies, flatbed scans, two-page spreads) into a
clean, searchable, much smaller PDF with PdfCraft. It removes covers and duplicate scans, turns
sepia paper white, keeps photos in grayscale, splits spreads, straightens pages, and sets a
uniform page size (default 6×9 in). It also runs OCR, matches PDF page labels to the printed
numbers, and compresses with JBIG2.

- Usage: `/pdf-fix <input.pdf> [output folder]`.
- Requirements:
  - [PdfCraft](https://github.com/storytold/pdfcraft) `pdfcraft-cli` ≥ 0.21
    (`brew install pdfcraft-cli`, the Linux packages, or the release zips). The desktop app
    provides the built-in OCR models.
  - Python 3.8+ (standard library only) for `skills/pdf-fix/scripts/pdffix.py`.
  - ImageMagick 7 (`magick`) or 6 (`convert`), for two-page spreads, verification and contact
    sheets.
  - Optional: Tesseract (a second OCR engine PdfCraft can use) and poppler's `pdfimages` (shows
    image encodings).
- To check the requirements: `python3 skills/pdf-fix/scripts/pdffix.py doctor`

## Adding a skill or agent

- Skill: `skills/<name>/SKILL.md` with `name` and `description` frontmatter, plus any supporting
  files in the same folder.
- Agent: `agents/<name>.md` with `name`, `description` and `tools` frontmatter.
- Run `npm run link`, then add a row to the table above. See `CLAUDE.md` for frontmatter details
  and how the skill and agent versions of a capability differ.
