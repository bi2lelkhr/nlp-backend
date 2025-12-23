const API = "http://127.0.0.1:5000/api";

let selectedCountryId = null;
let chart = null;

// ----------------------
// COUNTRY AUTOCOMPLETE
// ----------------------
const countryInput = document.getElementById("countryInput");
const countrySuggestions = document.getElementById("countrySuggestions");

countryInput.addEventListener("input", async () => {
  const q = countryInput.value.trim();
  if (!q) {
    countrySuggestions.innerHTML = "";
    return;
  }

  const res = await fetch(`${API}/countries/search?q=${q}`);
  const data = await res.json();

  countrySuggestions.innerHTML = data.map(c =>
    `<div onclick="selectCountry('${c.id}', '${c.name}')">${c.name}</div>`
  ).join("");
});

function selectCountry(id, name) {
  selectedCountryId = id;
  countryInput.value = name;
  countrySuggestions.innerHTML = "";

  document.getElementById("institutionInput").disabled = false;
  document.getElementById("institutionInput").value = "";
  document.getElementById("stats").innerHTML = "";

  if (chart) chart.destroy();
}

// ----------------------
// INSTITUTION AUTOCOMPLETE
// ----------------------
const institutionInput = document.getElementById("institutionInput");
const institutionSuggestions = document.getElementById("institutionSuggestions");

institutionInput.addEventListener("input", async () => {
  const q = institutionInput.value.trim();
  if (!q || !selectedCountryId) return;

  const res = await fetch(
    `${API}/institutions/search?country_id=${selectedCountryId}&q=${q}`
  );
  const data = await res.json();

  institutionSuggestions.innerHTML = data.map(i =>
    `<div onclick="selectInstitution('${i.id}', '${i.name}')">${i.name}</div>`
  ).join("");
});

async function selectInstitution(id, name) {
  institutionInput.value = name;
  institutionSuggestions.innerHTML = "";

  loadOverview(id);
  loadFields(id);
}

// ----------------------
// LOAD OVERVIEW
// ----------------------
async function loadOverview(id) {
  const d = await fetch(`${API}/institution/${id}/overview`).then(r => r.json());

  document.getElementById("stats").innerHTML = `
    <div class="stat">H-index<br><span>${d.average_h_index}</span></div>
    <div class="stat">RII<br><span>${d.average_rii}</span></div>
    <div class="stat">Rank<br><span>#${d.ranking}</span></div>
  `;
}

// ----------------------
// LOAD FIELD STATS
// ----------------------
async function loadFields(id) {
  const data = await fetch(`${API}/institution/${id}/fields`).then(r => r.json());

  const labels = data.map(d => d.field);
  const values = data.map(d => d.percentage);

  if (chart) chart.destroy();

  chart = new Chart(document.getElementById("fieldsChart"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values
      }]
    }
  });
}
