# Translation contract

Translate every `text` field from English to accurate, natural Japanese suitable for a research paper.

- Return JSON only: `{"translations":[{"id":"s00001","source":"exact input source","text":"…"}]}`.
- Return every assigned ID exactly once and preserve paragraph breaks with `\n`.
- Copy each input `source` exactly; do not normalize whitespace or Unicode.
- Preserve URLs, DOIs, citations, equation labels, variables, units, abbreviations, and names.
- Preserve every PDFMathTranslate placeholder such as `{v0}` exactly, including its count.
- Preserve the semantic role of every placeholder and variable, not merely its position. Check which noun, operator, comparison, or probability statement it belongs to.
- When one sentence is split across adjacent segments or pages, allocate the Japanese wording across those same segments according to their available source length. Keep a short continuation fragment short; never place the full remaining sentence into a narrow trailing fragment.
- Use the two-item `context_before` and `context_after` windows to translate the complete sentence, then place each part back in its own segment without duplication or dangling Japanese. A figure, table, equation, or heading may appear between two pieces of the same prose sentence.
- Translate closely and completely. Do not summarize, explain, strengthen, soften, or add parenthetical glosses not present in the source.
- Do not add explanations or Markdown.
- Leave strings without translatable prose unchanged.
- Apply the job-specific glossary consistently and prioritize technical meaning over English word order. If no glossary is supplied, create one from recurring domain terms before splitting work.
