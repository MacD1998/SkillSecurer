#!/usr/bin/env node
/**
 * analyst-inspect.mjs — Get ClawHub skill details
 * Usage: node analyst-inspect.mjs <skill-name> [--files]
 */
import { runCommand } from './exec.mjs';

const args = process.argv.slice(2);
const withFiles = args.includes('--files');
const name = args.filter(a => a !== '--files')[0];

if (!name) {
  console.error('Usage: node analyst-inspect.mjs <skill-name> [--files]');
  process.exit(1);
}

// Input validation: only allow alphanumeric, hyphens, underscores, dots, slashes
if (!/^[a-zA-Z0-9._\-\/]+$/.test(name)) {
  console.error('Error: Skill name contains invalid characters');
  process.exit(1);
}

try {
  const cmdArgs = ['inspect', name];
  if (withFiles) cmdArgs.push('--files');

  const raw = runCommand('clawhub', cmdArgs);

  // Parse inspect output
  const info = { name, raw: raw.trim() };

  const summaryMatch = raw.match(/Summary:\s*(.+)/);
  if (summaryMatch) info.summary = summaryMatch[1].trim();

  const ownerMatch = raw.match(/Owner:\s*(\S+)/);
  if (ownerMatch) info.owner = ownerMatch[1];

  const versionMatch = raw.match(/Latest:\s*(\S+)/);
  if (versionMatch) info.version = versionMatch[1];

  const licenseMatch = raw.match(/License:\s*(.+)/);
  if (licenseMatch) info.license = licenseMatch[1].trim();

  const createdMatch = raw.match(/Created:\s*(\S+)/);
  if (createdMatch) info.created = createdMatch[1];

  const updatedMatch = raw.match(/Updated:\s*(\S+)/);
  if (updatedMatch) info.updated = updatedMatch[1];

  console.log(JSON.stringify(info, null, 2));
} catch (e) {
  console.error('Inspect failed:', e.message);
  process.exit(1);
}
