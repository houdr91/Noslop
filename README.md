# no slop

**Detect AI slop in vibe-coded websites.**

If you have ever generated a portfolio with Claude Code, Cursor, v0 or Lovable
and shipped it without reviewing it, you probably have broken `href="#"` links,
a LinkedIn URL pointing to `/in/` with no handle, skill bars at 100% on things
you have never touched, or an About that says "IT support technician" while the
site claims you master React. `no slop` finds all of that — and about 80 more
things — in a couple of seconds, with no dependencies and no external API calls.

This project was born out of a real case. The portfolio of someone I know looked
fine at first glance, but the moment you clicked "Demo" it took you to `#`. The
LinkedIn link was `linkedin.com/in/` (no handle). Every skill was at 95%. The
About said "I am an IT support technician" while the skill bars claimed 100% in
React. Thirty seconds of manual review would have saved the site; nobody did it.
This skill turns those 30 seconds into a single command.

---

## What it does

It is a skill for agentic coding tools (Claude Code, opencode, Cursor). You
install it, ask the agent something like "review my freshly generated portfolio"
and it activates on its own. It runs a deterministic scanner in Python (stdlib
only) that analyzes HTML, JSX, TSX and Markdown, classifies the findings into
three severity tiers and produces a prioritized ASCII report. If enough context
has been extracted (About section + skill list), the user's own agent adds a
narrative inference section: does what you say you are match what you show? No
external API calls, no keys, no `pip install` of anything.

The score goes from 0 to 100, where **100 is a clean site and 0 is absolute slop**.

---

## Who it is for

- For people who generate sites with AI and ship them without a human looking
  at them.
- For people doing code review on junior work and tired of the same issues
  every time.
- For freelance QA who charge for audits and want to automate the boring 80%.
- For people evaluating vibe-coded tools (v0 vs Lovable vs Cursor) and wanting
  an objective metric for "is this really finished?".

---

## Installation

### Claude Code

```bash
# User-level (all projects)
cp -r no-slop ~/.claude/skills/

# Or inside a specific project
cp -r no-slop your-project/.claude/skills/
```

### opencode

```bash
# Linux / macOS
cp -r no-slop ~/.config/opencode/skills/

# Windows (PowerShell)
Copy-Item -Recurse no-slop "$env:APPDATA\opencode\skills\"
```

### Cursor and others

Copy `SKILL.md` to the folder where your tool reads agent instructions. The
scanner also works without the skill, directly from the CLI:

```bash
python scripts/slop_scan.py your-portfolio.html
```

---

## Usage

### Direct CLI

```bash
# Human-readable report in the console (ASCII pretty, English, 🔴🟡🟢🤔 emojis)
python scripts/slop_scan.py my-portfolio.html

# Structured JSON to integrate with other agents / CI / scripts
python scripts/slop_scan.py my-portfolio.html --json

# Dump JSON to a file
python scripts/slop_scan.py my-portfolio.html --json -o .noslop-report.json

# Audit an entire folder (walks .html, .jsx, .tsx, .md)
python scripts/slop_scan.py ./my-site/
```

### Via agentic skill

Ask the agent things like:

- "Review my freshly generated portfolio"
- "Audit this vibe-coded website"
- "Check if my site has AI slop"
- "My portfolio built with Claude / Cursor / v0"

`SKILL.md` carries a description tuned so the skill fires exactly in this
context and does not activate on generic code review or linting tasks.

---

## Example output

```
╔══════════════════════════════════════════════════════════════════════╗
║  NO SLOP REPORT                                                    ║
║  Target: my-portfolio.html                                         ║
║  Generated: 2026-07-20T19:30:00                                    ║
║  Files:  1    Slop-Score: 0/100                                    ║
╚══════════════════════════════════════════════════════════════════════╝

SUMMARY
  🔴 Broken   : 29  (user-visible, embarrassing)
  🟡 Fishy    : 42  (template not personalized)
  🟢 Minor    :  2  (accessibility / SEO low-hanging fruit)

DETAIL — Broken  🔴
  ┌─ my-portfolio.html:20
  │  href="#" placeholder
  │  >> <a href="#">Link</a>
  └
  ┌─ my-portfolio.html:0
  │  6 skill bars with pct >= 95 (suspicious)
  │  >> HTML=95%, CSS=98%, JavaScript=97%, React=100%, Vue=96%
  └
  ...

NARRATIVE COHERENCE  🤔  (context for the agent)
  · Invoke reasoning about About ↔ Skills (see context below).
  · Extracted context:
  ── my-portfolio.html ──
     declared name   :
     body language   : es
     title           : My Website
     about           : "I am an IT support technician. I have been working..."
     skills          : HTML=95%, CSS=98%, JavaScript=97%, React=100%, Vue=96%, ...
     socials         : {'linkedin': 'https://linkedin.com/in/yourname', ...}

FIX PRIORITY
  1. 🔴 6 skill bars with pct >= 95 (suspicious)  [my-portfolio.html]
  2. 🔴 form with action="#"                      [my-portfolio.html:66]
  3. 🔴 lorem ipsum detected                       [my-portfolio.html:27]
  ...
```

The agent receives that JSON, appends its own `🤔` section with a tri-state
verdict (`INCONSISTENT` / `OK` / `DUBIOUS`), and the user can clearly tell
what came from regex and what came from reasoning.

---

## How it works under the hood

Two-phase pipeline.

**Phase 1: deterministic scanner.** `scripts/slop_scan.py` applies 80+ patterns
classified as follows:

| Tier | Weight | Examples |
|---|---|---|
| 🔴 Broken | 10 pts | `href="#"`, `mailto:` with no destination, `tel:+1 (555) 123-4567`, lorem ipsum, `form action="#" method=POST`, `src=""` on `<img>`, `og:title` default `Website`, referenced files that do not exist, `console.log("TODO")`, `[Your Name]` placeholder, `you@example.com`. |
| 🟡 Fishy | 3 pts | `linkedin.com/in/yourname`, `github.com/yourusername`, skill bars with ≥3 percentages ≥95%, ≥5 skills all at the same pct, magic sequence 80/85/90/95/100, placeholder meta description, footer `© 2025 Your Name`, empty `try/catch {}`, `lang="en"` on a Spanish body, "modern and elegant", "built with love", "powered by", "built with ❤". |
| 🟢 Minor | 1 pt | missing `lang`, missing meta description, `data:,` favicon, buzzwords ("ai-powered", "seamless", "robust"), `<!-- generated by claude -->` comments. |

Score = `max(0, 100 - sum(weights))`.

**Phase 2: narrative inference.** Only if there is enough context (`about`
+ `skills` extracted) **and** ≥2 broken or ≥4 fishy findings. The agent
makes 1-3 inferences:

- **About ↔ Skills**: does the personal narrative match the displayed
  percentages?
- **Coherent identity**: declared name, real LinkedIn, public GitHub.
- **Authentic vs auto-generated hero**: scored 0-10.

Transparency is the golden rule: findings detected by regex carry 🔴/🟡/🟢,
agent inferences carry 🤔 and live in a separate section of the report. The
user can always distinguish "this is objective slop" from "this is a guess".

---

## Repository structure

```
no-slop/
├── SKILL.md                  Frontmatter + agent instructions
├── scripts/
│   ├── slop_scan.py          Deterministic scanner (stdlib only)
│   └── rules.py              Editable rules (~80 patterns)
├── examples/
│   ├── clean_portfolio.html  Well-made site: 0 broken, score 100
│   ├── slop_portfolio.html   Restored real case: 29 broken, score 0
│   └── edge_*.html           11 boundary cases (lorem, linkedin, skills...)
├── tests/
│   └── run_tests.py          Suite without pytest, stdlib only (28 checks)
└── README.md
```

---

## Testing

```bash
python tests/run_tests.py
```

No pytest. Stdlib only. It verifies:

- **`clean_portfolio.html`**: 0 broken, ≤3 fishy, score ≥90. This is the most
  important anti-false-positive test: a well-made site should not trigger
  anything critical.
- **`slop_portfolio.html`**: ≥8 broken, ≥10 fishy, score ≤45. Detects the
  five symptoms of the real case: `href="#"`, lorem, magic skill bars,
  generic LinkedIn, context about="IT support tech" + skill React=100%.
- **11 `edge_*` cases**: concentrated lorem, real vs generic handles
  (including the 3-char handle boundary), mixed languages, normal vs magic
  skills, broken vs working forms, Markdown with placeholders, empty file,
  missing assets, valid JSX without false positives.
- **Dedupe**: the same rule is not reported twice on the same line.

Current status: **28 OK, 0 FAIL ✓**

---

## Requirements

- Python 3.8+
- Zero external dependencies (no `pip install`, no `requirements.txt`)
- Zero external API calls (no keys, no tokens, no telemetry)
- Zero network. Everything runs locally.

---

## Editing rules

Rules live in `scripts/rules.py` as Python constants — easy to maintain
without dependencies and portable to Python 3.8+:

```python
# scripts/rules.py
LINKS = [
    (BROKEN, "my new broken pattern",
     r'\bhref\s*=\s*["\']my-placeholder["\']', re.I),
    # ...
]
```

Categories: `BROKEN`, `FISHY`, `MINOR`. Weights: 10 / 3 / 1 (tunable in
`SCORING` inside `slop_scan.py`).

---

## Limitations

- **Regex parser, not an AST**. In JSX/TSX it does not detect unused imports,
  broken refs or misused hooks. It detects structural slop, not code bugs.
  It is not a linter.
- **Short LinkedIn handles** (`<3 chars`): marked as 🟡, not 🔴. A real
  short handle like `ai` or `je` can land here and be validated by hand;
  the agent discards it if the user confirms it is real.
- **Language detector** based on stop-words. For very short texts
  (<30 words) it can fail.
- **External assets**: validation of non-existent `src` only applies to
  `.html`/`.htm` (in JSX the bundler resolves `src` at runtime).
- **ID cross-references** (`href="#id"` without matching `id`): only on
  HTML, not on JSX/MD components (a component may point to an id on
  another page).

---

## Roadmap

- [ ] Astro `.astro` and Svelte `.svelte` support
- [ ] Detector for duplicated sections (same paragraph in >1 section)
- [ ] Detector for identical `alt` on copy-pasted cards
- [ ] `--ci` mode (exit code != 0 if score < threshold) for pipelines
- [ ] Report i18n (English as a second output)

---

## Philosophy

- **Determinism first.** If a regex can detect it, do not give the agent
  the chance to hallucinate.
- **Transparency.** The user always knows what came from regex and what
  came from inference.
- **Zero lock-in.** No dependencies, no API, no keys, no account, no
  telemetry. If this project disappears tomorrow, the script still works.
- **False positives > false negatives.** A clean site flagged as 🟡 is
  verified in 5 seconds; a missed slop goes to production.

---

## Contributing

PRs welcome. Before submitting one, run:

```bash
python tests/run_tests.py
```

It must return **28 OK, 0 FAIL**. If you add a new pattern, add it to
`rules.py`, create an `edge_*.html` case that proves it, and update
`tests/run_tests.py`.

---

## License

MIT.
