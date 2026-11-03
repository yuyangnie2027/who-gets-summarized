# Research Notes

## Design direction

The interface borrows from public-record archives, newspaper research desks and
legislative papers rather than common “AI product” aesthetics. Warm paper, dark
ink, narrow rules, serif display type and restrained blue/rust accents keep the
source document—not a technological spectacle—at the centre.

## Research contribution

The project moves provenance inside the act of summarization. Every output unit
retains a speaker, institutional role, turn type and printed page. The omitted
ledger stays visible beside the generated brief, and stability is treated as part
of the result rather than a hidden engineering detail.

## Technical contribution

- deterministic, dependency-free runtime;
- TF–IDF and cosine similarity implemented locally;
- diversity-aware MMR selection with role and topic novelty;
- bounded, symmetric representation-gap metric using Jensen–Shannon divergence;
- seeded perturbation analysis with turn-level inclusion frequency;
- Pareto-frontier search for alternative editorial briefs;
- source-integrity and behaviour tests.

## Next research phase

1. Compare official English and Chinese records without treating translation as
   lossless.
2. Invite journalists and public-policy researchers to revise the topic ontology
   and selection objectives.
3. Add sentence-level anchors only where the official publication supports stable
   deep links.
4. Evaluate whether omission ledgers change editorial decisions under deadline.
5. Extend the method to several public-record genres before making comparative
   claims.
