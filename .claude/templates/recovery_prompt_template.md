# Recovery Prompt Template

**Purpose**: Template for RULE 17 recovery prompts at end of every response
**Usage**: Fill in ALL variables, don't leave any as [PLACEHOLDER]
**Verification**: Ask "Can user copy/paste this and continue seamlessly?"

---

## Standard Recovery Prompt Format

```
Continue [PROJECT_NAME] development from [CURRENT_VERSION].

CONTEXT FROM LAST SESSION:
- Completed: [LIST_COMPLETED_TASKS_WITH_DETAILS]
- Commits: [COMMIT_HASHES_AND_MESSAGES]
- Files changed: [NUMBER_AND_TYPES]
- Current status: [BRIEF_STATUS_SUMMARY]

CURRENT STATE:
- Version: [CURRENT_VERSION]
- Location: [FULL_DIRECTORY_PATH]
- Last commit: [COMMIT_HASH] "[COMMIT_MESSAGE]"
- State tracking: data/state/context_tracking.json ([PERCENTAGE]% used)
- Master state: data/state/master_state.json ([VERSION])
- Compression (v4.7.0+): [TOKENS_SAVED]K tokens saved ([COMPRESSION_PCT]% reduction)
  * JIT loading: [JIT_USES] uses, [JIT_SAVED]K tokens
  * Tool filtering: [FILTER_USES] uses, [FILTER_SAVED]K tokens
  * Context editing: [EDIT_USES] uses, [EDIT_SAVED]K tokens

[ORIGINAL_REQUEST_SECTION - Include if mid-task]:
ORIGINAL REQUEST:
[EXACT_COPY_OF_ORIGINAL_USER_REQUEST]

PROGRESS:
[WHAT_WAS_COMPLETED]
[WHAT_IS_PENDING]

WHAT TO DO:
[SPECIFIC_NEXT_ACTIONS_OR_CONTINUATION_INSTRUCTIONS]

[PERMISSIONS_STATEMENT_IF_NEEDED]:
Full autonomous permission granted to [SPECIFIC_PERMISSIONS].
```

---

## Example 1: Mid-Task Continuation

```
Continue Context-Preserving Framework development from v4.6.0.

CONTEXT FROM LAST SESSION:
- Completed v4.6.0: Checkpoint validation refactoring (P1 Critical fixed)
  * Split 407-line monolithic script → 5 modular components
  * All 33 validation checks preserved and tested
- Commit: 84f922c "RELEASE: v4.6.0 - Checkpoint Validation Refactoring"
- Files changed: 11 (6 new, 5 modified)
- Framework health: 100% (perfect self-compliance)

CURRENT STATE:
- Version: v4.6.0
- Location: /Users/davidlary/Dropbox/Environments/Code/ContextPreservingFramework
- Last commit: 84f922c "RELEASE: v4.6.0 - Checkpoint Validation Refactoring"
- State tracking: data/state/context_tracking.json (52.5% used)
- Master state: data/state/master_state.json (v4.6.0)
- Compression (v4.7.0+): 0K tokens saved (0% reduction, compression not yet active)

ORIGINAL REQUEST:
Execute comprehensive enhancement audit with FULL AUTONOMOUS PERMISSION:
1. Analyze violation logs ✅ Started
2. Research state-of-the-art AI agent frameworks (PENDING)
3. Compare against LangChain, AutoGPT, MetaGPT, CrewAI (PENDING)
4. Identify gaps (PARTIALLY COMPLETE)
5. Implement improvements (2 COMPLETE: v4.5.2, v4.6.0)
6. Update documentation ✅ COMPLETE
7. Commit and push ✅ COMPLETE
8. Generate enhancement report (PENDING)

WHAT TO DO:
Continue with Phase 2 (Research) of enhancement audit, OR implement
additional improvements identified in docs/analysis/ENHANCEMENT_AUDIT_20251113.md.

Full autonomous permission to research, implement, test, document, commit, push.
```

---

## Example 2: Task Complete, Next Session Open

```
Continue Context-Preserving Framework development from v4.6.1.

CONTEXT FROM LAST SESSION:
- Completed v4.6.1: RULE 17 violation pattern fix
  * Enhanced RULE 17 with self-verification checklist
  * Created recovery prompt template
  * Documented persistent non-compliance pattern
- Commit: [HASH] "FIX: v4.6.1 - RULE 17 Enforcement Enhancement"
- Files changed: 5 (2 new, 3 modified)
- All previous work intact (v4.5.2, v4.6.0)

CURRENT STATE:
- Version: v4.6.1
- Location: /Users/davidlary/Dropbox/Environments/Code/ContextPreservingFramework
- Last commit: [HASH] "FIX: v4.6.1 - RULE 17 Enforcement Enhancement"
- State tracking: data/state/context_tracking.json ([X]% used)
- Master state: data/state/master_state.json (v4.6.1)
- Framework status: 100% self-compliant, all rules enforced

WHAT TO DO:
Framework is ready for next task. Options:
1. Continue enhancement audit (Phase 2: Research)
2. Implement additional v4.7.0 features
3. Run comprehensive framework validation
4. Or specify new task

Respond with which direction you'd like to take.
```

---

## Example 3: Waiting for User Input

```
Continue Context-Preserving Framework development from v4.6.1.

CONTEXT FROM LAST SESSION:
- Implemented [FEATURE_NAME]
- Encountered decision point: [DESCRIPTION_OF_CHOICE]
- Asked user to choose between:
  Option A: [DESCRIPTION]
  Option B: [DESCRIPTION]
- Awaiting user decision to proceed

CURRENT STATE:
- Version: v4.6.1
- Location: /Users/davidlary/Dropbox/Environments/Code/ContextPreservingFramework
- Last commit: [HASH] "[MESSAGE]"
- State: Paused at decision point
- Branch: [BRANCH_NAME if not main]

WHAT TO DO:
Review the options presented in last session and tell me which to proceed with:
- Option A: [DESCRIPTION]
- Option B: [DESCRIPTION]
- Or provide alternative approach

Once you decide, I'll continue implementation.
```

---

## Verification Checklist

Before including recovery prompt in response, verify:

- [ ] All [VARIABLES] filled in with actual values
- [ ] No placeholders left (search for [ ])
- [ ] Project name correct
- [ ] Version number current
- [ ] Completed tasks listed with details
- [ ] Pending tasks clearly stated
- [ ] File paths absolute (not relative)
- [ ] Commit hashes real (not placeholder)
- [ ] User can copy/paste and Claude will know exactly what to do
- [ ] Permissions explicit (if autonomous work continues)

**Test Question**: "If I pasted this in a new session, would Claude understand the full context and know what to do next WITHOUT asking clarifying questions?"

If answer is NO → prompt is incomplete.

---

## Common Mistakes to Avoid

❌ **DON'T**: Provide options/suggestions instead of actual prompt
❌ **DON'T**: Use placeholders like [TBD], [TODO], [INSERT HERE]
❌ **DON'T**: Leave context vague ("continue where we left off")
❌ **DON'T**: Assume Claude will remember (new session = fresh start)
❌ **DON'T**: Skip commit hashes, version numbers, file paths

✅ **DO**: Fill in ALL details
✅ **DO**: Make prompt self-contained
✅ **DO**: Include specific next actions
✅ **DO**: Test with "can I copy/paste this?" question
✅ **DO**: Include permissions if autonomous work continues

---

**Last Updated**: 2025-11-14 (v4.7.0 - Added compression context support)
**Status**: ACTIVE - Use for all RULE 17 responses
**New in v4.7.0**: Compression metrics section shows RULE 22 effectiveness tracking
