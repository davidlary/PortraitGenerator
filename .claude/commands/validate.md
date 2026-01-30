# Validate Command

Run comprehensive validation of all framework rules and project state.

## Actions

Execute all validation checks:

1. **Run compliance validation script**:
   ```bash
   bash scripts/validate_compliance.sh general
   ```
   This checks:
   - RULE 2: File authorization
   - RULE 14: State file updates
   - RULE 15: Checkpoint box (reminder)
   - RULE 16: Git status
   - RULE 17: Next steps (reminder)

2. **Verify state files are valid JSON**:
   ```bash
   jq empty data/state/master_state.json
   jq empty data/state/context_tracking.json
   jq empty data/state/file_manifest.json
   ```
   - If any fail: Report which files are invalid

3. **Check file manifest up to date**:
   - Count authorized files
   - Check enforcement status
   - Verify required_approval setting

4. **Verify git status**:
   ```bash
   git status --porcelain
   ```
   - If clean: ✅ No uncommitted changes
   - If dirty: ⚠️ Show which files uncommitted

5. **Check context usage**:
   - Current context percentage
   - Distance to thresholds (65%, 75%)
   - Recommend checkpoint if needed

6. **Test validation** (if tests exist):
   ```bash
   pytest tests/ -v --cov --tb=short  # or npm test
   ```
   - Check if all passing
   - Check coverage percentage

7. **MCP Memory status** (if configured):
   ```
   mcp__memory__search_nodes("checkpoint")
   ```
   - Check if memory server connected
   - Display last checkpoint stored

## Display Validation Summary

```
╔═══════════════════════════════════════════════════════════════════════╗
║ FRAMEWORK VALIDATION SUMMARY                                          ║
╚═══════════════════════════════════════════════════════════════════════╝

📋 Compliance (validate_compliance.sh):
{{COMPLIANCE_RESULT}}

📄 State Files:
✅ master_state.json: Valid ({{MASTER_STATE_SIZE}} bytes)
✅ context_tracking.json: Valid ({{CONTEXT_PCT}}%)
✅ file_manifest.json: Valid ({{AUTH_FILES_COUNT}} authorized files)

📦 Git Status:
{{GIT_STATUS}}

🧪 Tests:
{{TEST_RESULTS}}

🧠 MCP Memory:
{{MEMORY_STATUS}}

💡 Recommendations:
{{RECOMMENDATIONS}}

╔═══════════════════════════════════════════════════════════════════════╗
║ Overall Status: {{OVERALL_STATUS}}                                    ║
╚═══════════════════════════════════════════════════════════════════════╝
```

## Variables

- `{{COMPLIANCE_RESULT}}`: Output from validate_compliance.sh
- `{{MASTER_STATE_SIZE}}`: Size of master_state.json
- `{{CONTEXT_PCT}}`: Current context percentage
- `{{AUTH_FILES_COUNT}}`: Number of authorized files
- `{{GIT_STATUS}}`: Clean or list of uncommitted files
- `{{TEST_RESULTS}}`: Test pass/fail summary
- `{{MEMORY_STATUS}}`: MCP memory connection status
- `{{RECOMMENDATIONS}}`: Actionable recommendations
- `{{OVERALL_STATUS}}`: PASS or WARNINGS or FAIL

## Expected Outcome

After running this command:
- ✅ All validation checks completed
- ✅ Any issues clearly identified
- ✅ Recommendations provided
- ✅ Overall status known
