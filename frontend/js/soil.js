import { $, setHTML, escapeHtml, API_BASE, withSpinner } from './config.js';

// ============================
// Soil
// ============================
function soilSkeleton() {
    setHTML($("#soil-result"), `<div class="skel h-6"></div><div class="skel h-6 mt"></div>`);
}

export async function loadSoil(btn) {
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
