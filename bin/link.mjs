#!/usr/bin/env node
import { readdirSync, lstatSync, mkdirSync, symlinkSync, rmSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = new Set(process.argv.slice(2));
const force = args.has('--force') || args.has('-f');
const dryRun = args.has('--dry-run') || args.has('-n');
const claudeDir = join(homedir(), '.claude');

function pathExists(p) {
  try { lstatSync(p); return true; } catch { return false; }
}

const targets = [
  { name: 'agents', filter: e => e.isFile() && e.name.endsWith('.md'), type: 'file' },
  { name: 'skills', filter: e => e.isDirectory(), type: 'dir' },
];

let linked = 0, replaced = 0, skipped = 0;

for (const { name, filter, type } of targets) {
  const srcDir = join(repoRoot, name);
  if (!pathExists(srcDir)) continue;
  const dstDir = join(claudeDir, name);
  if (!dryRun) mkdirSync(dstDir, { recursive: true });

  for (const entry of readdirSync(srcDir, { withFileTypes: true })) {
    if (!filter(entry)) continue;
    const srcPath = join(srcDir, entry.name);
    const dstPath = join(dstDir, entry.name);

    if (pathExists(dstPath)) {
      const isLink = lstatSync(dstPath).isSymbolicLink();
      if (!force) {
        console.log(`skip    ${dstPath}${isLink ? ' (symlink exists)' : ' (file exists)'}`);
        skipped++;
        continue;
      }
      if (!dryRun) rmSync(dstPath, { recursive: true, force: true });
      replaced++;
    }

    if (dryRun) {
      console.log(`would   ${srcPath} -> ${dstPath}`);
    } else {
      symlinkSync(srcPath, dstPath, type);
      console.log(`linked  ${entry.name} -> ${dstPath}`);
    }
    linked++;
  }
}

const tag = dryRun ? ' (dry run)' : '';
console.log(`\n${linked} linked, ${replaced} replaced, ${skipped} skipped${tag}`);
if (skipped && !force) console.log(`re-run with --force to replace existing entries.`);
