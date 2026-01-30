# Compression Tracking Template

**Purpose**: Real-time tracking template for RULE 22 compression effectiveness
**Usage**: Update throughout session to track compression strategy usage
**Version**: v4.7.0
**Last Updated**: 2025-11-14

---

## Session Compression Summary

**Session ID**: [SESSION_DATE_TIME]
**Project**: [PROJECT_NAME]
**Starting Context**: [INITIAL_TOKENS]K tokens ([INITIAL_PCT]%)

---

## Strategy Usage Tracking

### 1. JIT Loading (SELECT Strategy)

**Pattern**: Grep/Glob before Read (discovery → targeted loading)

| # | Time | Action | Tokens Saved | Notes |
|---|------|--------|--------------|-------|
| 1 | HH:MM | Grep "pattern" → Read target.py | ~[N]K | [Brief note] |
| 2 | HH:MM | Glob "*.js" → Read match.js | ~[N]K | [Brief note] |

**Total JIT Savings**: [TOTAL]K tokens

---

### 2. Tool Output Filtering (COMPRESS Strategy)

**Pattern**: Summarize verbose outputs (>1K tokens)

| # | Time | Tool | Output Size | Filtered To | Saved | Notes |
|---|------|------|-------------|-------------|-------|-------|
| 1 | HH:MM | Grep | 15K | 3K | ~12K | 50+ matches → summary |
| 2 | HH:MM | Bash | 8K | 2K | ~6K | Log file → key errors |

**Total Filtering Savings**: [TOTAL]K tokens

---

### 3. Context Editing (ISOLATE Strategy)

**Pattern**: Prune old low-signal content

| # | Time | Action | Tokens Removed | Notes |
|---|------|--------|----------------|-------|
| 1 | HH:MM | Pruned completed task discussion | ~[N]K | No longer relevant |
| 2 | HH:MM | Removed redundant file reads | ~[N]K | Content already known |

**Total Editing Savings**: [TOTAL]K tokens

---

### 4. Monitoring (WRITE Strategy)

**Pattern**: Track and display compression effectiveness

| # | Time | Check Type | Result | Action Taken |
|---|------|------------|--------|--------------|
| 1 | HH:MM | Context threshold check | 68% | Triggered checkpoint |
| 2 | HH:MM | Compression ratio check | 45% reduction | Continue session |

**Monitoring Checks**: [COUNT] checks this session

---

## Session Statistics

**Context Without Compression** (theoretical): [UNCOMPRESSED]K tokens
**Context With Compression** (actual): [COMPRESSED]K tokens
**Tokens Saved Total**: [SAVED]K tokens
**Compression Ratio**: [RATIO]% reduction ([X.X]:1)
**Effective Context**: [EFFECTIVE_PCT]% (vs [THEORETICAL_PCT]% without)

**Session Extension**: Enabled [X]x longer session duration

---

## Effectiveness Analysis

### Most Effective Strategy
- **[STRATEGY_NAME]**: [SAVINGS]K tokens saved ([PCT]% of total)
- **Why effective**: [EXPLANATION]

### Opportunities Missed
- [ ] [MISSED_OPPORTUNITY_1]
- [ ] [MISSED_OPPORTUNITY_2]

### Recommendations for Next Session
1. [RECOMMENDATION_1]
2. [RECOMMENDATION_2]
3. [RECOMMENDATION_3]

---

## Validation Against Research Claims

**Anthropic Research (2025)**: 50-80% reduction achievable

| Metric | Research Target | Actual | Status |
|--------|----------------|--------|--------|
| Total Reduction | 50-80% | [ACTUAL]% | [PASS/FAIL] |
| JIT Loading | 30-50% | [ACTUAL]% | [PASS/FAIL] |
| Tool Filtering | 15-25% | [ACTUAL]% | [PASS/FAIL] |
| Context Editing | 10-15% | [ACTUAL]% | [PASS/FAIL] |

**Validation Notes**: [ANALYSIS_OF_RESULTS]

---

## Quick Reference: When to Use Each Strategy

### Use JIT Loading When:
✅ Exploring codebase to find relevant files
✅ Searching for specific functionality
✅ Identifying modification targets
✅ Understanding project structure (start high-level)

❌ DON'T use when you already know exact file

### Use Tool Filtering When:
✅ Grep results >20 matches
✅ File listings >10 files
✅ Test output >50 lines
✅ Log files >100 lines
✅ JSON/data dumps >1K tokens

### Use Context Editing When:
✅ Completed work no longer relevant
✅ Redundant content in context
✅ Old error messages resolved
✅ Approaching 50% threshold

### Monitor Continuously:
✅ After every 5-10 operations
✅ When approaching threshold (>50%)
✅ Before/after major tool use
✅ At checkpoint time

---

## Example: Effective Compression Session

```
09:00 - Session start: 10K tokens (5%)
09:15 - JIT: Grep → Read (saved 30K vs pre-loading 5 files)
09:30 - Filter: Summarized 50-line test output (saved 12K)
09:45 - Context: 35K tokens (17.5%) ← Would be 77K (38.5%) without compression
10:00 - Continue working (extended session enabled)
10:15 - Filter: Grep 100 matches → summary (saved 25K)
10:30 - Edit: Pruned completed task (saved 8K)
10:45 - Final: 45K tokens (22.5%) ← Would be 120K (60%) without compression

Result: 75K tokens saved (62.5% reduction), 2x session extension
```

---

## Integration with State Files

**Update context_tracking.json After Each Strategy Use**:

```bash
# Update JIT loading
jq '.compression_metrics.strategies_used.jit_loading.uses += 1' context_tracking.json
jq '.compression_metrics.strategies_used.jit_loading.tokens_saved += [N]' context_tracking.json

# Update tool filtering
jq '.compression_metrics.strategies_used.tool_filtering.uses += 1' context_tracking.json
jq '.compression_metrics.strategies_used.tool_filtering.tokens_saved += [N]' context_tracking.json

# Update context editing
jq '.compression_metrics.strategies_used.context_editing.uses += 1' context_tracking.json
jq '.compression_metrics.strategies_used.context_editing.tokens_saved += [N]' context_tracking.json

# Update totals
jq '.compression_metrics.tokens_saved = [TOTAL]' context_tracking.json
jq '.compression_metrics.compression_ratio = [RATIO]' context_tracking.json
```

---

**Notes**:
- This is a working document - update throughout session
- Fill in actual values as you track compression usage
- Reference this when displaying checkpoint boxes (RULE 15)
- Include summary in recovery prompts (RULE 17)
- Validate effectiveness against research claims

**Status**: ACTIVE - Use starting v4.7.0+
