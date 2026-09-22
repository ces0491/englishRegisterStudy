# Collection log — Study 1

What each GloWbE query session did, including the queries that failed. Counts
that fit the registered grid go in `data/counts.csv`. This log keeps what does
not fit it yet.

## Constraints of a free account

Each was found during collection. The interface states them only when a query
is refused.

- **Section rule.** A search restricted to a section (General or Blog) is
  refused when every slot in the string occurs 1,500,000 times or more in the
  corpus: "(Except in COCA) You cannot search for high frequency multi-word
  strings, when you have also selected a SECTION." The unrestricted search
  still works.
- **Five-word limit.** "Unless you have a premium license, your search string
  must not be longer than five words in length." Tokens count as words, so
  `it 's not * , it 's` (F06) is seven.
- **Query limit.** 20 searches per rolling 24 hours. A premium licence gives
  200.

## Session 1 — 22 September 2026

Chart display throughout. "Combined" is the unrestricted search (section box
set to IGNORE).

| Frame | Section split | US | GB | IE | AU | ZA | All 20 | Note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| F01 | works | 1109 | 440 | 134 | 211 | 62 | 2728 | general + blog = combined in all five |
| F02 | works | 192 | 69 | 22 | 23 | 10 | 481 | general + blog = combined in all five |
| F03 | refused, General and Blog | 4052 | 1977 | 503 | 810 | 202 | 11772 | section rule |
| F04 | works | 2542 | 2613 | 520 | 973 | 237 | 10808 | general + blog = combined in all five |
| F05 | works | 198 | 143 | 15 | 30 | 9 | 552 | general + blog = combined in all five |
| F06 | refused, unrestricted too | | | | | | | five-word limit: no count possible on a free account |
| F07 | refused, General | 4379 | 4735 | 817 | 1575 | 271 | 16882 | section rule |

The session ended at the query limit (21 queries) before F08. Section word
counts were also taken this session (see D1 in `docs/deviations.md`).
