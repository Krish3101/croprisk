// ============================
// Config & Helpers
// ============================
const API_BASE = "http://127.0.0.1:9000";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
const setHTML = (el, html) => el && (el.innerHTML = html);
const escapeHtml = (s) =>
  String(s ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

const cache = {
  get: (k, fallback = null) => { try { return JSON.parse(localStorage.getItem(k)) ?? fallback; } catch { return fallback; } },
  set: (k, v) => localStorage.setItem(k, JSON.stringify(v)),
  del: (k) => localStorage.removeItem(k)
};

let toastTimer;
function toast(msg) {
  const el = $("#toast"), span = $("#toast-message");
  if (!el || !span) return;
  span.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
}

function withSpinner(btn, fn) {
  if (!btn) return fn();
  if (btn.classList.contains("loading")) return;
  btn.classList.add("loading");
  btn.disabled = true;
  const p = Promise.resolve().then(fn);
  p.finally(() => { btn.classList.remove("loading"); btn.disabled = false; });
  return p;
}

function cacheWithTTL(key, ttlMs, fetcher) {
  const now = Date.now();
  const cached = cache.get(key);
  if (cached && cached.t && (now - cached.t) < ttlMs) {
    return Promise.resolve(cached.v);
  }
  return fetcher().then(v => {
    cache.set(key, { t: now, v });
    return v;
  });
}

// ============================
// Theme (Dark/Light/Auto)
// ============================
function applyTheme(mode) {
  const root = document.documentElement;
  const label = $(".theme-label");
  if (mode === "dark") {
    root.classList.add("dark");
    label.textContent = "Dark";
  } else if (mode === "light") {
    root.classList.remove("dark");
    label.textContent = "Light";
  } else {
    // Auto: follow system
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.classList.toggle("dark", !!prefersDark);
    label.textContent = "Auto";
  }
}
function setupTheme() {
  const saved = cache.get("theme:mode", "auto");
  applyTheme(saved);
  $("#theme-toggle")?.addEventListener("click", () => {
    const cur = cache.get("theme:mode", "auto");
    const next = cur === "auto" ? "dark" : cur === "dark" ? "light" : "auto";
    cache.set("theme:mode", next);
    applyTheme(next);
  });
  // react to system changes if auto
  window.matchMedia?.("(prefers-color-scheme: dark)").addEventListener?.("change", () => {
    if (cache.get("theme:mode", "auto") === "auto") applyTheme("auto");
  });
}

// ============================
// Sidebar (desktop) collapse
// ============================
function applySidebarState() {
  const collapsed = !!cache.get("ui:sidebarCollapsed", false);
  const sidebar = $("#sidebar");
  const mainWrap = $(".main-wrap");
  if (!sidebar) return;
  sidebar.classList.toggle("collapsed", collapsed);
  if (mainWrap) {
    mainWrap.classList.toggle("sidebar-collapsed", collapsed);
  }
}
function setupSidebar() {
  const btn = $("#sidebar-toggle");
  applySidebarState();
  btn?.addEventListener("click", () => {
    const cur = !!cache.get("ui:sidebarCollapsed", false);
    cache.set("ui:sidebarCollapsed", !cur);
    applySidebarState();
  });
  window.addEventListener("resize", applySidebarState);
}

// ============================
// Navigation
// ============================
function setupNavigation() {
  const navItems = $$(".nav-item");
  const pages = $$(".page");
  const fabs = [$("#fab-add-crop"), $("#fab-add-tx")].filter(Boolean);
  const chatBtn = $("#ai-btn");

  function showPage(pageId) {
    // activate both side & bottom nav entries
    navItems.forEach(i => i.classList.toggle("active", i.getAttribute("data-page") === pageId));
    // show page
    pages.forEach(p => p.classList.toggle("hidden", p.id !== pageId));
    // FABs
    fabs.forEach(f => f.style.display = "none");
    if (pageId === "crops") {
    const cropFab = $("#fab-add-crop");
    if (cropFab) cropFab.style.display = "block";
    if (chatBtn) chatBtn.style.bottom = window.innerWidth >= 768 ? "90px" : "156px";
    } else if (pageId === "finances") {
    const txFab = $("#fab-add-tx");
    if (txFab) txFab.style.display = "block";
    if (chatBtn) chatBtn.style.bottom = window.innerWidth >= 768 ? "90px" : "156px";
    } else {
    if (chatBtn) chatBtn.style.bottom = window.innerWidth >= 768 ? "24px" : "90px";
    }
    // lazy load data
    if (pageId === "crops") fetchCrops();
    if (pageId === "finances") { loadSummary(); loadTxList(); drawFinanceChart(); }
  }

  navItems.forEach(item => item.addEventListener("click", () => showPage(item.getAttribute("data-page"))));
  // default
  showPage("dashboard");
}

// ============================
// Dashboard: Weather & Price
// ============================
function weatherSkeleton() {
  setHTML($("#weather-result"), `
    <div class="skel h-5 w-3/4"></div>
    <div class="skel h-4 w-1/2 mt"></div>
  `);
}
function priceSkeleton() {
  setHTML($("#price-result"), `
    <div class="skel h-5 w-3/4"></div>
    <div class="skel h-4 w-1/2 mt"></div>
  `);
}

async function loadWeather(btn) {
  return withSpinner(btn, async () => {
    const city = ($("#weather-city")?.value || "").trim();
    if (!city) return toast("Enter a city");
    weatherSkeleton();

    const key = `weather:${city.toLowerCase()}`;
    const ttl = 6 * 60 * 60 * 1000;
    try {
      const data = await cacheWithTTL(key, ttl, async () => {
        const r = await fetch(`${API_BASE}/weather?city=${encodeURIComponent(city)}`);
        const d = await r.json();
        if (d.error) throw new Error(d.error);
        return d;
      });
      setHTML($("#weather-result"), `
        <div class="space-y-1">
          <p><b>City:</b> ${escapeHtml(data.city)}</p>
          <p><b>Temperature:</b> ${data.temp}°C</p>
          <p><b>Condition:</b> ${escapeHtml(data.weather)}</p>
          <p><b>Humidity:</b> ${data.humidity}%</p>
        </div>
      `);
      cache.set("weather:last", data);
      updateRecommendation();
    } catch (e) {
      const last = cache.get("weather:last");
      if (last) {
        setHTML($("#weather-result"), `
          <div class="p-3 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg">
            <p class="font-semibold text-yellow-800 dark:text-yellow-200">Showing last saved weather.</p>
            <p class="text-sm mt-1">${escapeHtml(last.city)} — ${last.temp}°C, ${escapeHtml(last.weather)}</p>
          </div>
        `);
      } else {
        setHTML($("#weather-result"), `<div class="text-red-600">Error: ${escapeHtml(e.message)}</div>`);
      }
    }
  });
}

async function loadPrice(btn) {
  return withSpinner(btn, async () => {
    const crop = ($("#price-crop")?.value || "").trim();
    if (!crop) return toast("Enter a crop");
    priceSkeleton();

    const key = `price:${crop.toLowerCase()}`;
    const ttl = 6 * 60 * 60 * 1000;
    try {
      const data = await cacheWithTTL(key, ttl, async () => {
        const r = await fetch(`${API_BASE}/price?crop=${encodeURIComponent(crop)}`);
        const d = await r.json();
        if (d.error) throw new Error(d.error);
        return d;
      });
      setHTML($("#price-result"), `
        <div class="space-y-1">
          <p><b>Crop:</b> ${escapeHtml(data.crop)}</p>
          ${data.modal_price ? `<p><b>Modal:</b> ₹${escapeHtml(data.modal_price)}</p>` : ""}
          ${data.min_price ? `<p><b>Min:</b> ₹${escapeHtml(data.min_price)}</p>` : ""}
          ${data.max_price ? `<p><b>Max:</b> ₹${escapeHtml(data.max_price)}</p>` : ""}
          ${data.market ? `<p><b>Market:</b> ${escapeHtml(data.market)}</p>` : ""}
        </div>
      `);
      cache.set("price:last", data);
      updateRecommendation();
    } catch (e) {
      const last = cache.get("price:last");
      if (last) {
        setHTML($("#price-result"), `
          <div class="p-3 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg">
            <p class="font-semibold text-yellow-800 dark:text-yellow-200">Showing last saved price.</p>
            <p class="text-sm mt-1">${escapeHtml(last.crop)} — ₹${escapeHtml(last.modal_price ?? "-")}</p>
          </div>
        `);
      } else {
        setHTML($("#price-result"), `<div class="text-red-600">Error: ${escapeHtml(e.message)}</div>`);
      }
    }
  });
}

function updateSnapshot() {
  fetch(`${API_BASE}/expense/summary`).then(r => r.json()).then(s => {
    const income = +s.total_income || 0;
    const expense = +s.total_expense || 0;
    const profit = +s.profit || 0;
    setHTML($("#snapshot"), `
      <div class="bg-green-100 dark:bg-green-900/30 p-3 rounded text-center">
        <p class="text-green-700 dark:text-green-200 text-sm">Income</p>
        <p class="text-xl font-bold text-green-800 dark:text-green-100">₹${income.toLocaleString("en-IN")}</p>
      </div>
      <div class="bg-red-100 dark:bg-red-900/30 p-3 rounded text-center">
        <p class="text-red-700 dark:text-red-200 text-sm">Expenses</p>
        <p class="text-xl font-bold text-red-800 dark:text-red-100">₹${expense.toLocaleString("en-IN")}</p>
      </div>
      <div class="col-span-2 bg-blue-100 dark:bg-blue-900/30 p-3 rounded text-center">
        <p class="text-blue-700 dark:text-blue-200 text-sm">Net Profit</p>
        <p class="text-2xl font-bold text-blue-800 dark:text-blue-100">₹${profit.toLocaleString("en-IN")}</p>
      </div>
    `);
  }).catch(() => setHTML($("#snapshot"), `<div class="text-gray-500">No transactions yet.</div>`));
}

function updateRecommendation() {
  const w = cache.get("weather:last");
  const p = cache.get("price:last");
  let tip = "Enter a city or crop to get a tailored recommendation.";
  if (w?.weather?.toLowerCase().includes("rain")) tip = "🌧️ Rain expected — delay irrigation and ensure drainage.";
  if (p?.modal_price && Number(p.modal_price) > 4000) tip = "💹 Good prices — plan harvest or stagger sales.";
  if (w && p) tip += " (based on your latest weather & price)";
  setHTML($("#rec-box"), tip);
}

$("#save-city")?.addEventListener("click", () => {
  const city = ($("#weather-city")?.value || "").trim();
  if (!city) return toast("Enter a city first");
  cache.set("default:city", city); toast("City saved");
});
$("#save-crop")?.addEventListener("click", () => {
  const crop = ($("#price-crop")?.value || "").trim();
  if (!crop) return toast("Enter a crop first");
  cache.set("default:crop", crop); toast("Crop saved");
});

// ============================
// Crops
// ============================
async function fetchCrops() {
  const listEl = $("#crop-list");
  const emptyEl = $(".empty-state", $("#crops"));
  if (!listEl) return;
  listEl.innerHTML = `<div class="skel h-6"></div><div class="skel h-6 mt"></div>`;
  if (emptyEl) emptyEl.style.display = "none";

  try {
    const r = await fetch(`${API_BASE}/crops`);
    const list = await r.json();
    if (!Array.isArray(list) || list.length === 0) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";
    setHTML(listEl, list.map((c, i) => `
      <div class="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <h3 class="font-bold">${escapeHtml(c.crop)} (${escapeHtml(c.plot)})</h3>
          <span class="text-xs bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200 px-2 py-1 rounded">
            ${escapeHtml(c.stage || "Sown")}
          </span>
        </div>
        <p class="text-sm text-slate-600 dark:text-slate-300 mt-1">Sown on: ${escapeHtml(c.sown_date || "—")}</p>
        <div class="flex gap-2 mt-3">
          <button class="btn-ghost" onclick="advanceStage(${i})">Next Stage</button>
          <button class="btn-ghost" style="color:#dc2626;background:#fee2e2" onclick="deleteCrop(${i})">Delete</button>
        </div>
      </div>
    `).join(""));
  } catch {
    listEl.innerHTML = `<div class="text-red-600">Failed to load crops</div>`;
    emptyEl.style.display = "none";
  }
}

async function addCrop() {
  const crop = prompt("Crop name (e.g., Tomato):");
  const plot = prompt("Plot name (e.g., Field A):");
  if (!crop || !plot) return toast("Enter crop & plot");
  try {
    await fetch(`${API_BASE}/crops/add`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ crop, plot }) });
    toast("Crop added"); fetchCrops();
  } catch { toast("Failed to add crop"); }
}

async function advanceStage(index) {
  try {
    const listRes = await fetch(`${API_BASE}/crops`);
    const list = await listRes.json();
    if (!Array.isArray(list) || !list[index]) return;
    const stages = ["Sown", "Vegetative", "Flowering", "Harvest"];
    const cur = list[index].stage || "Sown";
    const i = stages.indexOf(cur);
    list[index].stage = stages[(i + 1) % stages.length];
    await fetch(`${API_BASE}/crops/delete`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ index }) });
    await fetch(`${API_BASE}/crops/add`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(list[index]) });
    fetchCrops();
  } catch (e) { toast(`Advance failed: ${e.message || e}`); }
}
async function deleteCrop(index) {
  try {
    await fetch(`${API_BASE}/crops/delete`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ index }) });
    toast("Crop deleted"); fetchCrops();
  } catch (e) { toast(`Delete failed: ${e.message || e}`); }
}
window.advanceStage = advanceStage; // temporary for inline handlers
window.deleteCrop = deleteCrop;

// ============================
// Finances
// ============================
async function addTransaction(btn) {
  return withSpinner(btn, async () => {
    const title = ($("#tx-title")?.value || "").trim();
    const amount = parseFloat($("#tx-amount")?.value);
    const type = $("#tx-type")?.value || "income";
    const date = $("#tx-date")?.value;
    if (!title || !amount || !date) return toast("Fill all fields");
    if (amount <= 0) return toast("Amount must be positive");

    try {
      const url = `${API_BASE}/expense/add?title=${encodeURIComponent(title)}&amount=${amount}&type=${type}&date=${date}`;
      const r = await fetch(url);
      const d = await r.json();
      if (d?.error) throw new Error(d.error);

      $("#tx-title").value = ""; $("#tx-amount").value = ""; $("#tx-date").value = "";
      toast("Transaction added");
      loadSummary(); loadTxList(); drawFinanceChart(); updateSnapshot();
    } catch (e) {
      toast(`Failed: ${e.message || e}`);
    }
  });
}

async function loadSummary() {
  try {
    const r = await fetch(`${API_BASE}/expense/summary`);
    const s = await r.json();
    const income = +s.total_income || 0, expense = +s.total_expense || 0, profit = +s.profit || 0;
    setHTML($("#summary"), `
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-green-100 dark:bg-green-900/30 p-3 rounded text-center">
          <p class="text-green-700 dark:text-green-200 text-sm">Income</p>
          <p class="text-xl font-bold text-green-800 dark:text-green-100">₹${income.toLocaleString("en-IN")}</p>
        </div>
        <div class="bg-red-100 dark:bg-red-900/30 p-3 rounded text-center">
          <p class="text-red-700 dark:text-red-200 text-sm">Expenses</p>
          <p class="text-xl font-bold text-red-800 dark:text-red-100">₹${expense.toLocaleString("en-IN")}</p>
        </div>
        <div class="col-span-2 bg-blue-100 dark:bg-blue-900/30 p-3 rounded text-center">
          <p class="text-blue-700 dark:text-blue-200 text-sm">Net Profit</p>
          <p class="text-2xl font-bold text-blue-800 dark:text-blue-100">₹${profit.toLocaleString("en-IN")}</p>
        </div>
      </div>
    `);
  } catch {
    setHTML($("#summary"), `<div class="text-red-600">Error loading summary</div>`);
  }
}

async function loadTxList() {
  const listEl = $("#tx-list");
  const emptyEl = $(".empty-state", $("#finances"));
  if (!listEl) return;
  listEl.innerHTML = `<div class="skel h-6"></div><div class="skel h-6 mt"></div>`;
  if (emptyEl) emptyEl.style.display = "none";
  try {
    const r = await fetch(`${API_BASE}/expense/list`);
    const list = await r.json();
    if (!Array.isArray(list) || list.length === 0) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";
    setHTML(listEl, list.slice().reverse().map(tx => `
      <div class="flex justify-between bg-white dark:bg-slate-900 p-3 rounded border border-slate-200 dark:border-slate-700">
        <div>
          <p class="font-semibold">${escapeHtml(tx.title)}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400">${escapeHtml(tx.date)}</p>
        </div>
        <p class="font-bold ${tx.type === "expense" ? "text-red-600" : "text-green-600"}">
          ${tx.type === "expense" ? "-" : "+"} ₹${(+tx.amount).toLocaleString("en-IN")}
        </p>
      </div>
    `).join(""));
  } catch {
    listEl.innerHTML = `<div class="text-red-600">Error loading transactions</div>`;
    emptyEl.style.display = "none";
  }
}

let financeChart = null;
async function drawFinanceChart() {
  const canvas = $("#expenseChart"); if (!canvas) return;
  try {
    const r = await fetch(`${API_BASE}/expense/summary`);
    const s = await r.json();
    const data = [+s.total_income || 0, +s.total_expense || 0];
    if (financeChart) financeChart.destroy();
    financeChart = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: ["Income", "Expenses"],
        datasets: [{
          data, borderWidth: 2, borderColor: "#fff",
          backgroundColor: ["rgba(22,163,74,0.85)","rgba(220,38,38,0.85)"]
        }]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });
  } catch {}
}

// ============================
// Soil
// ============================
function soilSkeleton() {
  setHTML($("#soil-result"), `<div class="skel h-6"></div><div class="skel h-6 mt"></div>`);
}
async function loadSoil(btn) {
  return withSpinner(btn, async () => {
    const field = ($("#soil-field")?.value || "default").trim();
    soilSkeleton();
    try {
      const r = await fetch(`${API_BASE}/soil?field=${encodeURIComponent(field)}`);
      const s = await r.json();
      setHTML($("#soil-result"), `
        <div class="space-y-1">
          ${s.soil_type ? `<p><b>Soil:</b> ${escapeHtml(s.soil_type)}</p>` : ""}
          ${s.ph ? `<p><b>pH:</b> ${escapeHtml(String(s.ph))}</p>` : ""}
          ${s.organic_carbon ? `<p><b>Organic Carbon:</b> ${escapeHtml(String(s.organic_carbon))}</p>` : ""}
          ${s.moisture ? `<p><b>Moisture:</b> ${escapeHtml(String(s.moisture))}</p>` : ""}
          ${s.nitrogen ? `<p><b>Nitrogen:</b> ${escapeHtml(s.nitrogen)}</p>` : ""}
          ${s.phosphorus ? `<p><b>Phosphorus:</b> ${escapeHtml(s.phosphorus)}</p>` : ""}
          ${s.potassium ? `<p><b>Potassium:</b> ${escapeHtml(s.potassium)}</p>` : ""}
          ${s.last_tested ? `<p class="text-xs text-slate-500 dark:text-slate-400">Last tested: ${escapeHtml(s.last_tested)}</p>` : ""}
        </div>
      `);
    } catch {
      setHTML($("#soil-result"), `<div class="text-red-600">Error loading soil</div>`);
    }
  });
}

// ============================
// Chat (with mic)
// ============================
function appendUser(t) {
  const b = $("#chat-body");
  b.insertAdjacentHTML("beforeend",
    `<div class="flex justify-end mb-2">
      <div class="bg-green-600 text-white p-3 rounded-xl max-w-xs">${escapeHtml(t)}</div>
    </div>`);
  b.scrollTop = b.scrollHeight;
}
function appendAI(t) {
  const b = $("#chat-body");
  b.insertAdjacentHTML("beforeend",
    `<div class="flex mb-2">
      <div class="bg-gray-200 dark:bg-slate-800 text-gray-800 dark:text-slate-100 p-3 rounded-xl max-w-xs whitespace-pre-line">${escapeHtml(t)}</div>
    </div>`);
  b.scrollTop = b.scrollHeight;
}
function showTyping() {
  const b = $("#chat-body");
  if (!$("#typing")) {
    b.insertAdjacentHTML("beforeend",
      `<div id="typing" class="flex mb-2">
        <div class="bg-gray-200 dark:bg-slate-800 text-gray-800 dark:text-slate-100 p-3 rounded-xl max-w-xs">
          <span class="inline-block animate-pulse">…</span>
        </div>
      </div>`);
  }
  b.scrollTop = b.scrollHeight;
}
function hideTyping() { $("#typing")?.remove(); }

async function sendMessage(btn) {
  const inp = $("#chat-msg");
  const text = (inp?.value || "").trim();
  if (!text) return;
  appendUser(text);
  inp.value = "";

  await withSpinner(btn, async () => {
    try {
      showTyping();
      const r = await fetch(`${API_BASE}/chatbot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });
      const d = await r.json();
      hideTyping();
      appendAI(d.answer || JSON.stringify(d, null, 2));
    } catch {
      hideTyping();
      appendAI("Server error. Try again.");
    }
  });
}

// Voice input (mic)
function setupMic() {
  const btn = $("#chat-mic");
  if (!btn) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    btn.disabled = true; btn.title = "Voice not supported in this browser";
    return;
  }
  let rec = null, active = false;
  btn.addEventListener("click", () => {
    if (!active) {
      rec = new SR();
      rec.lang = "en-IN"; // good default; user can still speak Hindi
      rec.interimResults = false; rec.maxAlternatives = 1;
      rec.onresult = (e) => {
        const text = e.results?.[0]?.[0]?.transcript;
        if (text) { $("#chat-msg").value = text; toast("Voice captured"); }
      };
      rec.onerror = () => toast("Mic error");
      rec.onend = () => { active = false; btn.classList.remove("loading"); };
      active = true; btn.classList.add("loading"); rec.start();
    } else {
      try { rec?.stop(); } catch {}
      active = false; btn.classList.remove("loading");
    }
  });
}

// ============================
// Init
// ============================
document.addEventListener("DOMContentLoaded", () => {
  setupTheme();
  setupSidebar();
  setupNavigation();

  // Prefill defaults
    const defCity = cache.get("default:city");
    const weatherInput = $("#weather-city");
    if (defCity && weatherInput) weatherInput.value = defCity;
    const defCrop = cache.get("default:crop");
    const priceInput = $("#price-crop");
    if (defCrop && priceInput) priceInput.value = defCrop;

  // Initial dashboard
  updateSnapshot();
  const lastW = cache.get("weather:last");
  if (lastW) setHTML($("#weather-result"),
    `<div class="space-y-1"><p><b>${escapeHtml(lastW.city)}</b>: ${lastW.temp}°C, ${escapeHtml(lastW.weather)}</p><p class="text-xs">Last cached</p></div>`);
  const lastP = cache.get("price:last");
  if (lastP) setHTML($("#price-result"),
    `<div class="space-y-1"><p><b>${escapeHtml(lastP.crop)}</b>: ₹${escapeHtml(lastP.modal_price ?? "-")}</p><p class="text-xs">Last cached</p></div>`);
  updateRecommendation();

  // Buttons + spinners
  $("#btn-weather")?.addEventListener("click", (e) => loadWeather(e.currentTarget));
  $("#btn-price")?.addEventListener("click", (e) => loadPrice(e.currentTarget));
  $("#btn-soil")?.addEventListener("click", (e) => loadSoil(e.currentTarget));
  $("#btn-add-tx")?.addEventListener("click", (e) => addTransaction(e.currentTarget));
  $("#btn-send-chat")?.addEventListener("click", (e) => sendMessage(e.currentTarget));

  // FABs
  $("#fab-add-crop")?.addEventListener("click", addCrop);
  $("#fab-add-tx")?.addEventListener("click", () => {
    $(".card:nth-child(2)", $("#finances"))?.scrollIntoView({ behavior: "smooth" });
    $("#tx-title")?.focus();
  });

  // Chat modal open/close
  const overlay = $("#chat-overlay"), modal = $("#chat-modal");
  const openChat = () => { overlay.style.display = "block"; modal.style.display = "flex";
    if (!$("#chat-body").children.length) appendAI("Hello! Ask about weather, prices, crops, soil, or finances."); };
  const closeChat = () => { overlay.style.display = "none"; modal.style.display = "none"; };
  $("#ai-btn")?.addEventListener("click", openChat);
  $("#chat-close")?.addEventListener("click", closeChat);
  overlay?.addEventListener("click", closeChat);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeChat(); });

  // Enter to send
  $("#chat-msg")?.addEventListener("keypress", (e) => { if (e.key === "Enter") $("#btn-send-chat")?.click(); });

  // Mic
  setupMic();

  // Refresh dashboard
  $("#refresh-btn")?.addEventListener("click", () => {
    if (!$("#dashboard")?.classList.contains("hidden")) {
      const bw = $("#btn-weather"), bp = $("#btn-price");
      if ($("#weather-city").value) loadWeather(bw);
      if ($("#price-crop").value) loadPrice(bp);
      updateSnapshot(); toast("Dashboard refreshed");
    }
  });

    // Handle window resize for FAB positioning
    window.addEventListener("resize", () => {
      const activePage = $(".page:not(.hidden)");
      if (activePage) {
        const pageId = activePage.id;
        const chatBtn = $("#ai-btn");
        if (!chatBtn) return;
        const isDesktop = window.innerWidth >= 768;
        if (pageId === "crops" || pageId === "finances") {
          chatBtn.style.bottom = isDesktop ? "90px" : "156px";
        } else {
          chatBtn.style.bottom = isDesktop ? "24px" : "90px";
        }
      }
    });
});
