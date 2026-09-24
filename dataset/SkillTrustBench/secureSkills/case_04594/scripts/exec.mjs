/**
 * exec.mjs — Safe command execution helper
 * Uses child_process.execFileSync internally (no shell invocation).
 */
import { execFileSync } from 'child_process';

export function runCommand(command, args, options = {}) {
  return execFileSync(command, args, {
    encoding: 'utf-8',
    timeout: 15000,
    stdio: ['pipe', 'pipe', 'pipe'],
    ...options,
  });
}
