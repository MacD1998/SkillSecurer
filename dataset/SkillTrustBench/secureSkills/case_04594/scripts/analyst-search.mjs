#!/usr/bin/env node
/**
 * analyst-search.mjs — Search ClawHub for skills
 * Usage: node analyst-search.mjs <query> [--limit N]
 */
import { runCommand } from './exec.mjs';

const args = process.argv.slice(2);
const limitIdx = args.indexOf('--limit');
let limit = 5;
if (limitIdx !== -1 && args[limitIdx + 1]) {
  limit = parseInt(args[limitIdx + 1], 10);
  if (isNaN(limit) || limit < 1) limit = 5;
  args.splice(limitIdx, 2);
}
const query = args.join(' ');

if (!query) {
  console.error('Usage: node analyst-search.mjs <query> [--limit N]');
  process.exit(1);
}

// Input validation: reject shell metacharacters and control characters
if (/[|&;$`\\()\n\r\0]/.test(query)) {
  console.error('Error: Query contains unsafe characters');
  process.exit(1);
}

try {
  const raw = runCommand('clawhub', ['search', query, '--limit', String(limit)]);

  // Parse search results
  const results = [];
  const lines = raw.trim().split('\n');

  for (const line of lines) {
    const match = line.match(/^(\S+)\s+(.+?)(?:\s+v(\S+))?$/);
    if (match) {
      results.push({
        name: match[1],
        description: match[2].trim(),
        version: match[3] || null
      });
    }
  }

  console.log(JSON.stringify({ query, limit, results, raw: raw.trim() }, null, 2));
} catch (e) {
  console.error('Search failed:', e.message);
  process.exit(1);
}
