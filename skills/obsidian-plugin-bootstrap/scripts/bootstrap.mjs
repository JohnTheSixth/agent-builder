#!/usr/bin/env node
// Bootstrap a new Obsidian plugin from the official sample template.
//
// Clones https://github.com/obsidianmd/obsidian-sample-plugin, removes its git history, and
// rewrites only the identifying fields (package.json, package-lock.json, manifest.json,
// versions.json, LICENSE, README.md). The template's scripts, dependencies, lint/build config,
// workflows and AGENTS.md are kept exactly as published, so the project always matches the
// current template instead of a copy pinned in this skill.
//
// Node built-ins only. Run with --help for usage.

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync, readdirSync, rmSync, mkdtempSync, cpSync } from 'node:fs';
import { join, resolve, basename } from 'node:path';
import { tmpdir } from 'node:os';

const TEMPLATE_URL = 'https://github.com/obsidianmd/obsidian-sample-plugin.git';

const HELP = `Usage: node bootstrap.mjs --dir <path> --id <plugin-id> --name <Display Name>
                         --description <text> --author <name> [options]

Required:
  --dir <path>              Target folder (must not exist, or be empty). Its basename should equal --id.
  --id <plugin-id>          Lowercase letters, digits and hyphens; no "obsidian"; must not end in "plugin".
  --name <name>             Display name; no "Obsidian" and no "Plugin".
  --description <text>      <= 250 chars, ends with ".", doesn't start with "This is a plugin".
  --author <name>           Author name (manifest, package.json, LICENSE).

Optional:
  --author-url <url>        Author website / GitHub profile.
  --funding-url <url>       Donation link. Omitted from manifest.json if not given (per Obsidian rules).
  --version <x.y.z>         Initial plugin version (default 1.0.0). No leading "v".
  --min-app-version <x.y.z> Minimum Obsidian version (default: latest "obsidian" npm package version).
  --desktop-only            Set isDesktopOnly: true (needed if the plugin uses Node.js/Electron APIs).
  --license <0-BSD|MIT>     License (default 0-BSD, same as the template).
  --template-ref <ref>      Branch or tag of the template to clone (default: its default branch).
  --no-git                  Skip "git init" and the initial commit.
  --check                   Validate the arguments only; clone nothing, write nothing.
  -h, --help                Show this help.`;

// ---------- argument parsing ----------

function parseArgs(argv) {
	const flags = new Set(['desktop-only', 'no-git', 'check', 'help']);
	const opts = {};
	for (let i = 0; i < argv.length; i++) {
		let a = argv[i];
		if (a === '-h') a = '--help';
		if (!a.startsWith('--')) fail(`Unexpected argument: ${a}`);
		let key = a.slice(2);
		let value;
		const eq = key.indexOf('=');
		if (eq !== -1) {
			value = key.slice(eq + 1);
			key = key.slice(0, eq);
		}
		if (flags.has(key)) {
			opts[key] = true;
			continue;
		}
		if (value === undefined) {
			value = argv[++i];
			if (value === undefined) fail(`Missing value for --${key}`);
		}
		opts[key] = value;
	}
	return opts;
}

function fail(msg) {
	console.error(`error: ${msg}`);
	process.exit(1);
}

// ---------- validation (Obsidian manifest + submission rules) ----------

const SEMVER = /^\d+\.\d+\.\d+$/;

function validate(o) {
	const errors = [];
	const warnings = [];
	for (const k of ['dir', 'id', 'name', 'description', 'author']) {
		if (!o[k] || !String(o[k]).trim()) errors.push(`--${k} is required`);
	}
	if (errors.length) return { errors, warnings };

	if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(o.id)) {
		errors.push(`id "${o.id}" must be kebab-case: lowercase letters, digits and single hyphens`);
	}
	if (o.id.includes('obsidian')) errors.push(`id "${o.id}" must not contain "obsidian"`);
	if (o.id.endsWith('plugin')) errors.push(`id "${o.id}" must not end with "plugin"`);
	if (/\d/.test(o.id)) warnings.push(`Obsidian's manifest docs say IDs use lowercase letters and hyphens; "${o.id}" has digits`);

	if (/obsidian|obsi-|-sidian/i.test(o.name)) errors.push(`name "${o.name}" must not contain "Obsidian" (or Obsi-/-sidian)`);
	if (/plugin/i.test(o.name)) errors.push(`name "${o.name}" must not contain "Plugin"`);
	if (!/^[A-Za-z0-9 ()+\-]+$/.test(o.name)) {
		errors.push(`name "${o.name}" may only use Basic Latin letters, digits, spaces, hyphens, "+" and parentheses`);
	}

	const d = o.description.trim();
	if (d.length > 250) errors.push(`description is ${d.length} chars; maximum is 250`);
	if (!d.endsWith('.')) errors.push('description must end with a period');
	if (/^this is (a|an) .*plugin/i.test(d)) errors.push('description must not start with "This is a plugin"');
	if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(d)) errors.push('description must not contain emoji');

	o.version = o.version ?? '1.0.0';
	if (o.version.startsWith('v')) errors.push(`version "${o.version}" must not have a leading "v"`);
	else if (!SEMVER.test(o.version)) errors.push(`version "${o.version}" must be SemVer x.y.z`);
	if (o['min-app-version'] && !SEMVER.test(o['min-app-version'])) {
		errors.push(`min-app-version "${o['min-app-version']}" must be x.y.z`);
	}

	for (const k of ['author-url', 'funding-url']) {
		if (o[k] && !/^https?:\/\//.test(o[k])) errors.push(`--${k} must be an http(s) URL`);
	}

	o.license = o.license ?? '0-BSD';
	if (!['0-BSD', 'MIT'].includes(o.license)) errors.push(`license "${o.license}" must be 0-BSD or MIT`);

	const dir = resolve(o.dir);
	if (existsSync(dir) && readdirSync(dir).length > 0) errors.push(`target folder ${dir} exists and is not empty`);
	if (basename(dir) !== o.id) {
		warnings.push(`folder name "${basename(dir)}" differs from id "${o.id}"; Obsidian expects them to match in <Vault>/.obsidian/plugins/`);
	}
	return { errors, warnings };
}

// ---------- helpers ----------

function run(cmd, args, cwd) {
	return execFileSync(cmd, args, { cwd, stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8' }).trim();
}

// The template uses tab-indented JSON (see .editorconfig and version-bump.mjs).
function readJson(p) {
	return JSON.parse(readFileSync(p, 'utf8'));
}
function writeJson(p, obj) {
	writeFileSync(p, JSON.stringify(obj, null, '\t') + '\n');
}

function latestObsidianApi() {
	try {
		const v = run('npm', ['view', 'obsidian', 'version']);
		if (SEMVER.test(v)) return v;
	} catch {
		/* fall through */
	}
	return null;
}

function licenseText(kind, year, author) {
	if (kind === 'MIT') {
		return `MIT License

Copyright (c) ${year} ${author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
`;
	}
	return null; // 0-BSD: keep the template's text, only the copyright line changes
}

function readme(o) {
	return `# ${o.name}

${o.description.trim()}

## Development

\`\`\`bash
npm install
npm run dev     # watch build: src/main.ts -> main.js
npm run build   # type-check + production build
npm run lint    # ESLint with eslint-plugin-obsidianmd
\`\`\`

To try it in a vault, put this folder (or a copy of \`main.js\`, \`manifest.json\` and \`styles.css\`) at
\`<Vault>/.obsidian/plugins/${o.id}/\`, reload Obsidian, and enable **${o.name}** in
**Settings → Community plugins**.

## Releasing

\`\`\`bash
npm version patch   # or minor / major: updates package.json, manifest.json, versions.json
git push --follow-tags
\`\`\`

Pushing a tag runs \`.github/workflows/release.yml\`, which builds the plugin and creates a draft GitHub
release with \`main.js\`, \`manifest.json\` and \`styles.css\`. Tags have no leading \`v\` (see \`.npmrc\`).

See \`AGENTS.md\` for Obsidian plugin conventions and https://docs.obsidian.md/Plugins for the API.

## License

${o.license}
`;
}

// ---------- main ----------

const o = parseArgs(process.argv.slice(2));
if (o.help) {
	console.log(HELP);
	process.exit(0);
}

const { errors, warnings } = validate(o);
for (const w of warnings) console.warn(`warning: ${w}`);
if (errors.length) {
	for (const e of errors) console.error(`error: ${e}`);
	process.exit(1);
}

const minAppVersion = o['min-app-version'] ?? latestObsidianApi();
if (!minAppVersion) fail('could not look up the latest Obsidian version (npm view obsidian version); pass --min-app-version');

if (o.check) {
	console.log(`ok: arguments are valid (minAppVersion would be ${minAppVersion})`);
	process.exit(0);
}

const dir = resolve(o.dir);
const year = new Date().getFullYear();

// 1. Clone into a temp folder, then copy without .git, so a failed clone leaves no half-made target.
const tmp = mkdtempSync(join(tmpdir(), 'obsidian-plugin-bootstrap-'));
const clonePath = join(tmp, 'template');
const cloneArgs = ['clone', '--quiet', '--depth', '1'];
if (o['template-ref']) cloneArgs.push('--branch', o['template-ref']);
cloneArgs.push(TEMPLATE_URL, clonePath);
try {
	run('git', cloneArgs);
} catch (e) {
	rmSync(tmp, { recursive: true, force: true });
	fail(`git clone failed: ${e.stderr || e.message}`);
}
const templateCommit = run('git', ['-C', clonePath, 'log', '-1', '--format=%h %cs']);
rmSync(join(clonePath, '.git'), { recursive: true, force: true });
cpSync(clonePath, dir, { recursive: true });
rmSync(tmp, { recursive: true, force: true });

// 2. package.json: change identity fields only; keep the template's scripts and dependencies.
const pkgPath = join(dir, 'package.json');
const pkg = readJson(pkgPath);
const ordered = {};
for (const [k, v] of Object.entries(pkg)) {
	ordered[k] = v;
	if (k === 'description') {
		ordered.author = o.author;
	}
}
Object.assign(ordered, {
	name: o.id,
	version: o.version,
	description: o.description.trim(),
	author: o.author,
	keywords: ['obsidian', 'obsidian-plugin'],
	license: o.license,
});
writeJson(pkgPath, ordered);

// 3. package-lock.json: keep it (npm ci in the template's workflows needs it); fix the root name/version.
const lockPath = join(dir, 'package-lock.json');
if (existsSync(lockPath)) {
	const lock = readJson(lockPath);
	lock.name = o.id;
	lock.version = o.version;
	if (lock.packages?.['']) {
		lock.packages[''].name = o.id;
		lock.packages[''].version = o.version;
		lock.packages[''].license = o.license;
	}
	writeJson(lockPath, lock);
}

// 4. manifest.json: rebuild from the template's keys so new fields it adds later are preserved.
const manifestPath = join(dir, 'manifest.json');
const manifest = readJson(manifestPath);
Object.assign(manifest, {
	id: o.id,
	name: o.name,
	version: o.version,
	minAppVersion,
	description: o.description.trim(),
	author: o.author,
	isDesktopOnly: Boolean(o['desktop-only']),
});
if (o['author-url']) manifest.authorUrl = o['author-url'];
else delete manifest.authorUrl;
if (o['funding-url']) manifest.fundingUrl = o['funding-url'];
else delete manifest.fundingUrl;
writeJson(manifestPath, manifest);

// 5. versions.json: one entry, plugin version -> minimum Obsidian version.
writeJson(join(dir, 'versions.json'), { [o.version]: minAppVersion });

// 6. LICENSE and README.md
const licensePath = join(dir, 'LICENSE');
const mit = licenseText(o.license, year, o.author);
if (mit) {
	writeFileSync(licensePath, mit);
} else if (existsSync(licensePath)) {
	const text = readFileSync(licensePath, 'utf8').replace(/^Copyright .*$/m, `Copyright (C) ${year} by ${o.author}`);
	writeFileSync(licensePath, text);
}
writeFileSync(join(dir, 'README.md'), readme(o));

// 7. Rename the template's sample classes. eslint-plugin-obsidianmd's `sample-names` rule fails
//    `npm run lint` until they are renamed. Other sample code (`no-sample-code`) is left for the
//    skill to remove, because which parts to keep is the user's call.
let pascal = o.name.replace(/[^A-Za-z0-9]+/g, ' ').trim().split(/\s+/)
	.map((w) => w[0].toUpperCase() + w.slice(1)).join('');
if (/^\d/.test(pascal)) pascal = `P${pascal}`;
const renames = {
	MyPluginSettings: `${pascal}Settings`,
	MyPlugin: `${pascal}Plugin`,
	SampleSettingTab: `${pascal}SettingTab`,
	SampleModal: `${pascal}Modal`,
};
const srcDir = join(dir, 'src');
const renamedFiles = [];
if (existsSync(srcDir)) {
	for (const f of readdirSync(srcDir, { recursive: true })) {
		if (!String(f).endsWith('.ts')) continue;
		const p = join(srcDir, String(f));
		const before = readFileSync(p, 'utf8');
		let after = before;
		for (const [from, to] of Object.entries(renames)) after = after.replace(new RegExp(`\\b${from}\\b`, 'g'), to);
		after = after.replace(/^\/\/ Remember to rename these classes and interfaces!\n\n?/m, '');
		if (after !== before) {
			writeFileSync(p, after);
			renamedFiles.push(`src/${f}`);
		}
	}
}

// 8. git init + first commit
let gitNote = 'skipped (--no-git)';
if (!o['no-git']) {
	try {
		run('git', ['init', '--quiet', '-b', 'main'], dir);
		run('git', ['add', '-A'], dir);
		run('git', ['commit', '--quiet', '-m', `chore: bootstrap ${o.id} from obsidian-sample-plugin ${templateCommit.split(' ')[0]}`], dir);
		gitNote = `initialized on branch main with one commit`;
	} catch (e) {
		gitNote = `FAILED: ${(e.stderr || e.message).trim()} (files are written; run git init/commit yourself)`;
	}
}

console.log(`Created ${o.name} (${o.id}) at ${dir}
  template:      obsidian-sample-plugin @ ${templateCommit}
  version:       ${o.version}
  minAppVersion: ${minAppVersion}
  desktop only:  ${Boolean(o['desktop-only'])}
  license:       ${o.license}
  classes:       ${Object.values(renames).join(', ')} (in ${renamedFiles.join(', ') || 'no files'})
  git:           ${gitNote}`);
