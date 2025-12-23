const API = "http://127.0.0.1:5000/api";

const input = document.getElementById("fieldInput");
const suggestions = document.getElementById("suggestions");

// -----------------------------
// Field autocomplete
// -----------------------------
input.addEventListener("input", async () => {
  const q = input.value.trim();

  if (!q) {
    suggestions.innerHTML = "";
    return;
  }

  const res = await fetch(`${API}/fields/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();

  suggestions.innerHTML = data
    .map((f) => `<div onclick="selectField('${f}')">${f}</div>`)
    .join("");
});

// -----------------------------
// When field is selected
// -----------------------------
async function selectField(field) {
  input.value = field;
  suggestions.innerHTML = "";

  // -------- Top researchers (field overview)
  const res = await fetch(
    `${API}/field/overview?field=${encodeURIComponent(field)}`
  );
  const data = await res.json();

  document.getElementById("byH").innerHTML = data.by_h_index
    .map(
      (r) => `
      <div class="researcher">
        <strong>${r.full_name}</strong><br>
        H-index: ${r.h_index}
      </div>
    `
    )
    .join("");

  document.getElementById("byRii").innerHTML = data.by_rii
    .map(
      (r) => `
      <div class="researcher">
        <strong>${r.full_name}</strong><br>
        RII: ${r.rii}
      </div>
    `
    )
    .join("");

  // -------- Country contribution
  const cres = await fetch(
    `${API}/field/countries?field=${encodeURIComponent(field)}`
  );
  const countries = await cres.json();

  document.getElementById("countries").innerHTML = countries
    .map(
      (c) => `
      <div class="country clickable"
           onclick="openCountry('${field}', '${c.country}', '${c.country_id}')">
        <div class="country-header">
          <span>${c.country}</span>
          <span>${c.percentage}%</span>
        </div>
        <div class="bar">
          <div class="fill" style="width:${c.percentage}%"></div>
        </div>
      </div>
    `
    )
    .join("");
}

// -----------------------------
// Open modal: Field × Country
// -----------------------------
async function openCountry(field, countryName, countryId) {
  const modal = document.getElementById("modal");
  modal.classList.remove("hidden");

  document.getElementById(
    "modalTitle"
  ).innerText = `${countryName} — Top Researchers in ${field}`;

  const res = await fetch(
    `${API}/field/country/researchers?field=${encodeURIComponent(
      field
    )}&country_id=${countryId}`
  );
  const data = await res.json();

  document.getElementById("modalByH").innerHTML = data.by_h_index
    .map(
      (r) => `
      <div class="researcher">
        <strong>${r.full_name}</strong>
        <div>H-index: ${r.h_index}</div>
        <div>Publications: ${r.total_publications}</div>
      </div>
    `
    )
    .join("");

  document.getElementById("modalByRii").innerHTML = data.by_rii
    .map(
      (r) => `
      <div class="researcher">
        <strong>${r.full_name}</strong>
        <div>RII: ${r.rii}</div>
        <div>Citations: ${r.total_citations}</div>
      </div>
    `
    )
    .join("");
}

// -----------------------------
// Close modal
// -----------------------------
function closeModal() {
  document.getElementById("modal").classList.add("hidden");
}
