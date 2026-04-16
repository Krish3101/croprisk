import { $, $$, cache } from './config.js';
import { fetchCrops } from './crops.js';
import { loadSummary, loadTxList, drawFinanceChart } from './finances.js';

// ============================
// Theme (Dark/Light/Auto)
// ============================
export function applyTheme(mode) {
    const root = document.documentElement;
    const label = $(".theme-label"); // Note: theme-label might not exist in current HTML, keeping for safety
    if (mode === "dark") {
        root.classList.add("dark");
        if (label) label.textContent = "Dark";
    } else if (mode === "light") {
        root.classList.remove("dark");
        if (label) label.textContent = "Light";
    } else {
        // Auto: follow system
        const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        root.classList.toggle("dark", !!prefersDark);
        if (label) label.textContent = "Auto";
    }
}

export function setupTheme() {
    const saved = cache.get("theme:mode", "auto");
    applyTheme(saved);

    // react to system changes if auto
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
            if (cache.get("theme:mode", "auto") === "auto") applyTheme("auto");
        });
    }
}

// ============================
// Sidebar (desktop) collapse
// ============================
export function applySidebarState() {
    const collapsed = !!cache.get("ui:sidebarCollapsed", false);
    const sidebar = $("#sidebar");
    const mainWrap = $(".main-wrap");
    if (!sidebar) return;
    sidebar.classList.toggle("collapsed", collapsed);
    if (mainWrap) {
        mainWrap.classList.toggle("sidebar-collapsed", collapsed);
    }
}

export function toggleSidebar() {
    const sidebar = $("#sidebar");
    if (sidebar) {
        // For mobile, we might want a different behavior, but reusing the collapse logic for now
        // or toggling a specific mobile class. 
        // The CSS uses .mobile-nav-toggle to show/hide sidebar on mobile usually via a class on body or sidebar.
        // Checking style.css: .sidebar-nav transform is used on mobile.
        sidebar.classList.toggle("active");
    }
}

export function setupSidebar() {
    applySidebarState();
    window.addEventListener("resize", applySidebarState);
}

// ============================
// Navigation
// ============================
export function showPage(pageId) {
    const navItems = $$(".nav-item");
    const pages = $$(".page");
    const chatBtn = $("#ai-btn");

    // activate both side & bottom nav entries
    navItems.forEach(i => i.classList.toggle("active", i.getAttribute("data-page") === pageId));
    // show page
    pages.forEach(p => p.classList.toggle("hidden", p.id !== pageId));

    // Adjust chat button position based on page
    if (chatBtn) {
        const isDesktop = window.innerWidth >= 768;
        if (pageId === "crops" || pageId === "finances") {
            chatBtn.style.bottom = isDesktop ? "90px" : "156px";
        } else {
            chatBtn.style.bottom = isDesktop ? "32px" : "80px";
        }
    }

    // lazy load data
    if (pageId === "crops") fetchCrops();
    if (pageId === "finances") { loadSummary(); loadTxList(); drawFinanceChart(); }
}

export function setupNavigation() {
    const navItems = $$(".nav-item");
    navItems.forEach(item => item.addEventListener("click", () => showPage(item.getAttribute("data-page"))));

    // Expose to window for HTML onclick attributes
    window.showPage = showPage;
    window.toggleSidebar = toggleSidebar;

    // default
    showPage("dashboard");
}
