# Using ChatGPT Pro (Codex)

## workflow
- use chatgpt pro in browser for heavy lifts (translate EL→Lite-C, write tests, review prs).
- optional vs code ai assistant (codeium/copilot free) for inline completions.

## prompts (save and reuse)
**translate EL→Lite-C**
Translate this EasyLanguage algorithm to Zorro Lite-C. Add guards (if Bar < N) and use series() for state. Output only code.
<PASTE SNIPPET>

**pre-PR scan**
Scan this Lite-C file and list risks: indexing, uninitialized series, div by zero. Output checklist + 2 pytest cases.
<PASTE CODE>
