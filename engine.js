import { TOPICS } from "./data.js";

const EPSILON = 1e-12;

export function tokenize(text) {
  return text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9’'-]+/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 2 && !STOP_WORDS.has(token));
}

const STOP_WORDS = new Set([
  "and", "the", "for", "that", "with", "from", "this", "will", "has", "have",
  "asks", "says", "also", "while", "more", "than", "into", "rather", "whether",
  "hong", "kong", "government", "secretary", "response", "question", "artificial",
  "intelligence", "technology", "public", "development",
]);

export function tfidfVectors(documents) {
  const tokenised = documents.map(tokenize);
  const vocabulary = [...new Set(tokenised.flat())].sort();
  const documentFrequency = new Map(
    vocabulary.map((term) => [term, tokenised.filter((doc) => doc.includes(term)).length]),
  );

  return tokenised.map((tokens) => {
    const counts = new Map();
    for (const token of tokens) counts.set(token, (counts.get(token) || 0) + 1);
    const vector = new Map();
    for (const [term, count] of counts) {
      const tf = count / Math.max(tokens.length, 1);
      const idf = Math.log((documents.length + 1) / ((documentFrequency.get(term) || 0) + 1)) + 1;
      vector.set(term, tf * idf);
    }
    return vector;
  });
}

export function cosineSimilarity(a, b) {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (const value of a.values()) normA += value * value;
  for (const value of b.values()) normB += value * value;
  const [small, large] = a.size < b.size ? [a, b] : [b, a];
  for (const [term, value] of small) dot += value * (large.get(term) || 0);
  return dot / (Math.sqrt(normA) * Math.sqrt(normB) + EPSILON);
}

export function similarityMatrix(turns) {
  const vectors = tfidfVectors(turns.map((turn) => turn.summary));
  return vectors.map((vectorA) => vectors.map((vectorB) => cosineSimilarity(vectorA, vectorB)));
}

export function normaliseTopicWeights(weights = {}) {
  const populated = Object.fromEntries(TOPICS.map(({ id }) => [id, Math.max(0, Number(weights[id] ?? 0))]));
  const total = Object.values(populated).reduce((sum, value) => sum + value, 0) || 1;
  return Object.fromEntries(Object.entries(populated).map(([key, value]) => [key, value / total]));
}

export function scoreTurn(turn, objective) {
  const weights = normaliseTopicWeights(objective.topicWeights);
  const topicScore = turn.topics.reduce((sum, topic) => sum + weights[topic], 0);
  const evidenceScore = Math.min(1, turn.evidenceMarkers / 5);
  const specificity = Math.min(1, turn.evidenceMarkers / Math.sqrt(Math.max(turn.words, 1)) * 4.5);
  const questionValue = turn.role === "member" ? 0.06 : 0;
  return 0.72 * topicScore + 0.17 * evidenceScore + 0.11 * specificity + questionValue;
}

export function selectTurns(turns, objective) {
  const matrix = similarityMatrix(turns);
  const selected = [];
  const selectedIndices = [];
  const uncoveredTopics = new Set(TOPICS.map(({ id }) => id));
  const seenSpeakers = new Set();
  const seenRoles = new Set();
  const size = Math.max(2, Math.min(turns.length, Number(objective.size || 5)));

  while (selected.length < size) {
    let best = null;
    for (let index = 0; index < turns.length; index += 1) {
      if (selectedIndices.includes(index)) continue;
      const turn = turns[index];
      const relevance = scoreTurn(turn, objective);
      const newTopics = turn.topics.filter((topic) => uncoveredTopics.has(topic));
      const topicNovelty = newTopics.length / Math.max(turn.topics.length, 1);
      const speakerNovelty = seenSpeakers.has(turn.speaker) ? 0 : 1;
      const roleNovelty = seenRoles.has(turn.role) ? 0 : 1;
      const redundancy = selectedIndices.length
        ? Math.max(...selectedIndices.map((selectedIndex) => matrix[index][selectedIndex]))
        : 0;

      const utility =
        objective.relevance * relevance +
        objective.topicCoverage * topicNovelty +
        objective.speakerDiversity * (0.78 * speakerNovelty + 0.22 * roleNovelty) -
        objective.redundancyPenalty * redundancy;

      const candidate = { turn, index, utility, relevance, redundancy, newTopics };
      if (
        !best ||
        candidate.utility > best.utility + EPSILON ||
        (Math.abs(candidate.utility - best.utility) <= EPSILON && turn.id < best.turn.id)
      ) {
        best = candidate;
      }
    }

    if (!best) break;
    selected.push({
      ...best.turn,
      selectionUtility: best.utility,
      relevanceScore: best.relevance,
      redundancyAtSelection: best.redundancy,
    });
    selectedIndices.push(best.index);
    seenSpeakers.add(best.turn.speaker);
    seenRoles.add(best.turn.role);
    for (const topic of best.turn.topics) uncoveredTopics.delete(topic);
  }

  return selected.sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)));
}

export function naiveTopK(turns, objective) {
  return [...turns]
    .map((turn) => ({ ...turn, relevanceScore: scoreTurn(turn, objective) }))
    .sort((a, b) => b.relevanceScore - a.relevanceScore || a.id.localeCompare(b.id))
    .slice(0, objective.size);
}

function topicDistribution(turns) {
  const counts = Object.fromEntries(TOPICS.map(({ id }) => [id, 0]));
  for (const turn of turns) {
    const contribution = turn.words / Math.max(turn.topics.length, 1);
    for (const topic of turn.topics) counts[topic] += contribution;
  }
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0) || 1;
  return Object.fromEntries(Object.entries(counts).map(([topic, value]) => [topic, value / total]));
}

function klDivergence(p, q) {
  return Object.keys(p).reduce((sum, key) => {
    if (p[key] <= 0) return sum;
    return sum + p[key] * Math.log2(p[key] / Math.max(q[key], EPSILON));
  }, 0);
}

export function jensenShannonDivergence(p, q) {
  const midpoint = Object.fromEntries(Object.keys(p).map((key) => [key, (p[key] + q[key]) / 2]));
  return 0.5 * klDivergence(p, midpoint) + 0.5 * klDivergence(q, midpoint);
}

export function meanPairwiseSimilarity(turns) {
  if (turns.length < 2) return 0;
  const matrix = similarityMatrix(turns);
  let total = 0;
  let pairs = 0;
  for (let i = 0; i < turns.length; i += 1) {
    for (let j = i + 1; j < turns.length; j += 1) {
      total += matrix[i][j];
      pairs += 1;
    }
  }
  return total / pairs;
}

export function auditSelection(corpus, selected) {
  const corpusSpeakers = new Set(corpus.map((turn) => turn.speaker));
  const selectedSpeakers = new Set(selected.map((turn) => turn.speaker));
  const selectedTopics = new Set(selected.flatMap((turn) => turn.topics));
  const totalWords = corpus.reduce((sum, turn) => sum + turn.words, 0);
  const retainedWords = selected.reduce((sum, turn) => sum + turn.words, 0);
  const governmentWords = selected
    .filter((turn) => turn.role === "government")
    .reduce((sum, turn) => sum + turn.words, 0);
  const recordDistribution = topicDistribution(corpus);
  const selectedDistribution = topicDistribution(selected);

  return {
    selectedTurns: selected.length,
    speakerCoverage: selectedSpeakers.size / corpusSpeakers.size,
    speakerCount: selectedSpeakers.size,
    topicCoverage: selectedTopics.size / TOPICS.length,
    topicCount: selectedTopics.size,
    retainedWordShare: retainedWords / totalWords,
    governmentWordShare: governmentWords / Math.max(retainedWords, 1),
    recordGovernmentWordShare:
      corpus.filter((turn) => turn.role === "government").reduce((sum, turn) => sum + turn.words, 0) /
      totalWords,
    representationGap: jensenShannonDivergence(recordDistribution, selectedDistribution),
    meanRedundancy: meanPairwiseSimilarity(selected),
    traceability: selected.every((turn) => turn.id && turn.page) ? 1 : 0,
    uncoveredTopics: TOPICS.filter(({ id }) => !selectedTopics.has(id)).map(({ label }) => label),
    selectedIds: selected.map((turn) => turn.id),
  };
}

function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}

function jaccard(idsA, idsB) {
  const a = new Set(idsA);
  const b = new Set(idsB);
  const intersection = [...a].filter((id) => b.has(id)).length;
  return intersection / (new Set([...a, ...b]).size || 1);
}

export function stabilityAnalysis(turns, objective, samples = 200, seed = 20240131) {
  const baseline = selectTurns(turns, objective).map((turn) => turn.id);
  const inclusions = Object.fromEntries(turns.map((turn) => [turn.id, 0]));
  const random = seededRandom(seed);
  let overlap = 0;

  for (let sample = 0; sample < samples; sample += 1) {
    const topicWeights = Object.fromEntries(
      Object.entries(objective.topicWeights).map(([topic, weight]) => {
        const perturbed = weight * (0.82 + random() * 0.36);
        return [topic, perturbed];
      }),
    );
    const trial = selectTurns(turns, { ...objective, topicWeights });
    const ids = trial.map((turn) => turn.id);
    for (const id of ids) inclusions[id] += 1;
    overlap += jaccard(baseline, ids);
  }

  return {
    samples,
    seed,
    baseline,
    meanJaccard: overlap / samples,
    inclusionFrequency: Object.fromEntries(
      Object.entries(inclusions).map(([id, count]) => [id, count / samples]),
    ),
  };
}

function dominates(a, b) {
  const atLeastAsGood =
    a.relevance >= b.relevance &&
    a.representation >= b.representation &&
    a.speakerCoverage >= b.speakerCoverage;
  const strictlyBetter =
    a.relevance > b.relevance ||
    a.representation > b.representation ||
    a.speakerCoverage > b.speakerCoverage;
  return atLeastAsGood && strictlyBetter;
}

export function paretoAlternatives(turns, objective) {
  const candidates = [];
  for (const relevance of [0.28, 0.36, 0.44, 0.52]) {
    for (const diversity of [0.12, 0.2, 0.28]) {
      for (const redundancy of [0.08, 0.14, 0.2]) {
        const coverage = Math.max(0.08, 1 - relevance - diversity - redundancy);
        const variant = {
          ...objective,
          relevance,
          speakerDiversity: diversity,
          redundancyPenalty: redundancy,
          topicCoverage: coverage,
        };
        const selected = selectTurns(turns, variant);
        const audit = auditSelection(turns, selected);
        const meanRelevance =
          selected.reduce((sum, turn) => sum + scoreTurn(turn, variant), 0) / selected.length;
        candidates.push({
          ids: selected.map((turn) => turn.id),
          relevance: meanRelevance,
          representation: 1 - audit.representationGap,
          speakerCoverage: audit.speakerCoverage,
          audit,
        });
      }
    }
  }

  const unique = [...new Map(candidates.map((candidate) => [candidate.ids.join("-"), candidate])).values()];
  return unique
    .filter((candidate) => !unique.some((other) => other !== candidate && dominates(other, candidate)))
    .sort((a, b) => b.representation - a.representation || b.relevance - a.relevance);
}

export function formatPercent(value, digits = 0) {
  return `${(value * 100).toFixed(digits)}%`;
}
