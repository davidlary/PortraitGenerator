# Google API Quota Issue - Report for Google Support

**Date**: January 31, 2026
**Time**: 13:10:06 (1:10 PM PST)
**API Key Used**: AIzaSy...REDACTED

---

## Issue Summary

Despite having prepaid API credits, receiving **429 RESOURCE_EXHAUSTED** errors with **"limit: 0"** for `generativelanguage.googleapis.com/generate_requests_per_model_per_day`.

---

## Exact Error Message from Google API

```json
{
  "error": {
    "code": 429,
    "message": "You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_requests_per_model_per_day, limit: 0",
    "status": "RESOURCE_EXHAUSTED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.Help",
        "links": [
          {
            "description": "Learn more about Gemini API quotas",
            "url": "https://ai.google.dev/gemini-api/docs/rate-limits"
          }
        ]
      },
      {
        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
        "violations": [
          {
            "quotaMetric": "generativelanguage.googleapis.com/generate_requests_per_model_per_day",
            "quotaId": "GenerateRequestsPerDayPerProjectPerModel"
          }
        ]
      }
    ]
  }
}
```

---

## Key Details

### Quota Metric
**`generativelanguage.googleapis.com/generate_requests_per_model_per_day`**

### Quota ID
**`GenerateRequestsPerDayPerProjectPerModel`**

### Reported Limit
**0** (zero)

This is unusual because:
1. **Customer has prepaid credits**
2. **Limit shows as 0** (should be higher with paid plan)
3. **Error occurred at 1:10 PM** (early in day, not end of day)

---

## API Calls Made Before Quota Exhaustion

### Model Used
`gemini-3-pro-image-preview` (Nano Banana Pro)

### Successful Calls Today
Based on generated files, approximately:
1. **Claude Shannon** (4 portraits) - likely generated earlier
2. **Alan Turing BW** (1 portrait) - earlier
3. **Alan Turing Color** (1 portrait) - last success at 13:10:06

**Total successful image generations today**: ~6 images
**Total API calls**: Higher due to research, validation, and fact-checking calls

### When Quota Exhausted
At 13:10:06 during parallel generation attempt for Alan Turing's remaining styles (Sepia, Painting).

---

## Questions for Google Support

1. **Why is the limit showing as "0"?**
   - Should reflect prepaid credits quota

2. **Are prepaid credits properly applied?**
   - API key: AIzaSy...REDACTED
   - Expected: Higher daily quota with prepaid plan

3. **Is this a per-model quota?**
   - Quota metric mentions "per_model_per_day"
   - Is `gemini-3-pro-image-preview` limited separately?

4. **How to check current quota usage?**
   - Monitoring URL provided: https://ai.dev/rate-limit
   - Need to verify actual usage vs. available quota

5. **How to increase quota if needed?**
   - Expected: Prepaid credits should provide adequate quota
   - Need clarification on quota tiers

---

## Expected Behavior

With prepaid API credits, should have:
- Higher daily request quota
- Not hit limit after only ~6 image generations
- Clear visibility into remaining quota

---

## Current Impact

**Blocked from completing testing**:
- 6 of 84 portraits generated (7.1%)
- 78 remaining portraits cannot be generated
- Production-ready system waiting for quota availability

---

## Supporting Information

### API Usage Pattern
- **Model**: gemini-3-pro-image-preview (image generation)
- **Parallel requests**: Up to 4 concurrent (for 4 portrait styles)
- **Additional calls**: Research queries, validation, fact-checking
- **Each portrait subject**: ~10-15 API calls total

### Estimated Daily Need
- **21 subjects × 4 styles**: 84 portraits
- **~15 calls per subject**: ~315 API calls total
- **Duration**: ~3.5 hours estimated

---

## Monitoring URLs Provided by Google

1. **Rate Limits Documentation**: https://ai.google.dev/gemini-api/docs/rate-limits
2. **Usage Monitoring**: https://ai.dev/rate-limit

---

## Request for Google Support

Please investigate why:
1. Daily quota limit shows as "0"
2. Quota exhausted after minimal usage (~6 images)
3. Prepaid credits not reflected in quota limits

**Expected Resolution**:
- Verify prepaid credits are active
- Increase daily quota to match prepaid plan
- Provide visibility into current usage and limits

---

## Contact Information

**API Key**: AIzaSy...REDACTED
**Project**: Portrait Generator v2.0.0
**Use Case**: Automated portrait generation using gemini-3-pro-image-preview
**Prepaid Credits**: Yes (confirmed by customer)

---

## Technical Stack

- **Python SDK**: google-genai (latest)
- **Model**: gemini-3-pro-image-preview
- **API Method**: `models.generate_content()` with `response_modalities=['Image']`
- **Error Handling**: Implemented with retry logic (2 attempts)

---

## Timeline

- **11:24 AM**: Earlier portrait generation successful
- **12:02-12:20 PM**: Claude Shannon 4 portraits successful
- **13:09-13:10 PM**: Alan Turing Color successful
- **13:10:06 PM**: Quota exhaustion begins
- **13:10:06+ PM**: All subsequent calls fail with 429 RESOURCE_EXHAUSTED

---

**This document can be shared directly with Google Cloud Support or Gemini API Support.**
