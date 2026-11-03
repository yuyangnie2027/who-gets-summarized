import { PRESETS, SOURCE, TOPICS, TURNS } from "./data.js";
import {
  auditSelection,
  formatPercent,
  paretoAlternatives,
  selectTurns,
  stabilityAnalysis,
} from "./engine.js";

const presetList = document.querySelector("#preset-list");
const briefTitle = document.querySelector("#brief-title");
const briefNote = document.querySelector("#brief-note");
const metricGrid = document.querySelector("#metric-grid");
const briefOutput = document.querySelector("#brief-output");
const turnLedger = document.querySelector("#turn-ledger");
const stabilityChart = document.querySelector("#stability-chart");
const stabilityScore = document.querySelector("#stability-score");
const paretoCount = document.querySelector("#pareto-count");
const interpretation = document.querySelector("#interpretation");

const topicInputs = Object.fromEntries(
  TOPICS.map(({ id }) => [id, document.querySelector(`#${id}`)]),
);
const sizeInput = document.querySelector("#size");
let activePreset = "balanced";

function currentObjective() {
  const base = PRESETS[activePreset] || PRESETS.balanced;
  return {
    ...base,
    id: activePreset || "custom",
    name: activePreset ? base.name : "Custom editorial objective",
    note: activePreset
      ? base.note
      : "The weighting is manually configured. Selection remains deterministic and source-linked.",
    size: Number(sizeInput.value),
    topicWeights: Object.fromEntries(
      TOPICS.map(({ id }) => [id, Number(topicInputs[id].value) / 100]),
    ),
  };
}

function setControls(objective) {
  for (const { id } of TOPICS) {
    const value = Math.round(objective.topicWeights[id] * 100);
    topicInputs[id].value = value;
    document.querySelector(`#${id}-value`).textContent = value;
  }
  sizeInput.value = objective.size;
  document.querySelector("#size-value").textContent = objective.size;
}

function renderPresets() {
  presetList.innerHTML = Object.values(PRESETS)
    .map(
      (preset) => `
        <button class="preset-button" type="button" data-preset="${preset.id}" aria-pressed="${activePreset === preset.id}">
          <strong>${preset.name}</strong>
          <span>${preset.note}</span>
        </button>`,
    )
    .join("");

  for (const button of presetList.querySelectorAll("button")) {
    button.addEventListener("click", () => {
      activePreset = button.dataset.preset;
      setControls(PRESETS[activePreset]);
      renderPresets();
      render();
    });
  }
}

function metric(label, value) {
  return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`;
}

function renderBrief(selected, audit, objective) {
  briefTitle.textContent = objective.name;
  briefNote.textContent = objective.note;
  metricGrid.innerHTML = [
    metric("turns retained", `${audit.selectedTurns} / ${TURNS.length}`),
    metric("speaker coverage", `${audit.speakerCount} / 7`),
    metric("topic coverage", `${audit.topicCount} / ${TOPICS.length}`),
    metric("words retained", formatPercent(audit.retainedWordShare)),
    metric("representation gap", audit.representationGap.toFixed(3)),
  ].join("");

  briefOutput.innerHTML = selected
    .map(
      (turn) => `
        <article class="brief-turn">
          <div class="brief-id">${turn.id}</div>
          <div>
            <h4>${turn.speakerLabel} · ${turn.turnType}</h4>
            <p>${turn.summary}</p>
            <span class="paraphrase-tag">AUTHOR’S PARAPHRASE · NOT A QUOTATION</span>
          </div>
          <div class="brief-source">Official record<br />p. ${turn.page}</div>
        </article>`,
    )
    .join("");
}

function renderLedger(selected) {
  const selectedIds = new Set(selected.map((turn) => turn.id));
  turnLedger.innerHTML = TURNS.map((turn) => {
    const isSelected = selectedIds.has(turn.id);
    const pills = turn.topics
      .map((topic) => `<span title="${TOPICS.find((item) => item.id === topic)?.label}">${TOPICS.find((item) => item.id === topic)?.short}</span>`)
      .join("");
    return `
      <div class="ledger-row ${isSelected ? "selected" : ""}">
        <span class="ledger-id">${turn.id}</span>
        <span class="ledger-speaker"><strong>${turn.speaker}</strong><span>${turn.turnType}</span></span>
        <span class="ledger-page">p. ${turn.page}</span>
        <span class="topic-pills ledger-topics">${pills}</span>
        <span class="ledger-status">${isSelected ? "retained" : "omitted"}</span>
      </div>`;
  }).join("");
}

function renderStability(stability, selectedIds) {
  const selected = new Set(selectedIds);
  const rows = TURNS.map((turn) => ({
    turn,
    frequency: stability.inclusionFrequency[turn.id],
  })).sort((a, b) => b.frequency - a.frequency || a.turn.id.localeCompare(b.turn.id));

  stabilityChart.innerHTML = rows
    .map(
      ({ turn, frequency }) => `
        <div class="stability-row" title="${turn.speaker}: ${formatPercent(frequency, 1)} inclusion">
          <span>${turn.id}${selected.has(turn.id) ? "•" : ""}</span>
          <span class="stability-track"><span class="stability-fill" style="width:${frequency * 100}%"></span></span>
          <span>${formatPercent(frequency)}</span>
        </div>`,
    )
    .join("");
}

function renderInterpretation(audit) {
  const missing = audit.uncoveredTopics.length
    ? `It leaves ${audit.uncoveredTopics.join(", ").toLowerCase()} outside the brief.`
    : "It retains at least one turn for every annotated topic.";
  const governmentShift = audit.governmentWordShare - audit.recordGovernmentWordShare;
  const shiftCopy = Math.abs(governmentShift) < 0.02
    ? "The selected government word share stays close to the full record."
    : `The selected government word share is ${formatPercent(Math.abs(governmentShift), 1)} ${governmentShift > 0 ? "higher" : "lower"} than the full record.`;
  interpretation.textContent =
    `Reading the current brief: ${formatPercent(audit.speakerCoverage)} of speakers and ${formatPercent(audit.topicCoverage)} of topics remain visible. ${missing} ${shiftCopy} The representation-gap score is ${audit.representationGap.toFixed(3)}; it should be compared across alternatives, not treated as a universal quality score.`;
}

function render() {
  const objective = currentObjective();
  const selected = selectTurns(TURNS, objective);
  const audit = auditSelection(TURNS, selected);
  const stability = stabilityAnalysis(TURNS, objective, 200, 20240131);
  const frontier = paretoAlternatives(TURNS, objective);

  renderBrief(selected, audit, objective);
  renderLedger(selected);
  renderStability(stability, audit.selectedIds);
  renderInterpretation(audit);
  stabilityScore.textContent = formatPercent(stability.meanJaccard, 1);
  paretoCount.textContent = String(frontier.length).padStart(2, "0");
}

for (const { id } of TOPICS) {
  topicInputs[id].addEventListener("input", () => {
    activePreset = null;
    document.querySelector(`#${id}-value`).textContent = topicInputs[id].value;
    renderPresets();
    render();
  });
}

sizeInput.addEventListener("input", () => {
  activePreset = null;
  document.querySelector("#size-value").textContent = sizeInput.value;
  renderPresets();
  render();
});

document.documentElement.dataset.source = SOURCE.id;
setControls(PRESETS.balanced);
renderPresets();
render();
