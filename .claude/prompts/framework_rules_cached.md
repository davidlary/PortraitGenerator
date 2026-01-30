# Context-Preserving Framework Rules (CACHED VERSION)

**Version**: v4.1.0 (Enhanced with 2025 Capabilities)
**Purpose**: Complete framework rules with prompt caching enabled
**Cache Duration**: Up to 1 hour (refreshes on each hit)
**Token Savings**: ~90% reduction on repeated sessions

---

<!-- ANTHROPIC_PROMPT_CACHE_CONTROL: type=ephemeral -->

## 🚀 2025 ENHANCEMENTS - NEW CAPABILITIES

**This cached version includes**:
1. ✅ MCP server integration (.mcp.json)
2. ✅ Prompt caching (this file - 90% cost reduction)
3. ✅ PreToolUse hooks (proactive validation)
4. ✅ MCP Memory Server (automatic context preservation)
5. ✅ Slash commands (.claude/commands/)

**All existing rules below are preserved + enhanced with new capabilities**

---

## 📋 COMPLETE FRAMEWORK RULES (v4.1.0)

### RULE 1: ZERO HARD-CODING

**Principle**: All values from config files or database
**Action**:
  - Use `config['section']['key']`, never literal values
  - Store constants in config files (JSON, YAML, or .env)
  - Use environment variables for deployment-specific values
**Validation**: Search codebase for hardcoded values, ensure all come from config

---

### RULE 2: NAMED FILES ONLY (ENHANCED v2.1 - WITH PRETOOLUSE VALIDATION)

**Principle**: Only create files authorized in manifest - UPDATE EXISTING files, don't create new ones
**Enforcement**: MUST (Tier 2) - Technically enforced by PreToolUse + PostToolUse hooks + file_manifest.json
**Critical**: Addresses user complaint "persistent issue creating new code instead of updating existing"

**NEW in v4.1.0**: PreToolUse hook validates BEFORE Write operation (blocks unauthorized files)

**Actions** (REQUIRED):

### Before Using Write Tool (MANDATORY - NOW ENFORCED PROACTIVELY)

**BEFORE creating ANY file, Claude MUST:**

1. **Check if file exists** (use Read tool or Glob):
   - If exists: **UPDATE it** (use Edit tool, NOT Write) ✅ PREFERRED
   - If not exists: Continue to step 2

2. **Check file_manifest.json** (if exists in project):
   ```bash
   # Check authorized files
   jq '.authorized_files' data/state/file_manifest.json
   jq '.always_allowed_patterns' data/state/file_manifest.json
   ```

3. **PreToolUse Hook Validation** (NEW in v4.1.0):
   - Hook runs automatically BEFORE Write tool executes
   - Validates file against manifest
   - **BLOCKS** Write operation if unauthorized
   - No violation occurs (proactive prevention)

4. **If NOT authorized**:
   - **MUST** use AskUserQuestion tool: "File X not in manifest. Options: (a) Update existing file Y instead, (b) Approve creating X, (c) Cancel"
   - **MUST** wait for user approval
   - **MUST** add to manifest if approved
   - **MUST NOT** create file without approval

5. **If authorized**:
   - Create file with Write tool
   - Update manifest's last_update timestamp

### File Manifest Structure

Location: `data/state/file_manifest.json`

```json
{
  "authorized_files": ["src/auth.py", "src/user.py"],
  "always_allowed_patterns": ["README.md", "test_*.py", "docs/**/*.md"],
  "always_allowed_extensions": [".md", ".txt", ".json"],
  "require_approval_for_new_files": true
}
```

### Validation (Two-Layer Enforcement)

**Layer 1: PreToolUse (NEW - Proactive)**:
- Runs BEFORE Write tool executes
- Checks file against manifest
- **BLOCKS** operation if unauthorized
- No cleanup needed (violation prevented)

**Layer 2: PostToolUse (Existing - Reactive)**:
- Runs AFTER Write operation (safety net)
- Detects any violations that slipped through
- Flags for correction

**Result**: Double enforcement (proactive + reactive)

---

### RULE 3: ZERO SILENT FAILURES

**Principle**: Every error MUST be logged loudly
**Action**:
  - Use proper logging (logger.error(), console.error(), etc.) with full context
  - Log warnings for unexpected conditions
  - All logs → stdout + log file
  - Never swallow exceptions or fail silently
**Never**: Catch exceptions without logging or re-raising

---

### RULE 4: AUTONOMOUS ISSUE RESOLUTION

**Principle**: Attempt recovery within retry limits before escalating
**Action**:
  - Max 3 retries with exponential backoff
  - Fatal errors (MemoryError, DiskFull): escalate immediately
  - Create issue tracking file if max retries exceeded
  - Document resolution attempts in logs

---

### RULE 5: DOCUMENTATION SYNCHRONIZATION

**Principle**: Docs must match code 100%
**Action**: After ANY code change:
  - Update corresponding docs in SAME commit
  - Run documentation validation
  - Never commit code without updating docs
  - Use inline comments for complex logic

---

### RULE 6: STRATEGY VS STATUS SEPARATION

**Principle**: Design (strategy) separate from progress (status)
**Structure**:
  - `docs/strategy/` or `docs/design/` → design docs (static, rarely changes)
  - `docs/implementation/` or `docs/progress/` → progress tracking (dynamic)
  - `STATUS.md` → top-level summary
  - Keep design decisions separate from implementation status

---

### RULE 7: VALIDATION GATES

**Principle**: Validation must pass before proceeding to next phase
**Action**:
  - Each major phase must validate before proceeding
  - Autonomous debug-and-fix on failures
  - Pipeline halts if validation fails after auto-fix attempt
  - Document validation criteria clearly

---

### RULE 8: PERFORMANCE OPTIMIZATION

**Principle**: Apply performance best practices from design docs
**Required**:
  - Use efficient data structures
  - Implement caching where appropriate
  - Batch operations when possible
  - Profile and optimize hotspots
  - Document performance requirements

---

### RULE 9: CODE REUSE MANDATORY

**Principle**: Search for existing functionality before writing new code
**Action**:
  1. Search codebase for existing functionality
  2. If found: Reuse and document
  3. If not found: Write new and register it
  4. Maintain code reuse registry if applicable

---

### RULE 10: CONTEXT MANAGEMENT (ENHANCED v4.1 - WITH MCP MEMORY)

**Principle**: Prevent context exhaustion through multi-layer management
**Enforcement**: MUST (Tier 1 - Critical)
**NEW in v4.1.0**: MCP Memory Server for automatic context preservation

**Thresholds** (Research-Based 2025):
- 0-50%: Continue normally (safe zone)
- 50-65%: Monitor closely, prepare for checkpoint
- **65%**: Normal checkpoint (summarize + save) - **MUST** trigger
- **75%**: Emergency checkpoint (force save) - **MUST** trigger
- **MUST NOT** exceed 75%

**Actions** (REQUIRED):
- **MUST** keep files small and focused (max 250-500 lines per file)
- **MUST** track context in real-time after every operation
- **MUST** display warning at 50%, critical at 65%
- **MUST** auto-checkpoint at 65%+
- **MUST** force emergency checkpoint at 75%
- **MUST** use recovery prompts for session continuity
- **MUST** apply automatic summarization: Compress completed work (95% token reduction)

**NEW: MCP Memory Integration**:
- Use `mcp__memory__create_entities` to store module summaries
- Use `mcp__memory__search_nodes` to retrieve context semantically
- Use `mcp__memory__create_relations` to link modules
- **Automatic recovery**: No manual prompt needed, query memory server

**Example**:
```
Session 1:
mcp__memory__create_entities([{
  name: "Module_1.2_Authentication",
  type: "module",
  observations: ["Complete", "Tests: 45 passing", "Files: src/auth.py (250 lines)"]
}])

Session 2:
mcp__memory__search_nodes("authentication")
# Returns: Module_1.2_Authentication with all context
# No manual recovery prompt needed!
```

---

### RULE 11: AUTONOMOUS EXECUTION MODE

**Principle**: Check AUTONOMOUS_MODE.md before significant actions
**Action**: At session start:
  - Check if `AUTONOMOUS_MODE.md` exists and `STATUS: ACTIVE`
  - If active: Proceed without asking for granted permissions
  - If not active: Ask before major operations
  - Display autonomous status clearly

---

### RULE 12: PRESERVE CORE REQUIREMENTS

**Principle**: Respect original requirements and design decisions
**Action**:
  - Treat requirements as sacred: preserve then enhance
  - Validate changes against requirements
  - Never contradict original design without approval
  - Document all deviations with justification

---

### RULE 13: REAL DATA ONLY

**Principle**: No placeholders, no dummy data, no TODOs in ANY committed file
**Forbidden**: "TODO", "TBD", "PLACEHOLDER", "XXX", "FIXME", empty strings, mock values
**Action**: Research real values before committing
**Validation**: Search for placeholder patterns before commits

---

### RULE 14: MANDATORY STATE TRACKING - ENFORCED EVERY OPERATION

**Principle**: State tracking **MUST** occur after EVERY tool operation
**Enforcement**: MUST (Tier 1 - Critical)

**Actions** (REQUIRED):
After Read, Write, Edit, Bash, Claude **MUST**:
  1. Log operation to log file (`logs/operation_log.txt`)
  2. Update state tracking (`data/state/master_state.json` or equivalent)
  3. Update context tracking (`data/state/context_tracking.json`)
  4. Check context threshold

**NEW in v4.1.0**: Can also use MCP Memory Server for state storage (optional enhancement)

---

### RULE 15: VISIBLE STATE TRACKING - MANDATORY IN EVERY RESPONSE

**Principle**: Make tracking VISIBLE in every response
**Action**: BEFORE completing ANY response, display:

```
═══════════════════════════════════════════════════════════════════════
📊 STATE TRACKING CHECKPOINT (AUTOMATIC - RULES 14-17)
═══════════════════════════════════════════════════════════════════════

✅ Operation logged: [type] → [log_file]
✅ State updated: [state_file] (timestamp: HH:MM:SS)
✅ Context tracked: [N]K tokens ([X.X]%)
✅ Threshold check: [SAFE/WARNING/CRITICAL]
✅ Git status: [Last commit hash or "No commits"]

Next threshold: [65%] at [N]K tokens
Operations this session: [count]

═══════════════════════════════════════════════════════════════════════
```

**This makes tracking visible and verifiable.**

---

### RULE 16: AUTOMATIC GIT OPERATIONS - MANDATORY COMMIT PROTOCOL

**Principle**: All work preserved in git automatically
**Action**: Commit at these points:
  - After completing any module or major task
  - After writing tests that pass
  - Before context reaches 65%
  - Every 30 minutes if actively working
  - Minimum: Every 5 significant operations

**Commit format** (use HEREDOC):
```bash
git commit -m "$(cat <<'EOF'
[Session_ID] Task_Description - STATUS

Changes:
- List of files modified

Progress: [X]% complete
Context: [N]K tokens ([X]%)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### RULE 17: CLEAR NEXT STEPS - MANDATORY AT END OF EVERY RESPONSE

**Principle**: User ALWAYS knows what to do next
**Action**: At END of EVERY response (AFTER checkpoint), display:

```
███████████████████████████████████████████████████████████████████████
🎯 NEXT STEPS FOR YOU (AFTER YOU EXIT AND COME BACK IN)
███████████████████████████████████████████████████████████████████████

### When You Exit This Session and Come Back:

1. **Start new Claude Code session in this directory**

2. **Paste this EXACT prompt** (OR use /resume command if available):
   ```
   [Exact recovery prompt with all context]
   ```

3. **Verify in first response**:
   - ✅ [What to check]

4. **Then continue with**: [Next task]

### Before You Close This Session:

- **Verify**: [Quick check]
- **Expected**: [What should show]

### If Issues When You Resume:

- **If [problem]**: [solution]

███████████████████████████████████████████████████████████████████████
[END OF RESPONSE - NOTHING AFTER THIS BLOCK]
███████████████████████████████████████████████████████████████████████
```

**NEW in v4.1.0**: Can use `/resume` slash command for automatic recovery (if configured)

---

### RULE 18: MANDATORY TESTING (v4.0 ADDITION)

**Principle**: Every module **MUST** have comprehensive tests before checkpoint
**Enforcement**: MUST (Tier 1 - Critical)

**Requirements** (MANDATORY):
- **MUST** write tests for every module
- **MUST** achieve >80% line coverage
- Tests **MUST** be in `tests/` directory
- Test file **MUST** follow naming convention:
  - Python: `test_<module>.py`
  - JavaScript: `<module>.test.js` or `<module>.spec.js`
  - Go: `<module>_test.go`
  - Rust: `tests/<module>.rs` or inline `#[test]`

**Test Execution** (REQUIRED):
- **MUST** run all tests before checkpoint
- **MUST** verify 100% passing (0 failures, 0 errors)
- **MUST NOT** checkpoint if any test fails

---

### RULE 19: MANDATORY AUTO-DOCUMENTATION (v4.0 ADDITION)

**Principle**: Documentation **MUST** be comprehensive, accurate, and current
**Enforcement**: MUST (Tier 2 - Important, but yields to Tier 1 context management)

**Documentation Types** (5 REQUIRED):

### 19.1 Inline Documentation (MUST - Every Function)
### 19.2 README.md (MUST UPDATE)
### 19.3 API.md (MUST UPDATE)
### 19.4 ARCHITECTURE.md (MUST UPDATE)
### 19.5 CHANGELOG.md (MUST UPDATE)

---

## 🎯 v4.1.0 ENHANCEMENTS SUMMARY

**New Capabilities**:
1. ✅ **MCP Server Integration** (.mcp.json)
   - Memory server for persistent context
   - Filesystem server for enhanced operations

2. ✅ **Prompt Caching** (this file)
   - 90% token cost reduction
   - 85% latency reduction
   - 1-hour cache TTL

3. ✅ **PreToolUse Hooks** (proactive enforcement)
   - RULE 2 validated BEFORE Write operations
   - Violations blocked, not just detected

4. ✅ **MCP Memory Server** (automatic context)
   - No manual recovery prompts
   - Semantic search for context
   - Persistent across sessions

5. ✅ **Slash Commands** (.claude/commands/)
   - /checkpoint - Create checkpoint automatically
   - /resume - Resume from checkpoint
   - /validate - Run all validations
   - Custom workflows

**All Existing Rules Preserved**: Rules 1-19 remain fully functional and enforced

---

## 📋 QUICK REFERENCE - ENFORCEMENT TIERS

### TIER 1: CRITICAL (Never Violate)
- RULE 10: Context Management
- RULE 14: State Tracking
- RULE 15: Visible Checkpoint
- RULE 16: Git Commit Protocol
- RULE 17: Next Steps
- RULE 18: Mandatory Testing

### TIER 2: IMPORTANT (Follow Unless Overridden by Tier 1)
- RULE 1-9, RULE 11-13, RULE 19

### TIER 3: OPTIMIZATION (Follow When Possible)
- Performance optimizations, best practices

**Conflict Resolution**: See `RULE_PRIORITIES_AND_CONFLICTS.md` for complete resolution algorithm

---

<!-- END_ANTHROPIC_PROMPT_CACHE_CONTROL -->

**Cache Information**:
- This content is cached for up to 1 hour
- Cache refreshes on each successful hit
- Subsequent sessions read from cache (90% token savings)
- No configuration needed (Claude Code handles automatically)

**Token Savings**:
- Without caching: ~15K tokens per session
- With caching: ~1.5K tokens per session
- Savings: ~13.5K tokens (90%) per session

**Last Updated**: 2025-01-12
**Version**: v4.1.0 (Enhanced Edition)
**Status**: Production-ready with 2025 best practices
