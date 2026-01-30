# NEXT STEPS Template (RULE 17)

**Purpose**: Template for RULE 17 mandatory end-of-response recovery instructions
**Usage**: MUST display at END of EVERY response (nothing after this block)
**Version**: v4.7.0
**Last Updated**: 2025-11-14

---

## RULE 17 Requirement

**MANDATORY**: At END of EVERY response (after checkpoint box), display NEXT STEPS block.

**Structure**: Must include recovery prompt that user can copy/paste in next session.

---

## Template Structure

```
███████████████████████████████████████████████████████████████████████
🎯 NEXT STEPS FOR YOU (AFTER YOU EXIT AND COME BACK IN)
███████████████████████████████████████████████████████████████████████

### When You Exit This Session and Come Back:

1. **Start new Claude Code session in this directory**

2. **Paste this EXACT prompt**:
   ```
   [FULL RECOVERY PROMPT - SEE RECOVERY_PROMPT_TEMPLATE.MD]
   ```

3. **Verify in first response**:
   - ✅ [VERIFICATION_ITEM_1]
   - ✅ [VERIFICATION_ITEM_2]
   - ✅ [VERIFICATION_ITEM_3]

4. **Then continue with**: [NEXT_TASK_DESCRIPTION]

### Before You Close This Session:

- **Verify**: [QUICK_CHECK_COMMAND]
- **Expected**: [EXPECTED_OUTPUT]

### If Issues When You Resume:

- **If [PROBLEM_1]**: [SOLUTION_1]
- **If [PROBLEM_2]**: [SOLUTION_2]

███████████████████████████████████████████████████████████████████████
[END OF RESPONSE - NOTHING AFTER THIS BLOCK]
███████████████████████████████████████████████████████████████████████
```

---

## v4.7.0 Enhancement: Compression Context

**NEW**: When using compression (RULE 22), include compression stats in verification:

### Enhanced Verification Section (v4.7.0+)

```
3. **Verify in first response**:
   - ✅ Version shows [VERSION]
   - ✅ Last commit is [COMMIT_HASH]
   - ✅ [TASK_SPECIFIC_VERIFICATION]
   - ✅ Compression enabled: [X]K tokens saved ([Y]% reduction)
   - ✅ [FILE_OR_FEATURE_EXISTS]
```

### Enhanced Before Closing Section (v4.7.0+)

```
### Before You Close This Session:

- **Verify**: git log -2 --oneline
- **Expected**: Should show [COMMIT_HASH] ([COMMIT_MESSAGE])
- **Compression**: Check compression_metrics in context_tracking.json
- **Savings**: [X]K tokens saved this session ([Y]% reduction)
```

---

## Complete Example (v4.7.0 with Compression)

```
███████████████████████████████████████████████████████████████████████
🎯 NEXT STEPS FOR YOU (AFTER YOU EXIT AND COME BACK IN)
███████████████████████████████████████████████████████████████████████

### When You Exit This Session and Come Back:

1. **Start new Claude Code session in this directory**

2. **Paste this EXACT prompt**:
   ```
   Continue Context-Preserving Framework development from v4.7.0.

   CONTEXT FROM LAST SESSION:
   - Completed v4.7.0 Phases 2-3: State tracking enhancement and template updates
     * Enhanced context_tracking.json with compression_metrics schema
     * Updated RULE 15 checkpoint template with compression stats display
     * Updated recovery_prompt_template.md with compression context
     * Created compression_tracking_template.md for real-time tracking
     * Created next_steps_template.md with v4.7.0 enhancements
   - Commits: [HASH1] "ENHANCE: v4.7.0 Phase 2-3 - State tracking and templates"
   - Files changed: 5 (3 modified, 2 new)

   CURRENT STATE:
   - Version: v4.7.0-alpha
   - Location: /Users/davidlary/Dropbox/Environments/Code/ContextPreservingFramework
   - Last commit: [HASH1] "ENHANCE: v4.7.0 Phase 2-3 - State tracking and templates"
   - State tracking: data/state/context_tracking.json (54% used)
   - Master state: data/state/master_state.json (v4.7.0-alpha)
   - Compression: 0K tokens saved (0% reduction, tracking infrastructure ready)
     * JIT loading: 0 uses, 0K tokens
     * Tool filtering: 0 uses, 0K tokens
     * Context editing: 0 uses, 0K tokens

   PENDING WORK (v4.7.0 Phases 4-5):
   - Phase 4: Testing and validation (~2 hours)
   - Phase 5: Documentation and release (~2 hours)

   WHAT TO DO:
   Begin Phase 4: Testing and validation. Test JIT loading, tool filtering,
   context editing, and benchmark full session with compression.

   Full autonomous permission granted: test, document, commit, push.
   ```

3. **Verify in first response**:
   - ✅ Version shows v4.7.0-alpha
   - ✅ Last commit is [HASH1]
   - ✅ compression_metrics exists in context_tracking.json
   - ✅ Templates updated (recovery_prompt, compression_tracking, next_steps)
   - ✅ Phase 2-3 complete, Phase 4-5 pending

4. **Then continue with**: Phase 4 (Testing and validation)

### Before You Close This Session:

- **Verify**: git log -2 --oneline
- **Expected**: Should show Phase 2-3 commit and previous v4.7.0-alpha commit
- **Compression**: Check compression_metrics.enabled=true in context_tracking.json
- **Templates**: Verify 3 templates exist in .claude/templates/

### If Issues When You Resume:

- **If version wrong**: Check git show [HASH]:data/state/master_state.json
- **If compression_metrics missing**: Check git show [HASH]:data/state/context_tracking.json
- **If templates missing**: Check git show [HASH]:.claude/templates/

███████████████████████████████████████████████████████████████████████
[END OF RESPONSE - NOTHING AFTER THIS BLOCK]
███████████████████████████████████████████████████████████████████████
```

---

## RULE 17 Self-Verification Checklist

**BEFORE completing response, verify:**

### Structure
- [ ] NEXT STEPS section exists at END of response
- [ ] Section includes "Paste this EXACT prompt:"
- [ ] Recovery prompt is COMPLETE (not placeholder)
- [ ] Section is LAST thing (nothing after it)

### Content
- [ ] Prompt includes what was completed this session
- [ ] Prompt includes current state (version, location, commit)
- [ ] Prompt includes pending work
- [ ] Prompt includes exact continuation instructions
- [ ] All [VARIABLES] filled with actual values
- [ ] File paths are absolute
- [ ] Commit hashes are real
- [ ] Version numbers are current

### v4.7.0 Compression Context
- [ ] Compression stats included in CURRENT STATE
- [ ] JIT/filtering/editing uses and savings listed
- [ ] Compression verification included in "Verify in first response"
- [ ] Compression check included in "Before closing"

### Copy/Paste Test
- [ ] Ask: "Can user copy/paste this and continue WITHOUT asking questions?"
- [ ] If NO → fix before completing response
- [ ] If YES → verification passed

---

## Common Mistakes to Avoid

❌ **DON'T**:
- Provide suggestions instead of actual prompt
- Use placeholders like [TBD], [TODO], [INSERT]
- Leave context vague
- Omit compression stats (v4.7.0+)
- Skip verification items

✅ **DO**:
- Fill in ALL details with real values
- Make prompt self-contained
- Include specific next actions
- Add compression context (v4.7.0+)
- Include permissions if autonomous work continues

---

## Integration with Other Templates

**Related Templates**:
- `recovery_prompt_template.md` - Full recovery prompt structure
- `compression_tracking_template.md` - Compression stats tracking

**Workflow**:
1. Complete work
2. Display checkpoint box (RULE 15)
3. **Display NEXT STEPS block (RULE 17)** ← YOU ARE HERE
4. End response (nothing after NEXT STEPS)

---

**Status**: ACTIVE - Use for all responses starting v4.7.0+
**Enforcement**: MUST (Tier 1 - Critical for user experience)
**Validation**: Technical enforcement via RULE 17 checklist
