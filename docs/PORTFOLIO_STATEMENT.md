# Portfolio Statement

“Who Gets Summarized?” is an interactive editorial audit designed by Yuyang Nie.
It examines a practical consequence of AI-assisted media production: before a
system writes a fluent brief, it must decide which source material will receive
attention.

The prototype studies one official Hong Kong Legislative Council exchange on AI
development. The 31 January 2024 record spans printed pages 49–59, 14 substantive
turns, 7 speakers and 3,463 English words. Instead of replacing this record with
one opaque answer, the interface lets a reader compare editorial objectives and
inspect every retained and omitted turn.

The technical system is intentionally transparent. A local TF–IDF model estimates
textual similarity. A diversity-aware selection routine balances topic relevance,
new topic coverage, new speakers and redundancy. Jensen–Shannon divergence
measures how far the selected topic distribution moves from the full record. Two
hundred seeded perturbations reveal whether a result is stable, while a Pareto
search exposes alternative briefs that make different defensible trade-offs.

The work is designed for editors, researchers and civic-media teams. It does not
claim to identify truth or produce a politically neutral summary. Its contribution
is an interface that treats provenance, omission and sensitivity as first-class
media objects rather than footnotes.

I developed the research framing, source data model, interaction design, visual
system, selection engine, audit metrics, tests and portfolio document. The project
reflects my interest in AI not only as a content generator, but as an editorial
infrastructure whose values should be visible and contestable.
