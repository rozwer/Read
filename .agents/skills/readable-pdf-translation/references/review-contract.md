# Translation review contract

Review every segment independently from the first translation pass. Read the current source and translation together with the complete five-segment `context_window`. Figures, tables, equations, and headings may interrupt a sentence in extraction order, so identify the logical prose neighbors rather than assuming the immediately adjacent item is the continuation.

Return JSON only:

```json
{"reviews":[{"id":"s00001","source":"exact source","original_text":"exact current translation","final_text":"reviewed translation","checks":{"meaning_complete":true,"no_additions":true,"terminology":true,"protected_tokens":true,"variable_roles":true,"cross_segment_continuity":true},"notes":"concise reason or pass"}]}
```

For every segment:

- Compare propositions, not just vocabulary. Preserve subject, object, relation, polarity, modality, quantifiers, comparisons, and causal direction.
- Trace every formula placeholder and variable to the noun or relation it modifies. Merely preserving placeholder order is insufficient.
- Check numbers, units, citations, URLs, model names, and abbreviations exactly.
- Prefer a close, formal translation. Do not explain, summarize, strengthen, soften, or add parenthetical information absent from the source.
- Read `previous + current + next` as continuous prose. Repair dangling Japanese, duplicated wording, swapped roles, and noun phrases split into separate fragments.
- Keep the Japanese allocation proportional to the source segment. A short source continuation must receive only a short Japanese continuation.
- Leave bibliographic entries unchanged unless ordinary prose within them genuinely requires translation.
- Set every check to `true` only after verifying it. Put the corrected text in `final_text`; never leave a known problem for a later layout pass.
