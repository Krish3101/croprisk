const BASE = "http://127.0.0.1:8000";

const show = (id, data) => {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify(data, null, 2);
  }
};

const showLoading = (id) => {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = "Loading...";
  }
};

const showError = (id, error) => {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify({ error: error.message || error }, null, 2);
  }
};

async function fetchPrice() {
  const crop = document.getElementById("crop").value.trim();
  const market = document.getElementById("market").value.trim();
  if (!crop) return show("priceOut", { error: "Enter a crop" });

  const url = new URL(`${BASE}/api/price/${encodeURIComponent(crop)}`);
  if (market) url.searchParams.set("market", market);

  showLoading("priceOut");
  try {
    const r = await fetch(url);
    const j = await r.json();
    if (!r.ok) throw j;
    show("priceOut", j);
  } catch (e) {
    showError("priceOut", e);
  }
}

async function fetchWeather() {
  const loc = document.getElementById("location").value.trim();
  if (!loc) return show("weatherOut", { error: "Enter a location" });

  showLoading("weatherOut");
  try {
    const r = await fetch(`${BASE}/api/weather/${encodeURIComponent(loc)}`);
    const j = await r.json();
    if (!r.ok) throw j;
    show("weatherOut", j);
  } catch (e) {
    showError("weatherOut", e);
  }
}

async function fetchFarmer() {
  const id = document.getElementById("farmerId").value.trim();
  if (!id) return show("farmerOut", { error: "Enter farmer ID" });

  showLoading("farmerOut");
  try {
    const r = await fetch(`${BASE}/api/farmer/${id}`);
    const j = await r.json();
    if (!r.ok) throw j;
    show("farmerOut", j);
  } catch (e) {
    showError("farmerOut", e);
  }
}

async function listAllFarmers() {
  showLoading("farmerOut");
  try {
    const r = await fetch(`${BASE}/api/farmers`);
    const j = await r.json();
    if (!r.ok) throw j;
    show("farmerOut", j);
  } catch (e) {
    showError("farmerOut", e);
  }
}

async function createFarmer() {
  const body = {
    name: document.getElementById("fname").value.trim(),
    village: document.getElementById("fvillage").value.trim(),
    crop: document.getElementById("fcrop").value.trim(),
  };
  if (!body.name || !body.village || !body.crop)
    return show("farmerCrudOut", { error: "Fill all fields" });

  showLoading("farmerCrudOut");
  try {
    const r = await fetch(`${BASE}/api/farmer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await r.json();
    if (!r.ok) throw j;
    show("farmerCrudOut", j);
  } catch (e) {
    showError("farmerCrudOut", e);
  }
}

async function updateFarmer() {
  const id = document.getElementById("farmerId").value.trim();
  if (!id) return show("farmerCrudOut", { error: "Enter farmer ID" });

  const body = {
    name: document.getElementById("fname").value.trim(),
    village: document.getElementById("fvillage").value.trim(),
    crop: document.getElementById("fcrop").value.trim(),
  };
  if (!body.name || !body.village || !body.crop)
    return show("farmerCrudOut", { error: "Fill all fields" });

  showLoading("farmerCrudOut");
  try {
    const r = await fetch(`${BASE}/api/farmer/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await r.json();
    if (!r.ok) throw j;
    show("farmerCrudOut", j);
  } catch (e) {
    showError("farmerCrudOut", e);
  }
}

async function deleteFarmer() {
  const id = document.getElementById("farmerId").value.trim();
  if (!id) return show("farmerCrudOut", { error: "Enter farmer ID" });

  showLoading("farmerCrudOut");
  try {
    const r = await fetch(`${BASE}/api/farmer/${id}`, { method: "DELETE" });
    const j = await r.json();
    if (!r.ok) throw j;
    show("farmerCrudOut", j);
  } catch (e) {
    showError("farmerCrudOut", e);
  }
}
