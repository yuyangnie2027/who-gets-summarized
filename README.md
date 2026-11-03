# WHO GETS SUMMARIZED?

**Yuyang Nie · Interactive editorial research prototype · 2026**

- Public demonstrator: https://yuyangnie2027.github.io/who-gets-summarized/
- Public source repository: https://github.com/yuyangnie2027/who-gets-summarized

“Who Gets Summarized?” is a provenance-first instrument for examining what
disappears when a long public record becomes a short policy brief. It is designed
for editors, researchers and civic-media teams who want to compare several
defensible compressions of the same record before publication.

The case study uses the Hong Kong Legislative Council’s official English record
of the oral question “Developing artificial intelligence” from 31 January 2024.
The source exchange spans printed pages 49–59 and contains 14 substantive turns,
7 speakers and 3,463 English words. Government responses account for 63.8% of
the record’s words.

The interface stores author-reviewed paraphrases beside speaker, role, turn type
and printed-page provenance, then runs a deterministic selection and audit
pipeline in the browser.

## Purpose

Automated summaries are often assessed for fluency and factual correctness.
This project focuses on an earlier editorial question: which parts of a public
record receive attention, and which disappear, when a document is compressed?

The prototype supports three actions:

1. select source turns with an explicit editorial objective;
2. inspect every retained and omitted turn;
3. compare coverage, redundancy, topic-distribution shift and parameter stability.

## Run

```bash
npm test
npm run check
npm run serve
```

Open `http://127.0.0.1:4173`.

The public build runs directly in a modern browser.

## Implemented methods

- source integrity record with OData identifiers and SHA-256 checksum;
- speaker-turn segmentation and page-level provenance;
- eight transparent editorial topic labels;
- TF–IDF vectors and cosine similarity;
- multi-objective, diversity-aware MMR selection;
- speaker, role and topic novelty accounting;
- Jensen–Shannon divergence between record and brief topic distributions;
- 200-run seeded sensitivity analysis with turn inclusion frequency;
- Pareto search across relevance, representation and speaker coverage;
- deterministic tests for data integrity, provenance and model behaviour.

## Repository map

```text
dist/
  index.html            research narrative and accessible interface
  styles.css            responsive editorial design system
  src/
    app.js              interaction, rendering and audit state
    data.js             official source record and 14 derived turns
    engine.js           TF–IDF, MMR, JSD, stability and Pareto analysis
docs/
  METHODOLOGY.md         data pipeline, formulas and limitations
  PORTFOLIO_STATEMENT.md submission-ready project statement
  DEMO_SCRIPT.md         concise walkthrough
  RESEARCH_NOTES.md      design rationale and research lineage
scripts/
  fetch-source.mjs      reproducible metadata and source acquisition
  check.mjs             structural, provenance and offline checks
  create_portfolio_pdf.py
```

## Primary source

- Legislative Council Official Record of Proceedings, 31 January 2024,
  “Developing artificial intelligence,” printed pages 49–59.
- LegCo Hansard Open Data record: Rundown ID `1291567`, Hansard ID `6481`.
- Stored source PDF SHA-256:
  `2aa29c311ce071cc196fcf8046345bcfbd93515f541af38af15fea53301a6f0d`.

The distributed dataset contains author-reviewed paraphrases and derived
measurements with page-level links to the official record.

## Author

Research, data modelling, interaction design, visual design and front-end
engineering by Yuyang Nie.
