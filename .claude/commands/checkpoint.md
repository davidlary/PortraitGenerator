# Checkpoint Command

Create a comprehensive checkpoint with all validation and state updates.

## Actions

Perform the following steps in order:

1. **Verify all tests passing** (RULE 18):
   ```bash
   pytest tests/ -v --cov  # or npm test
   ```
   - If tests fail: Debug and fix before proceeding
   - MUST NOT checkpoint with failing tests

2. **Update all state files** (RULE 14):
   - Update `data/state/master_state.json` with current module status
   - Update `data/state/context_tracking.json` with current context percentage
   - Append operation to `logs/operation_log.txt`
   - Timestamp all updates

3. **Store in MCP Memory** (NEW - if MCP configured):
   ```
   mcp__memory__create_entities([{
     name: "Checkpoint_{{TIMESTAMP}}",
     type: "checkpoint",
     observations: [
       "Context: {{CONTEXT_PCT}}%",
       "Modules complete: {{MODULES_COMPLETE}}",
       "Current module: {{CURRENT_MODULE}}",
       "Tests: passing"
     ]
   }])
   ```

4. **Git commit** (RULE 16):
   ```bash
   git add -A
   git commit -m "Checkpoint: {{MODULE_ID}} complete ({{CONTEXT_PCT}}% context)"
   git push origin main
   ```

5. **Display checkpoint box** (RULE 15):
   ```
   ═══════════════════════════════════════════════════════════════════════
   📊 STATE TRACKING CHECKPOINT (AUTOMATIC - RULES 14-17)
   ═══════════════════════════════════════════════════════════════════════
   ✅ Operation logged
   ✅ State updated
   ✅ Context tracked: {{CONTEXT_PCT}}%
   ✅ Tests passing
   ✅ Git committed
   ✅ MCP memory updated (if configured)
   ═══════════════════════════════════════════════════════════════════════
   ```

6. **Display next steps** (RULE 17):
   - Show exact recovery prompt for next session
   - Include current state summary
   - Provide verification steps

## Context Information

Fill in these variables:
- `{{TIMESTAMP}}`: Current timestamp
- `{{CONTEXT_PCT}}`: Current context percentage
- `{{MODULES_COMPLETE}}`: List of completed modules
- `{{CURRENT_MODULE}}`: Current module being worked on
- `{{MODULE_ID}}`: Module ID (e.g., "1.2")

## Expected Outcome

After running this command:
- ✅ All validation passing
- ✅ State files updated
- ✅ Git committed and pushed
- ✅ Memory stored (if MCP configured)
- ✅ User has clear next steps
