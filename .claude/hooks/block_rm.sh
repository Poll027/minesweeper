#!/bin/bash
cmd=$(jq -r '.tool_input.command // ""')

if printf '%s' "$cmd" | grep -qF 'rm -rf'; then
    jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Blocked by toy hook: commands containing rm -rf are not allowed."
    }
  }'
  exit 0
fi

exit 0