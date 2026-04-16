// ============================
// Config & Helpers
// ============================
export const API_BASE = "http://127.0.0.1:9000";

export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
export const setHTML = (el, html) => el && (el.innerHTML = html);
export const escapeHtml = (s) =>
    String(s ?? "").replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));

export const cache = {
    get: (k, fallback = null) => { try { return JSON.parse(localStorage.getItem(k)) ?? fallback; } catch { return fallback; } },
    set: (k, v) => localStorage.setItem(k, JSON.stringify(v)),
    del: (k) => localStorage.removeItem(k)
};

let toastTimer;
export function toast(msg) {
    const el = $("#toast"), span = $("#toast-message");
    if (!el || !span) return;
    span.textContent = msg;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
}

export function withSpinner(btn, fn) {
    if (!btn) return fn();
    if (btn.classList.contains("loading")) return;
    btn.classList.add("loading");
    btn.disabled = true;
    const p = Promise.resolve().then(fn);
    p.finally(() => { btn.classList.remove("loading"); btn.disabled = false; });
    return p;
}

export function cacheWithTTL(key, ttlMs, fetcher) {
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
