# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A source-of-truth collection of Claude Code **subagents** and **skills**, installed into the user's global Claude config (`~/.claude/`) via symlinks. There is no application code, build step, test suite, or linter — the "code" is Markdown prompt files with YAML frontmatter, plus a small Node installer script.

## Commands

```sh
npm run link                      # symlink agents/skills into ~/.claude/
node bin/link.mjs --dry-run       # (-n) preview what would be linked
node bin/link.mjs --force         # (-f) replace existing entries in ~/.claude/
```

No dependencies to install; `bin/link.mjs` uses only Node built-ins (ESM).

## Layout and install model

- `agents/<name>.md` — one file per subagent. Linked as a **file** symlink to `~/.claude/agents/<name>.md`. Frontmatter: `name`, `description`, `tools`.
- `skills/<name>/SKILL.md` — one **directory** per skill (so it can hold supporting files). The whole directory is symlinked to `~/.claude/skills/<name>`. Frontmatter: `name`, `description`.
- `bin/link.mjs` only picks up `*.md` files directly under `agents/` and directories directly under `skills/`. Anything else is ignored.
- Because installs are symlinks, edits to files here take effect in `~/.claude/` immediately — no re-link needed unless you add a new agent/skill. Existing non-symlink entries at the destination are skipped unless `--force` is passed (which deletes them).

## Agent vs. skill for the same capability

`obsidian-plugin-finder` exists in both forms, and they are written differently on purpose:

- The **skill** runs in the main conversation: it may ask one clarifying question and uses a lighter search/report flow.
- The **agent** runs as a delegated subagent with no follow-up turn: it must not ask questions (enumerates interpretations instead), fans out searches in parallel, adds download/star/maintenance evaluation via `community-plugin-stats.json` and GitHub, and outputs only the report for the parent agent.

They are separate prompts, not generated from a shared source — when changing shared behavior (sources, match grades, report structure, hard rules), update both deliberately. They currently differ on the staleness threshold (skill: >2 years since update; agent: >18 months since release or >12 months since last commit).

## BizWiz drafts

`skills/bizwiz-claude/` and `skills/bizwiz-grok/` are competing drafts of the same business-research skill, written by different models. `bizwiz-grok` targets Grok's harness (its tool names and `when-to-use` key don't work in Claude Code). Both split instructions across `SKILL.md` (workflow), `sources.md` (catalog), and `template.md` (Obsidian note layout) — keep rules defined in one file only.

## Skill frontmatter notes

Verified against Claude Code docs: `argument-hint`, `when_to_use` (underscore), `allowed-tools`, `model`, `context: fork`, and `disable-model-invocation` are valid; `description` + `when_to_use` are truncated at 1,536 chars combined. Use `${CLAUDE_SKILL_DIR}` to give subagents absolute paths to supporting files. The subagent tool is `Agent` (formerly `Task`); the built-in `Explore` agent has no web tools, so web-research fan-outs use `general-purpose`.

The `description` frontmatter is what Claude uses to decide when to trigger a skill or delegate to an agent, so treat it as functional, not documentation.
