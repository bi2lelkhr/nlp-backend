const API = "http://127.0.0.1:5000";

// ------------------------------------
// Apply filters
// ------------------------------------
async function applyFilters() {
  const country = document.getElementById("countryInput").value.trim();
  const institution = document.getElementById("institutionInput").value.trim();
  const field = document.getElementById("fieldInput").value.trim();

  let url = `${API}/analytics?`;

  if (country) url += `country_id=${country}&`;
  if (institution) url += `institution_id=${institution}&`;
  if (field) url += `field=${encodeURIComponent(field)}`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    if (data.error) {
      alert(data.error);
      return;
    }

    // Metrics
    document.getElementById("avgH").textContent =
      data.metrics.average_h_index ?? "-";
    document.getElementById("avgRii").textContent =
      data.metrics.average_rii ?? "-";

    // Researchers
    fillList("topH", data.top_researchers.by_h_index);
    fillList("topRii", data.top_researchers.by_rii);

    // Institutions (country only)
    const block = document.getElementById("institutionsBlock");
    if (data.top_institutions) {
      block.style.display = "block";
      fillList("instH", data.top_institutions.by_h_index, true);
      fillList("instRii", data.top_institutions.by_rii, true);
    } else {
      block.style.display = "none";
    }

  } catch (err) {
    alert("Failed to fetch analytics");
    console.error(err);
  }
}

// ------------------------------------
// Helpers
// ------------------------------------
function fillList(id, items, isInstitution = false) {
  const ul = document.getElementById(id);
  ul.innerHTML = "";

  if (!items || items.length === 0) {
    ul.innerHTML = "<li>No data</li>";
    return;
  }

  items.forEach(item => {
    const li = document.createElement("li");

    li.textContent = isInstitution
      ? `${item.name} — H: ${item.average_h_index}, RII: ${item.average_rii}`
      : `${item.name} — H: ${item.h_index}, RII: ${item.rii}
         | Pub: ${item.total_publications}, Cit: ${item.total_citations}`;

    ul.appendChild(li);
  });
}

// ------------------------------------
// Events
// ------------------------------------
document.getElementById("applyBtn").addEventListener("click", applyFilters);
