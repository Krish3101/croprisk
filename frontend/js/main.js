import { $, cache, setHTML, escapeHtml, toast } from './config.js';
import { setupTheme, setupSidebar, setupNavigation } from './ui.js';
import { loadWeather, loadPrice, updateSnapshot, updateRecommendation } from './dashboard.js';
import { addCrop } from './crops.js';
import { addTransaction } from './finances.js';
import { loadSoil } from './soil.js';
import { setupChat } from './chat.js';

// ============================
// Init
// ============================
document.addEventListener("DOMContentLoaded", () => {
    setupTheme();
    setupSidebar();
    setupNavigation();
    setupChat();

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

    // Save defaults
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
});
