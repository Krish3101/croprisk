import { $, escapeHtml, API_BASE, toast, withSpinner } from './config.js';

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

export async function sendMessage(btn) {
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
export function setupMic() {
    const btn = $("#chat-mic");
    if (!btn) return;
    // @ts-ignore
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
            try { rec?.stop(); } catch { }
            active = false; btn.classList.remove("loading");
        }
    });
}

export function setupChat() {
    // Chat modal open/close
    const overlay = $("#chat-overlay"), modal = $("#chat-modal");
    const openChat = () => {
        overlay.style.display = "block";
        modal.style.display = "flex";
        if (!$("#chat-body").children.length) appendAI("Hello! Ask about weather, prices, crops, soil, or finances.");
    };
    const closeChat = () => { overlay.style.display = "none"; modal.style.display = "none"; };

    $("#ai-btn")?.addEventListener("click", openChat);
    $("#chat-close")?.addEventListener("click", closeChat);
    overlay?.addEventListener("click", closeChat);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeChat(); });

    // Enter to send
    $("#chat-msg")?.addEventListener("keypress", (e) => { if (e.key === "Enter") $("#btn-send-chat")?.click(); });
    $("#btn-send-chat")?.addEventListener("click", (e) => sendMessage(e.currentTarget));

    setupMic();
}
