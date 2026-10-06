---
name: readable-pdf-translation
description: Translate English research-paper PDFs into accurate Japanese with Codex while preserving source page correspondence, figures, tables, equations, citations, and layout. Use for Readable-style side-by-side Japanese/source PDFs, terminology-controlled paper translation, or repeatable Codex PDF translation jobs.
---

# Readable PDF translation

Use Codex as the translator. By default, produce two Readable-style PDFs with `Japanese page N` on the left and `source page N` on the right of the same landscape sheet: a `readable` variant with smaller Japanese and punctuation-aware wrapping, and a `standard` variant with source-size Japanese and ordinary wrapping. Produce an alternating-page or translation-only PDF only when the user explicitly asks for it. Keep reusable machinery inside this skill; keep each paper's source, glossary, translations, and outputs in a separate job directory.

Set `SKILL_DIR` to the directory containing this file. Use scripts under `$SKILL_DIR/scripts`; do not assume a particular workspace path.

## Workflow

1. Inspect page count and render representative source pages.
2. Create a job directory with `segments.json`, `batches/`, `translations/`, `engine-output/`, and `output/`. Put paper-specific terminology in `glossary.md`; never add it to the generic contract.
3. Start `scripts/codex_translation_bridge.py` in `record` mode on port 11435. Run `scripts/run_pdf2zh_readable.py --runtime-dir JOB/patched-pdf2zh --` followed by the normal `pdf2zh` arguments, using service `ollama`, `OLLAMA_HOST=http://127.0.0.1:11435`, `prompts/codex-bridge.txt`, absolute input/output paths, `--thread 1`, and `--ignore-cache`. Single-threaded recording is required so segment IDs and adjacent-context review packets follow deterministic document order. The wrapper uses a job-local copy of pdf2zh and leaves the installed package unchanged. Stop the bridge after it records every exact translation segment.
4. Split the recorded segments with `scripts/prepare_codex_batches.py`. Each item includes its immediate source neighbors. Read `references/translation-contract.md` and the job's `glossary.md`, translate in context, and write one translation JSON per batch.
5. Build the first-pass map with `scripts/build_codex_translation_map.py`. Then run `scripts/prepare_translation_review.py` to create review packets with the source, translation, and both adjacent pairs. In a separate Codex pass, read `references/review-contract.md` and write review JSON for every segment. Do not reuse the first-pass judgment.
6. Run `scripts/build_reviewed_translation_map.py` to require all six review checks for every ID and build the only map permitted for final rendering. Any missing or false check is a hard failure. Store its audit report beside the final map. Run `scripts/summarize_payload.py`; label its counts as payload measurements, not billed tokens.
7. Start the bridge in `serve` mode with the reviewed map. Render twice, sequentially, with new model names, `--thread 1`, and `--ignore-cache`: once with `scripts/run_pdf2zh_readable.py --preset readable` and once with `--preset standard`. Single-threaded final rendering avoids nondeterministic layout order and native-library shutdown failures observed in parallel runs. The readable preset uses `--font-scale 0.92 --width-scale 1.04 --sentence-threshold 0.58 --comma-threshold 0.82`; the standard preset uses source-size text, the source text-region width, and ordinary wrapping. Stop the bridge after both renders. Override individual values only when representative-page inspection supports it.
8. Treat each generated `*-mono.pdf` only as intermediate translated pages. Do not deliver the generator's `*-dual.pdf` directly. Run `scripts/side_by_side_readable.py TRANSLATED SOURCE OUTPUT` separately for both variants to reject any translated glyph outside its original page, then place each Japanese page on the left and its source page on the right. Name the outputs clearly with `-readable` and `-standard`. If either variant is rejected, compact or redistribute the responsible translation segments, repeat the independent review for every changed segment and its neighbors, rebuild the reviewed map, and rerun `pdf2zh`; never widen the page to conceal the overflow. Use `scripts/interleave_readable.py` only for an explicitly requested alternating-page variant.
9. Confirm for both variants that the final page count equals the source page count and that every landscape sheet contains the matching `Japanese N | source N` pair. Render both final PDFs as contact sheets, then inspect the cover, every revised page, a formula-heavy page, a figure-heavy page, a references page, and the final page at readable resolution.
10. After visual inspection, run `scripts/verify_readable_completion.py REVIEWED_MAP SEMANTIC_AUDIT TRANSLATED SOURCE FINAL COMPLETION_REPORT --visual-inspection passed` separately for both variants. Deliver both only if each verifies that the reviewed map has not changed, the semantic audit covers every segment, all page counts and spread dimensions match, and no glyph lies outside either translated or final pages.

## Layout contract

- Preserve the source MediaBox, CropBox, page background, columns, figures, tables, equations, citations, headers, footers, and page numbers.
- Never add page borders, text-box outlines, section frames, separator rules, shaded panels, or other decorations that do not exist on the corresponding source page.
- Preserve rules, boxes, and shading that are present in the source, including table borders and algorithm boxes. Compare translated and source renderings before deciding that a line is removable.
- Keep translated text inside the source text region. Adjust Japanese font size and line breaking before moving, resizing, or decorating the region.
- For multiline Japanese prose, default to 92% of the source font size and 104% of the source text-region width, expanding equally into the available side margins. Do not scale glyphs or figures. Prefer a break after `。！？` once 58% of the line is occupied, then after `、；：` once 82% is occupied. Apply Japanese line-start prohibition and use hanging punctuation rather than starting a line with closing punctuation. Keep headings, equations, single-line labels, and untranslated bibliography entries at their source size. Inspect representative pages because punctuation-aware ragging can add lines or narrow a column gap.
- Detect translated glyph bounding boxes outside the original page rectangle before composition. Treat horizontal or vertical overflow as an error requiring upstream translation-layout repair. Never expand the page, crop the glyphs, or hide the defect during composition.
- Use BIZ UDPMincho for Japanese overlay text when a local overlay or repair is required, unless the reference PDF clearly uses another font.
- Preserve both halves as vector PDF content; do not rasterize them. Use a blank central gutter only, without a divider line, page border, labels, shadows, or decorative framing.
- Keep each half at its original physical page size by default. The landscape canvas should be `translated width + gutter + source width` by the greater page height; let the PDF viewer scale the spread to its window.

Never alter URLs, DOIs, citation markers, equation labels, variables, units, author names, source keys, or `{vN}` placeholders. Use absolute paths with `pdf2zh` because it changes its working directory internally.

## Usage accounting

Do not claim an exact Codex token total unless the runtime or API returns usage data. Character counts from `summarize_payload.py` measure only the paper text sent for translation and the frozen translation text. They exclude system prompts, conversation history, reasoning tokens, tool output, retries, and subagent overhead.
