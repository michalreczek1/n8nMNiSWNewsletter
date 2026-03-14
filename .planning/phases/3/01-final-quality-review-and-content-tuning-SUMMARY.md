# Phase 3 Summary

## Outcome
Phase 3 was completed. The final newsletter pipeline now combines stronger source extraction, tighter AI instructions, and stricter quality gates for summary acceptance.

## Implemented Changes
- Improved `docx` extraction in `scripts/rcl_extract_project.py` so documents stored mainly in tables are no longer treated as empty.
- Reduced noisy AI context by suppressing low-value heuristic fallback summaries when they would mislead the model.
- Strengthened the AI prompt in `AI Project Summary` to demand concrete legal, operational, financial or beneficiary-level changes instead of vague prose.
- Added a stronger generic-summary filter in `Finalize Project Analysis` so weak AI outputs fall back to more concrete content built from `keyChanges`.
- Narrowed MNiSW relevance scoring to avoid false positives from long consultation or stakeholder lists embedded in source documents.

## Files Changed
- `E:\Projects\n8n\RPL.json`
- `E:\Projects\n8n\scripts\rcl_extract_project.py`

## Notes
- The biggest quality gain in this phase came from improving source extraction, not only prompt tuning.
- After tuning, sample summaries for weaker projects became materially more concrete and the false positive in the main MNiSW section was removed.
