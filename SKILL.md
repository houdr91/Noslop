---
name: noslop
description: Detect "AI slop" in AI-generated (vibe-coded) portfolios and personal sites — broken href="#" links, placeholder LinkedIn/GitHub handles, invented skill percentages, lorem ipsum, textual placeholders, unfilled meta tags, scribe-tier generic copy, forms without action, and narrative contradictions between the About section and the displayed skills. Use ONLY when the user asks something like "review my freshly generated portfolio", "audit this vibe-coded website", "check if my site has AI slop", "my portfolio built with Claude/Cursor/v0/Lovable", or presents one or several `.html` / `.jsx` / `.tsx` / `.md` files of a personal site or portfolio suspected to be AI-generated. Do NOT activate for general code review, refactoring, functional bug hunting, performance, pure accessibility audits or linting of serious projects.
---

# noslop — AI slop detector for vibe-coded websites

Born from a real case: an AI-generated portfolio with unfilled `href="#"` links, a generic LinkedIn URL, invented skill percentages, and contradictions between the About ("IT support technician") and the displayed skills (95% in React).

## How to use this skill

When the user asks you to audit a portfolio or website (and this skill fires), ALWAYS follow this two-phase pipeline:

### Phase 1 — Deterministic scan (Python script)

1. Identify which files to audit (the `.html`, `.jsx`, `.tsx`, `.js`, `.ts`, `.md`, `.markdown` the user mentioned, or those in the directory they asked about).
2. Run the script with:

   ```
   python <path_to_this_skill>/scripts/slop_scan.py <file_or_folder> --json -o .noslop-report.json
   ```

   - The script uses ONLY the Python standard library (3.8+). No `pip install` needed.
   - It makes NO external API calls. All deterministic analysis runs locally.
   - The JSON output contains: prioritized findings (🔴/🟡/🟢), extracted context, and the score.

3. Read the generated JSON and proceed to Phase 2.

### Phase 2 — Narrative coherence analysis (your reasoning)

The script CANNOT detect semantic contradictions. That is YOUR job. Only PROCEED to this phase if the JSON has enough context (a non-empty `about` field AND a non-empty `skills` field).

**When you invoke it, do one or more of these checks with the extracted context:**

- **About ↔ Skills**: compare the first paragraph of `about` with the `skills` list (label + pct). Does the personal narrative match the percentages? Example of contradiction: "I am an IT support tech" + "React 95%". Return `INCONSISTENT` / `OK` / `DUBIOUS` + 1 line of justification quoting the excerpt.
- **Coherent identity**: compare `declared_name` with declared `socials`. Someone with 10 skills at 95% and no GitHub? Generic LinkedIn? Return a verdict.
- **Authentic hero**: does the `hero` sound auto-generated or authentic? Phrases like "modern and elegant", "built with love", "sketch of the application" are slop fingerprints. Verdict 0-10.

Do not make more inferences than those. The golden rule is **do not invoke your reasoning if there are fewer than 2 broken findings or fewer than 4 fishy findings** — in that case the site is clean and not worth spending tokens on.

### Phase 3 — Final report

Render the report in the exact format the script outputs (ASCII pretty, broken/fishy/minor table) and APPEND at the end a section titled:

```
NARRATIVE COHERENCE  🤔
  › Finding 1: <your judgement>
    Evidence: <quoted excerpt> ⟷ <skill bar 95% title>
    Verdict: INCONSISTENT / OK / DUBIOUS

  › Finding 2: ...
```

If you decided not to invoke inference because the site was clean, write:
```
NARRATIVE COHERENCE  🤔
  · Site without critical findings. Narrative inference skipped.
```

## Report format

The script already produces a formatted report. Your only task is to add the narrative section above. Do NOT change the rest of the report.

The score is 0-100, where **100 = clean site** and **0 = absolute slop**.

## Behavioral rules

- **Be transparent**: findings detected by regex CARRY 🔴/🟡/🟢 icons and a line. Inferences made by you CARRY a 🤔 icon and the separate section — the user must distinguish "this is objective slop" from "this is a guess".
- **Tri-state**: never say "broken" in an inference — use `INCONSISTENT` / `OK` / `DUBIOUS`.
- **Do not hallucinate**: if the script did not extract an `about`, do not invent one. If there are no skills, do not invent skills.
- **Do not edit the user's files** during the scan. Only read and report. If the user asks you to fix something, ask for explicit confirmation first.
- **Report language**: English by default. Switch to Spanish only if the user asked for the audit in Spanish.

## Known limitations

- The scanner can produce false positives on short LinkedIn handles (`linkedin.com/in/ai`) — it flags them as 🟡 (fishy), not 🔴 (broken). If the user tells you "that handle is real", dismiss the finding.
- In JSX/TSX the parser is regex, not an AST: it does not detect unused imports or broken refs (this skill does not validate code, it validates slop).
- The body-language vs `lang` declaration detector uses stop-words; for very short texts it can fail.
- Skill percentages `< 80` are never marked as magic — only suspicious aggregations are flagged (≥5 bars at the same pct, or ≥3 bars ≥95%, or the magic 80-100 sequence).

## Skill structure

```
no-slop/
├── SKILL.md                 # this file
├── scripts/
│   ├── slop_scan.py         # deterministic scanner (stdlib only)
│   └── rules.py             # user-editable rules
├── examples/
│   ├── clean_portfolio.html # clean case (0 broken expected)
│   ├── slop_portfolio.html  # real slop case
│   └── edge_*.html          # edge cases for tuning
├── tests/
│   └── run_tests.py         # suite without pytest, stdlib only
└── README.md
```
