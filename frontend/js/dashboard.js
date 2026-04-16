import { $, setHTML, escapeHtml, cache, cacheWithTTL, API_BASE, toast, withSpinner } from './config.js';

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

export async function loadWeather(btn) {
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

            // Also update dashboard weather if on dashboard
            const dashWeather = $("#dash-weather");
            if (dashWeather) {
                setHTML(dashWeather, `${data.temp}°C, ${escapeHtml(data.weather)}`);
            }

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

export async function loadPrice(btn) {
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

            // Also update dashboard price if on dashboard
            const dashPrice = $("#dash-price");
            if (dashPrice) {
                setHTML(dashPrice, `₹${escapeHtml(data.modal_price ?? "-")} (${escapeHtml(data.crop)})`);
            }

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

export function updateSnapshot() {
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

export function updateRecommendation() {
    const w = cache.get("weather:last");
    const p = cache.get("price:last");
    let tip = "Enter a city or crop to get a tailored recommendation.";
    if (w?.weather?.toLowerCase().includes("rain")) tip = "🌧️ Rain expected — delay irrigation and ensure drainage.";
    if (p?.modal_price && Number(p.modal_price) > 4000) tip = "💹 Good prices — plan harvest or stagger sales.";
    if (w && p) tip += " (based on your latest weather & price)";
    setHTML($("#rec-box"), tip);
}
