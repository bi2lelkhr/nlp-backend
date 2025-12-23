const API = "http://127.0.0.1:5000/api/overview";

async function loadSection(endpoint, containerId, nameKey, valueKey, label) {
  const res = await fetch(`${API}/${endpoint}`);
  const data = await res.json();

  const container = document.getElementById(containerId);
  container.innerHTML = `
    <div class="metric">
      <h3>🏆 By ${label}</h3>
      ${data.by_h_index.map(item => `
        <div class="item">
          ${item[nameKey]}
          <span class="value">${item[valueKey]}</span>
        </div>
      `).join("")}
    </div>

    <div class="metric">
      <h3>🔥 By RII</h3>
      ${data.by_rii.map(item => `
        <div class="item">
          ${item[nameKey]}
          <span class="value">${item.rii || item.average_rii}</span>
        </div>
      `).join("")}
    </div>
  `;
}

loadSection("countries", "countries", "name", "average_h_index", "H-index");
loadSection("institutions", "institutions", "name", "average_h_index", "H-index");
loadSection("researchers", "researchers", "full_name", "h_index", "H-index");
