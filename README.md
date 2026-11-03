# WHO GETS SUMMARIZED?

**Yuyang Nie · Interactive editorial research prototype · 2026**

[Open the public demonstrator](https://yuyangnie2027.github.io/who-gets-summarized/)

“Who Gets Summarized?” is a provenance-first instrument for examining what
disappears when a long public record becomes a short policy brief. It uses the
Hong Kong Legislative Council’s official English record of the oral question
“Developing artificial intelligence” from 31 January 2024: 14 substantive
turns, 7 speakers and 3,463 words across printed pages 49–59.

The interface runs entirely in the browser. It does not call a remote model or
hide the selection rule. Readers can choose an editorial objective, change
eight topic priorities, inspect retained and omitted turns, and compare source
coverage with the resulting brief.

## Implemented methods

- source-linked turn records with speaker, role, order and printed-page provenance;
- TF–IDF vectors and cosine-similarity redundancy control;
- diversity-aware maximal marginal relevance selection;
- speaker, role and topic novelty accounting;
- Jensen–Shannon divergence between source and brief topic distributions;
- 200-run seeded sensitivity analysis with turn-inclusion frequency;
- Pareto comparison across relevance, representation and speaker coverage.

## Repository map

```text
index.html   research narrative and accessible interface
styles.css   responsive editorial design system
app.js       interaction, rendering and audit state
data.js      source metadata and 14 derived turn records
engine.js    TF–IDF, MMR, divergence, stability and Pareto analysis
```

## Source and limitations

The case record comes from the Legislative Council of the Hong Kong SAR:

- [Official English record](https://www.legco.gov.hk/yr2024/english/counmtg/hansard/cm20240131-translate-e.pdf#nameddest=orq05)
- [Council agenda](https://www.legco.gov.hk/yr2024/english/counmtg/agenda/cm20240131.htm)
- [Hansard open-data documentation](https://www.legco.gov.hk/en/open-legco/open-data/hansard-database.html)

The dataset stores authored paraphrases and derived measurements, not a
republished transcript. The prototype audits editorial compression; it is not
a truth classifier or a claim of political neutrality.

## Author

Research, data modelling, interaction design, visual design and front-end
engineering by Yuyang Nie.
