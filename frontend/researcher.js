const API = "http://127.0.0.1:5000/api";

const input = document.getElementById("researcherInput");
const suggestions = document.getElementById("suggestions");
let chart = null;

// ----------------------
// AUTOCOMPLETE
// ----------------------
input.addEventListener("input", async () => {
  const q = input.value.trim();
  if (!q) {
    suggestions.innerHTML = "";
    return;
  }

  const res = await fetch(`${API}/researchers/search?q=${q}`);
  const data = await res.json();

  suggestions.innerHTML = data.map(r =>
    `<div onclick="selectResearcher('${r.id}','${r.full_name}')">${r.full_name}</div>`
  ).join("");
});

async function selectResearcher(id, name) {
  input.value = name;
  suggestions.innerHTML = "";

  loadProfile(id);
  loadArticles(id);
  loadCoauthors(id);
  loadFields(id);
}

// ----------------------
// PROFILE
// ----------------------
async function loadProfile(id) {
  const d = await fetch(`${API}/researcher/${id}/overview`).then(r => r.json());

  document.getElementById("profile").innerHTML = `
    <div class="stat">H-index<br><span>${d.h_index}</span></div>
    <div class="stat">RII<br><span>${d.rii}</span></div>
    <div class="stat">Publications<br><span>${d.total_publications}</span></div>
    <div class="stat">Citations<br><span>${d.total_citations}</span></div>
  `;
}

// ----------------------
// ARTICLES
// ----------------------
async function loadArticles(id) {
  const data = await fetch(`${API}/researcher/${id}/articles`).then(r => r.json());

  const tbody = document.querySelector("#articles tbody");
  tbody.innerHTML = data.map(a => `
    <tr>
      <td>${a.title}</td>
      <td>${a.journal_name || "-"}</td>
      <td>${a.publication_date ? a.publication_date.slice(0,4) : "-"}</td>
      <td>${a.cited_by_count}</td>
    </tr>
  `).join("");
}

// ----------------------
// CO-AUTHORS
// ----------------------
async function loadCoauthors(id) {
  const data = await fetch(`${API}/researcher/${id}/coauthors`).then(r => r.json());

  document.getElementById("coauthors").innerHTML =
    data.map(c => `
      <div class="coauthor">
        <b>${c.name}</b><br>
        Shared papers: ${c.shared_articles}
      </div>
    `).join("");
}

// ----------------------
// FIELD STATS
// ----------------------
async function loadFields(id) {
  const data = await fetch(`${API}/researcher/${id}/fields`).then(r => r.json());

  const labels = data.map(d => d.field);
  const values = data.map(d => d.percentage);

  if (chart) chart.destroy();

  chart = new Chart(document.getElementById("fieldsChart"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values }]
    }
  });
}
