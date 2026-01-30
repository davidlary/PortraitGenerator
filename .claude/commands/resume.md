# Resume Command

Resume the project from the last checkpoint with automatic context recovery.

## Actions

Perform these steps to resume work:

1. **Load state files**:
   - Read `data/state/master_state.json`
   - Read `data/state/context_tracking.json`
   - Read `data/state/plan.json` (if exists)
   - Read `.claude/checkpoints/` (if exists)

2. **Query MCP Memory** (NEW - if MCP configured):
   ```
   mcp__memory__search_nodes("checkpoint")
   ```
   This retrieves the most recent checkpoint context automatically.

3. **Display current status**:
   ```
   ╔═══════════════════════════════════════════════════════════════════════╗
   ║ PROJECT RESUME - Loaded from Last Checkpoint                          ║
   ╚═══════════════════════════════════════════════════════════════════════╝

   📊 Project Status:
   - Project: {{PROJECT_NAME}}
   - Version: {{VERSION}}
   - Last updated: {{LAST_UPDATE}}

   ✅ Modules Complete ({{COMPLETE_COUNT}}):
   {{#each MODULES_COMPLETE}}
   - {{this}}
   {{/each}}

   ⏳ Current Module: {{CURRENT_MODULE}}
   - Status: {{MODULE_STATUS}}
   - Progress: {{MODULE_PROGRESS}}%

   📋 Next Module: {{NEXT_MODULE}}

   💾 Context: {{CONTEXT_PCT}}%
   📦 Git: {{GIT_COMMIT}}
   🧠 MCP Memory: {{MEMORY_STATUS}}
   ```

4. **Verify everything is ready**:
   - ✅ State files loaded
   - ✅ Current module identified
   - ✅ Next steps clear
   - ✅ No uncommitted changes (if git repo)

5. **Continue from checkpoint**:
   - If current module in-progress: Continue that module
   - If no current module: Start next pending module
   - Display what will be done next

## Variables

These are automatically populated from state files:
- `{{PROJECT_NAME}}`: From master_state.json
- `{{VERSION}}`: Framework version
- `{{LAST_UPDATE}}`: Last state update timestamp
- `{{MODULES_COMPLETE}}`: Array of completed module IDs
- `{{COMPLETE_COUNT}}`: Count of completed modules
- `{{CURRENT_MODULE}}`: Current module ID
- `{{MODULE_STATUS}}`: Current module status
- `{{MODULE_PROGRESS}}`: Progress percentage
- `{{NEXT_MODULE}}`: Next pending module
- `{{CONTEXT_PCT}}`: Current context usage
- `{{GIT_COMMIT}}`: Latest git commit hash
- `{{MEMORY_STATUS}}`: MCP memory connection status

## Expected Outcome

After running this command:
- ✅ Full context recovered from checkpoint
- ✅ Current state clearly displayed
- ✅ Next steps identified
- ✅ Ready to continue work immediately

No manual recovery prompt needed!
