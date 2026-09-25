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

## Session 2 — 23 September 2026

| Frame | Section split | US | GB | IE | AU | ZA | All 20 | Note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| F08 | refused, General | 747 | 882 | 183 | 294 | 59 | 3828 | section rule |
| F09 | refused, General | 3201 | 2654 | 385 | 805 | 161 | 10237 | section rule |
| F10 | refused, General | 9246 | 6828 | 1370 | 2648 | 763 | 33443 | section rule; interface flagged SLOW QUERY |
| F11 | works | 229 | 150 | 41 | 52 | 7 | 616 | general + blog = combined in all five |
| F12 | works | 86 | 58 | 17 | 30 | 1 | 275 | general + blog = combined in all five; ZA blog is the first zero cell |
| F13 | refused, General | 24330 | 19265 | 3958 | 7492 | 1558 | 84253 | section rule; roughly ten times any other frame |
| F14 | works | 12073 | 7642 | 1449 | 2965 | 614 | 36702 | general + blog = combined in all five |
| F15 | combined 23 Sep, sections 25 Sep | 696 | 354 | 53 | 136 | 37 | 1763 | general + blog = combined in all five |

The limit is a rolling 24-hour window and counts refused queries too, which is
why a survey of eight frames exhausted it.

## Which frames the interface allows

| Split by section | Combined only | Not countable |
|---|---|---|
| F01, F02, F04, F05, F11, F12, F14, F15 | F03, F07, F08, F09, F10, F13 | F06 |

The blocked set is not arbitrary: the section rule catches the frames built
entirely from very common words, which is the whole contrastive family
(F06-F10) plus F03 and F13. What follows from it is deviation D2.

## Session 3 — 25 September 2026

F15's General and Blog runs, the two the second session ran out of queries
before reaching. Both grids are now complete: 70 combined cells in
`data/counts-combined.csv` and 80 section cells in `data/counts.csv`.
