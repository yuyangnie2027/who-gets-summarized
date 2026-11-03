# Methodology

## Research question

When a long, attributable public record is compressed into a short policy brief,
how can an editorial system keep source selection, omission and parameter
sensitivity visible?

## Case selection

The prototype uses the Hong Kong Legislative Council oral question “Developing
artificial intelligence,” recorded on 31 January 2024. The case was selected
because it is bounded, officially published, attributable and internally varied.
The exchange moves across strategy, infrastructure, work, law, public
applications, SME adoption, data governance and deepfake regulation.

Primary source:

- Official English translation, printed pages 49–59;
- Rundown ID `1291567`;
- Hansard ID `6481`;
- SHA-256 `2aa29c311ce071cc196fcf8046345bcfbd93515f541af38af15fea53301a6f0d`.

## Data preparation

1. Query the LegCo Hansard OData service for meeting metadata.
2. Download the official English PDF and record its checksum.
3. Isolate the question from the heading through the final answer.
4. Segment the record at speaker headings.
5. Remove running headers and printed page numbers from word-count calculations.
6. Preserve source order, speaker, institutional role, turn type and printed pages.
7. Write a compact paraphrase for interface display and assign topic labels.

The resulting dataset contains 14 substantive turns, 7 speakers and 3,463 words.
The office of the Secretary for Innovation, Technology and Industry accounts for
2,209 words, or 63.8% of the exchange. Interface text is explicitly labelled as
paraphrase. The official record remains the authority for exact wording.

## Representation and relevance

Each turn is represented by:

- a TF–IDF vector calculated from its paraphrase;
- an eight-dimensional binary topic vector;
- speaker and institutional-role identifiers;
- source specificity, approximated by the number of named policies, programmes
  or institutions in the turn;
- source word count and page provenance.

The relevance score combines topic alignment, source specificity and a small
question-value term. The term protects interrogative turns from being crowded out
by longer, more detailed answers; it does not assert that a question is more true.

## Diversity-aware selection

At each iteration the selector evaluates every remaining turn:

```text
U(t) = αR(t) + βC(t) + γS(t) − δ max sim(t, s)
```

where:

- `R(t)` is editorial-topic relevance and source specificity;
- `C(t)` is the proportion of the turn’s topics not yet represented;
- `S(t)` rewards a new speaker and, to a lesser degree, a new institutional role;
- `sim(t, s)` is the maximum TF–IDF cosine similarity with a selected turn;
- `α, β, γ, δ` are visible interface parameters or preset values.

This is a transparent variant of Maximal Marginal Relevance. It does not create a
summary sentence; it selects source-linked turns that can be paraphrased and
reviewed.

## Audit metrics

The interface reports:

- turn retention and word retention;
- unique-speaker coverage;
- topic coverage;
- government word share in the selected brief and full record;
- mean pairwise TF–IDF similarity as a redundancy diagnostic;
- page-level traceability;
- Jensen–Shannon divergence between full-record and brief topic distributions.

Jensen–Shannon divergence is symmetric and bounded. In this project it is called
the “representation gap.” A lower score means the selected brief’s topic mix is
closer to the complete record. It cannot determine fairness on its own.

## Sensitivity and alternatives

The sensitivity module performs 200 seeded trials. Each trial perturbs every
topic weight within ±18% and reruns the selector. It reports:

- inclusion frequency for each turn;
- mean Jaccard overlap with the baseline selection.

The Pareto module evaluates combinations of relevance, topic coverage, speaker
diversity and redundancy penalty. A brief is retained on the frontier only if no
other candidate is simultaneously better in average relevance,
topic-distribution fidelity and speaker coverage.

## Limitations

- Topic annotation and paraphrase remain human editorial decisions.
- The official English translation may not preserve every nuance of Cantonese or
  Putonghua delivery.
- One exchange cannot represent the legislature or Hong Kong’s AI policy debate.
- Source specificity rewards named programmes; it does not verify effectiveness.
- The selector does not assess truth, political intent or social impact.
- Page-level provenance supports review but does not replace reading the source.

The prototype should therefore be evaluated as an argument about interface and
editorial accountability, not as a neutral or production-ready summarizer.
