# Writing the grammar practice for Phunzies Classroom

You are writing ORIGINAL grammar practice for a teacher's classroom app (students in Spain, British English).
The teacher said the current grammar exercises "aren't very good": they are repetitive, some have two gaps with
answers like "comes, fly", some ask meta-questions ("What is the main clause?"), and many are near-duplicates.

## Input
`tools/grammar_briefs/<book>.json` has, for every unit: `n`, `unit_title`, `grammar` (the grammar point(s); sometimes
empty or generic, in which case work it out from `existing_questions_sample`), `vocab` (the unit's words: use them in
your sentences so grammar and vocabulary are practised together) and `existing_questions_sample` (only to see the level
and the grammar point; do NOT copy or lightly reword them).

Levels: Time Travellers 1-6 = Spanish primary school, ages 6-12 (TT1-2: very short sentences, present tenses, 2-3
options; TT3-4: A1; TT5-6: A2). Prepare 4-8 = secondary, ages 12-16 (Level 4 = A2, 5 = A2/B1, 6 = B1, 7 = B1+/B2, 8 = B2).

## Output
Write `tools/grammar_data/<book>.json` (UTF-8, valid JSON, one file per book):

```json
{"book": "tt5", "units": [
  {"n": 3, "title": "Zero conditional",
   "notes": ["If / When + present simple, present simple: If you heat ice, it melts.", "Use it for things that are always true."],
   "items": [
     {"t": "choose", "q": "If you heat ice, it ___.", "opts": ["melts", "melt", "melted"], "a": "melts", "why": "it + present simple takes -s"},
     {"t": "write",  "q": "When winter ___ (come), birds fly south.", "a": ["comes"], "why": "winter = it, so comes"},
     {"t": "fix",    "q": "If it rain, we stay inside.", "a": ["If it rains, we stay inside."], "why": "it rains"},
     {"t": "order",  "q": "gets / when / angry / late / we / the teacher / are", "a": ["When we are late, the teacher gets angry.", "The teacher gets angry when we are late."], "why": ""}
   ]}
]}
```

Rules
- `title`: a clear short name of the grammar point (fix generic ones). `notes`: 2-4 short rules, each with an example, in simple English.
- 20 items per unit. Mix for TT3-6 and Prepare: 9 choose, 6 write, 3 fix, 2 order. For TT1-2: 14 choose, 4 write, 2 order, no fix,
  sentences of at most 7 words.
- EXACTLY ONE gap (`___`, three underscores) per `choose` / `write` item. Never two gaps.
- `choose`: 3 options (2 allowed for TT1-2 when only two forms exist), exactly one correct, `a` identical to one of `opts`,
  the correct option in a random position. Distractors must be real mistakes learners make (wrong tense, wrong auxiliary,
  missing -s, wrong preposition...), never nonsense, and never also correct.
- `write`: the base word goes in brackets after the gap; `a` lists EVERY correct answer (contracted and full forms:
  "doesn't like", "does not like"). The context must make one tense the only natural choice (add a time expression or a
  second sentence). Ask yourself of every gap: "could another word or tense also be right here?" If yes, add context or list it.
- `fix`: one mistake only, a typical one for Spanish speakers; `a` = the full corrected sentence (all acceptable versions).
- `order`: 5-9 chunks separated by " / ", shuffled, no capital letter or final punctuation clue; `a` = every correct sentence.
- `why`: a short reason in simple English (max 12 words); may be "" for `order`.
- No meta-questions, no two-gap items, no near-duplicates (do not repeat the same pattern with a different subject more
  than twice), no item that depends on a picture or on the book's text. Every sentence must make sense on its own.
- Do not use the characters `|` or tab anywhere. Do not use " - " or " : " or " = " (spaces around them) inside `q` or `a`.
- Cover every grammar point named in the unit (if a unit has two points, split the items between them).
- Check every answer twice. A wrong key is worse than no exercise.

When you finish, run this check and fix anything it reports:
`python tools/check_grammar.py <book>`

Final reply: one line per book with the number of units and items written, and any unit whose grammar point you had to guess.
