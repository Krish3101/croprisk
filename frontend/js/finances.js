import { $, setHTML, escapeHtml, API_BASE, toast, withSpinner } from './config.js';
import { updateSnapshot } from './dashboard.js';

// ============================
// Finances
// ============================
export async function addTransaction(btn) {
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

export async function loadSummary() {
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

export async function loadTxList() {
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
export async function drawFinanceChart() {
    const canvas = $("#expenseChart"); if (!canvas) return;
    try {
        const r = await fetch(`${API_BASE}/expense/summary`);
        const s = await r.json();
        const data = [+s.total_income || 0, +s.total_expense || 0];
        if (financeChart) financeChart.destroy();
        // @ts-ignore
        financeChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: ["Income", "Expenses"],
                datasets: [{
                    data, borderWidth: 2, borderColor: "#fff",
                    backgroundColor: ["rgba(22,163,74,0.85)", "rgba(220,38,38,0.85)"]
                }]
            },
            options: { responsive: true, plugins: { legend: { position: "bottom" } } }
        });
    } catch { }
}
