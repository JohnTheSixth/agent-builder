---
name: obsidian-plugin-bootstrap
description: >
  Bootstrap a new Obsidian community plugin from the official obsidian-sample-plugin template:
  clone it fresh, set the plugin's id, name, description, author, version and minAppVersion in
  package.json, package-lock.json, manifest.json and versions.json (keeping the template's own
  current scripts, dependencies, ESLint flat config and release workflows), rename the sample
  classes, strip sample code until `npm run lint` passes, and make the first git commit. Use when
  the user wants to start, create, scaffold, set up or bootstrap a new Obsidian plugin, or
  invokes /obsidian-plugin-bootstrap.
argument-hint: "<plugin name> [target folder]"
---

# /obsidian-plugin-bootstrap — new Obsidian plugin from the official template

The deterministic work is done by `${CLAUDE_SKILL_DIR}/scripts/bootstrap.mjs` (Node built-ins
only). It clones https://github.com/obsidianmd/obsidian-sample-plugin **at run time** and changes
only the fields that identify the plugin. Never write `package.json` dependencies, scripts or
lint config yourself: the template's own are always current, and copies in this skill would
go stale.

Run `node ${CLAUDE_SKILL_DIR}/scripts/bootstrap.mjs --help` for every option.

## Requirements

`git`, Node.js 20+ and `npm` on PATH, plus network access to GitHub and the npm registry.

## 1. Gather the details

Arguments: `$ARGUMENTS`. The first is the plugin's display name; the optional second is the
target folder.

Work out sensible defaults, then ask for what's missing **in one message** and show the
defaults so the user can just confirm:

| Field | Flag | Default / rule |
|---|---|---|
| Display name | `--name` | From the argument. Must not contain "Obsidian" or "Plugin". Basic Latin letters, digits, spaces, `-`, `+` and `()` only. |
| Plugin ID | `--id` | Kebab-case of the name (`Word Counter` → `word-counter`). Must not contain `obsidian` or end in `plugin`. **It can't change after release.** |
| Target folder | `--dir` | `./<id>`. Its folder name should equal the ID, because Obsidian loads plugins from `<Vault>/.obsidian/plugins/<id>/`. |
| Description | `--description` | Required. Start with a verb ("Count words in…"), keep it to 250 characters or fewer, end with a period, and use no emoji. Don't start with "This is a plugin". |
| Author | `--author` | Ask. Suggest `git config user.name` if it's set. |
| Author URL | `--author-url` | Optional, for example their GitHub profile. |
| Funding URL | `--funding-url` | Leave it out unless they take donations. Obsidian requires removing it otherwise. |
| Version | `--version` | `1.0.0`. SemVer `x.y.z` with no leading `v`. |
| Minimum Obsidian version | `--min-app-version` | The latest `obsidian` npm version (looked up automatically). Lower it only if they need older apps. |
| Desktop only | `--desktop-only` | No. Required if the plugin will use Node.js or Electron APIs (`fs`, `path`, `child_process`, …). |
| License | `--license` | `0-BSD`, the template's license. `MIT` is the other option. |
| Keep sample features? | (step 4) | Ask whether to keep the sample ribbon icon, commands, modal and settings tab as working examples, or strip down to an empty plugin plus settings. |

## 2. Validate, then create

Run the script with `--check` first. Fix any `error:` lines with the user, and mention any
`warning:` lines:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/bootstrap.mjs" --check --dir <dir> --id <id> --name "<name>" \
  --description "<description>" --author "<author>" [other flags]
```

Then run the same command without `--check`. It:

1. Clones the template to a temp folder and copies it to `--dir` without `.git`.
2. Sets `name`, `version`, `description`, `author`, `keywords` and `license` in `package.json`, and
   the root name and version in `package-lock.json`, so that `npm ci` still works. All scripts
   and dependencies are left alone.
3. Writes `manifest.json` (it removes `authorUrl` and `fundingUrl` if they weren't given) and a
   one-entry `versions.json`.
4. Puts the author in `LICENSE` (or writes the MIT text), and replaces the template's README
   with one for the new plugin.
5. Renames the sample classes (`MyPlugin`, `MyPluginSettings`, `SampleSettingTab`,
   `SampleModal`) after the plugin, because `eslint-plugin-obsidianmd`'s `sample-names` rule fails
   lint until they are renamed.
6. Runs `git init -b main` and makes the first commit
   (`chore: bootstrap <id> from obsidian-sample-plugin <sha>`), unless `--no-git` is passed.

Keep it: `AGENTS.md` (the template's guide to Obsidian plugin conventions for agents),
`.github/workflows/lint.yml` and `release.yml`, `.npmrc` (`tag-version-prefix=""`),
`.editorconfig` (tabs) and `version-bump.mjs`.

## 3. Install and build

```bash
cd <dir> && npm install && npm run build
```

`npm run build` must pass before you continue.

## 4. Remove sample code until lint passes

The unmodified template **fails** `npm run lint` on purpose: `eslint-plugin-obsidianmd` reports
`obsidianmd/no-sample-code`, `obsidianmd/sample-names` and `no-console` on the sample code. Run
`npm run lint` and fix every **error**:

- **Keep examples** (the user's choice): remove only what lint flags. Currently that's the
  `registerInterval(... console.log('setInterval') ...)` block. Keep everything else as is.
- **Strip**: also remove the ribbon icon, status bar item, the three sample commands, the
  `registerDomEvent` click notice and the modal class. Keep the settings interface, its defaults,
  `loadSettings`/`saveSettings` and the settings tab, and replace the sample setting with a
  placeholder named for the plugin.

Read the plugin's `AGENTS.md` before writing code. Follow the existing code style: tabs and
single quotes. Repeat `npm run lint` and `npm run build` until both exit 0. Report warnings
without fixing them unless the user asks. For example, `prefer-setting-definitions` suggests
Obsidian 1.13's declarative settings API, which is a bigger change than a bootstrap should make.

Commit the result (with `--no-git`, skip the commit):

```bash
git add -A && git commit -m "chore: remove sample code flagged by eslint-plugin-obsidianmd"
```

## 5. Report

Report in a few lines: the folder, ID, name, the template commit (the script prints it), and
that build and lint pass, with any warnings. Then give the next steps:

1. `npm run dev` rebuilds `main.js` whenever a file changes.
2. To try it in a vault, symlink the folder:
   `ln -s "$PWD" "<Vault>/.obsidian/plugins/<id>"`. Then reload Obsidian and enable the plugin in
   **Settings → Community plugins**. The Hot Reload plugin (github.com/pjeby/hot-reload, installed
   by hand) reloads the plugin after each build.
3. To release: run `npm version patch|minor|major`, then `git push --follow-tags`. The template's
   `release.yml` creates a draft GitHub release with `main.js`, `manifest.json` and `styles.css`.
4. Before submitting to the community directory, remove all remaining sample code. See
   https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin and the submission
   requirements.

Offer to create a GitHub repo (`gh repo create`) only if the user wants one. Never push
without asking.

## Hard rules

- Always clone the template fresh. Never paste in dependency versions, lint config or scripts
  from memory, this file, or another plugin.
- Don't change the template's `devDependencies`, `scripts`, `eslint.config.mts`,
  `tsconfig.json` or `esbuild.config.mjs` during bootstrap. Fix lint by changing `src/`, not
  by disabling rules.
- Never write into a folder that isn't empty. The script refuses to.
- The manifest `version`, the `versions.json` key and release tags are all `x.y.z` with no `v`.
