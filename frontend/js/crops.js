import { $, setHTML, escapeHtml, API_BASE, toast } from './config.js';

// ============================
// Crops
// ============================
export async function fetchCrops() {
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

export async function addCrop() {
    const nameInput = $("#crop-name");
    const plotInput = $("#crop-plot");
    const crop = (nameInput?.value || "").trim();
    const plot = (plotInput?.value || "").trim();

    if (!crop || !plot) return toast("Enter crop & plot");
    try {
        await fetch(`${API_BASE}/crops/add`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ crop, plot }) });
        toast("Crop added");
        if (nameInput) nameInput.value = "";
        if (plotInput) plotInput.value = "";
        fetchCrops();
    } catch { toast("Failed to add crop"); }
}

export async function advanceStage(index) {
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

export async function deleteCrop(index) {
    try {
        await fetch(`${API_BASE}/crops/delete`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ index }) });
        toast("Crop deleted"); fetchCrops();
    } catch (e) { toast(`Delete failed: ${e.message || e}`); }
}

// Expose to window for inline handlers
window.addCrop = addCrop;
window.advanceStage = advanceStage;
window.deleteCrop = deleteCrop;
