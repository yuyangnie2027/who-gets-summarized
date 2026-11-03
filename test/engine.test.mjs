import test from "node:test";
import assert from "node:assert/strict";
import { CORPUS_STATS, PRESETS, SOURCE, TOPICS, TURNS } from "../dist/src/data.js";
import {
  auditSelection,
  cosineSimilarity,
  jensenShannonDivergence,
  meanPairwiseSimilarity,
  naiveTopK,
  paretoAlternatives,
  selectTurns,
  similarityMatrix,
  stabilityAnalysis,
  tfidfVectors,
} from "../dist/src/engine.js";

test("official-source identifiers and checksum are preserved", () => {
  assert.equal(SOURCE.rundownId, 1291567);
  assert.equal(SOURCE.hansardId, 6481);
  assert.match(SOURCE.officialRecordUrl, /^https:\/\/www\.legco\.gov\.hk\//);
  assert.match(SOURCE.openDataDocsUrl, /^https:\/\/www\.legco\.gov\.hk\//);
  assert.match(SOURCE.sourceSha256, /^[a-f0-9]{64}$/);
});

test("derived corpus totals match the official-record segmentation", () => {
  assert.equal(TURNS.length, CORPUS_STATS.substantiveTurns);
  assert.equal(new Set(TURNS.map((turn) => turn.speaker)).size, CORPUS_STATS.speakers);
  assert.equal(TURNS.reduce((sum, turn) => sum + turn.words, 0), CORPUS_STATS.words);
  const governmentWords = TURNS.filter((turn) => turn.role === "government")
    .reduce((sum, turn) => sum + turn.words, 0);
  assert.ok(Math.abs(governmentWords / CORPUS_STATS.words - CORPUS_STATS.governmentWordShare) < 0.001);
});

test("every derived turn retains page-level provenance", () => {
  for (const turn of TURNS) {
    assert.match(turn.id, /^T\d{2}$/);
    assert.match(turn.page, /^\d{2}(?:–\d{2})?$/);
    assert.ok(turn.summary.length > 100);
    assert.ok(turn.topics.length >= 2);
    assert.ok(turn.topics.every((topic) => TOPICS.some(({ id }) => id === topic)));
  }
});

test("TF–IDF cosine similarity is symmetric and bounded", () => {
  const vectors = tfidfVectors(TURNS.map((turn) => turn.summary));
  const ab = cosineSimilarity(vectors[0], vectors[1]);
  const ba = cosineSimilarity(vectors[1], vectors[0]);
  assert.ok(ab >= 0 && ab <= 1);
  assert.ok(Math.abs(ab - ba) < 1e-12);
});

test("selection is deterministic and sorted by source order", () => {
  const first = selectTurns(TURNS, PRESETS.balanced);
  const second = selectTurns(TURNS, PRESETS.balanced);
  assert.deepEqual(first.map(({ id }) => id), second.map(({ id }) => id));
  assert.deepEqual(
    first.map(({ id }) => Number(id.slice(1))),
    first.map(({ id }) => Number(id.slice(1))).toSorted((a, b) => a - b),
  );
});

test("balanced brief covers both institutional roles and most speakers", () => {
  const selected = selectTurns(TURNS, PRESETS.balanced);
  const audit = auditSelection(TURNS, selected);
  assert.deepEqual(new Set(selected.map((turn) => turn.role)), new Set(["member", "government"]));
  assert.ok(audit.speakerCoverage >= 5 / 7);
  assert.ok(audit.topicCoverage >= 0.75);
  assert.equal(audit.traceability, 1);
});

test("diversity-aware selection is no more redundant than naive top-k", () => {
  const selected = selectTurns(TURNS, PRESETS.balanced);
  const naive = naiveTopK(TURNS, PRESETS.balanced);
  assert.ok(meanPairwiseSimilarity(selected) <= meanPairwiseSimilarity(naive) + 1e-12);
});

test("Jensen–Shannon divergence is symmetric and bounded", () => {
  const p = { a: 0.7, b: 0.3 };
  const q = { a: 0.2, b: 0.8 };
  const pq = jensenShannonDivergence(p, q);
  const qp = jensenShannonDivergence(q, p);
  assert.ok(pq >= 0 && pq <= 1);
  assert.ok(Math.abs(pq - qp) < 1e-12);
});

test("seeded stability analysis is reproducible", () => {
  const first = stabilityAnalysis(TURNS, PRESETS.balanced, 200, 20240131);
  const second = stabilityAnalysis(TURNS, PRESETS.balanced, 200, 20240131);
  assert.deepEqual(first, second);
  assert.equal(first.samples, 200);
  assert.ok(first.meanJaccard >= 0 && first.meanJaccard <= 1);
  assert.ok(Object.values(first.inclusionFrequency).every((value) => value >= 0 && value <= 1));
});

test("presets produce meaningfully different source selections", () => {
  const balanced = selectTurns(TURNS, PRESETS.balanced).map(({ id }) => id);
  const policy = selectTurns(TURNS, PRESETS.policy).map(({ id }) => id);
  assert.notDeepEqual(balanced, policy);
});

test("Pareto output contains unique non-empty alternatives", () => {
  const frontier = paretoAlternatives(TURNS, PRESETS.balanced);
  assert.ok(frontier.length >= 1);
  assert.equal(new Set(frontier.map((item) => item.ids.join("-"))).size, frontier.length);
  assert.ok(frontier.every((item) => item.ids.length === PRESETS.balanced.size));
});

test("the full similarity matrix has a unit diagonal and no self-loss", () => {
  const matrix = similarityMatrix(TURNS);
  assert.equal(matrix.length, TURNS.length);
  for (let index = 0; index < matrix.length; index += 1) {
    assert.ok(Math.abs(matrix[index][index] - 1) < 1e-9);
  }
});
