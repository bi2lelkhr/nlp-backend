const API = "http://127.0.0.1:5000/api";
let chart;

const input = document.getElementById("countryInput");
const suggestions = document.getElementById("suggestions");

input.addEventListener("input", async () => {
  const q = input.value;
  if (!q) return suggestions.innerHTML = "";

  const res = await fetch(`${API}/countries/search?q=${q}`);
  const data = await res.json();

  suggestions.innerHTML = data.map(c =>
    `<div onclick="selectCountry('${c.id}','${c.name}')">${c.name}</div>`
  ).join("");
});

async function selectCountry(id, name) {
  input.value = name;
  suggestions.innerHTML = "";

  loadOverview(id);
  loadInstitutions(id);
  loadFields(id);
}

async function loadOverview(id) {
  const d = await fetch(`${API}/country/${id}/overview`).then(r => r.json());
  document.getElementById("stats").innerHTML = `
    <div class="card">H-index<br><b>${d.average_h_index}</b></div>
    <div class="card">RII<br><b>${d.average_rii}</b></div>
    <div class="card">Rank<br><b>#${d.ranking}</b></div>
  `;
}

async function loadInstitutions(id) {
  const d = await fetch(`${API}/country/${id}/institutions`).then(r => r.json());
  document.getElementById("institutions").innerHTML =
    d.by_h_index.map(i => `<p>${i.name} (${i.average_h_index})</p>`).join("");
}

async function loadFields(id) {
  const data = await fetch(`${API}/country/${id}/fields`).then(r => r.json());

  const labels = data.map(d => d.field);
  const values = data.map(d => d.percentage);

  if (chart) chart.destroy();
  chart = new Chart(document.getElementById("fieldsChart"), {
    type: "doughnut",
    data: { labels, datasets: [{ data: values }] }
  });
}
