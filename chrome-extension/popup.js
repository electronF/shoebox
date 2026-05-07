"use strict";

const API  = "http://localhost:8000";
const DASH = "http://localhost:8050";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $  = (id) => document.getElementById(id);
const el = {
  loading:      $("loading"),
  content:      $("content"),
  errorBanner:  $("error-banner"),
  business:     $("kpi-business"),
  collect:      $("kpi-collect"),
  refunds:      $("kpi-refunds"),
  flagged:      $("kpi-flagged"),
  txCount:      $("kpi-tx-count"),
  overdueCount: $("kpi-overdue-count"),
  todoList:     $("todo-list"),
  invoiceList:  $("invoice-list"),
  btnOpen:      $("btn-open"),
  btnRefresh:   $("btn-refresh"),
};

// ── Formatting ────────────────────────────────────────────────────────────────
const fmt = (n) =>
  new Intl.NumberFormat("fr-CA", { style: "currency", currency: "CAD",
    minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(n);

// ── Fetch helpers ─────────────────────────────────────────────────────────────
async function get(path) {
  const res = await fetch(`${API}${path}`, { signal: AbortSignal.timeout(4000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Badge builder ─────────────────────────────────────────────────────────────
function badge(label, cls) {
  const s = document.createElement("span");
  s.className = `badge badge--${cls}`;
  s.textContent = label;
  return s;
}

// ── Render functions ──────────────────────────────────────────────────────────
function renderKpis(summary, invoices) {
  const totalBiz  = summary.total_business  || 0;
  const refunds   = summary.total_refunds   || 0;
  const flagged   = summary.flagged_count   || 0;
  const txCount   = summary.tx_count        || 0;

  const unpaid    = invoices.filter((i) => ["unpaid", "overdue"].includes(i.status));
  const toCollect = unpaid.reduce((s, i) => s + (i.amount || 0), 0);
  const overdue   = invoices.filter((i) => i.status === "overdue").length;

  el.business.textContent     = fmt(totalBiz);
  el.collect.textContent      = fmt(toCollect);
  el.refunds.textContent      = fmt(refunds);
  el.flagged.textContent      = String(flagged);
  el.txCount.textContent      = `${txCount} transaction${txCount !== 1 ? "s" : ""}`;
  el.overdueCount.textContent = overdue > 0 ? `${overdue} en retard` : "";
}

function renderTodos(actions) {
  const open = actions.filter((a) => a.status === "open").slice(0, 4);
  if (!open.length) return;

  el.todoList.innerHTML = "";
  open.forEach((a) => {
    const li  = document.createElement("li");
    const txt = document.createElement("span");
    txt.className   = "todo-text";
    txt.textContent = a.text || "—";
    li.append(badge("À faire", "blue"), txt);
    el.todoList.append(li);
  });
}

function renderInvoices(invoices) {
  const pending = invoices
    .filter((i) => ["unpaid", "overdue"].includes(i.status))
    .slice(0, 4);

  if (!pending.length) return;

  el.invoiceList.innerHTML = "";
  pending.forEach((inv) => {
    const li      = document.createElement("li");
    const isLate  = inv.status === "overdue";
    const txt     = document.createElement("span");
    txt.className = "todo-text";
    txt.textContent = `${inv.client || "—"} · ${fmt(inv.amount || 0)}`;
    li.append(badge(isLate ? "Impayée" : "En attente", isLate ? "red" : "amber"), txt);
    el.invoiceList.append(li);
  });
}

// ── Main load ─────────────────────────────────────────────────────────────────
async function load() {
  el.loading.classList.remove("hidden");
  el.content.classList.add("hidden");
  el.errorBanner.classList.add("hidden");
  el.btnRefresh.classList.add("spinning");

  try {
    const [summary, actions, invoices] = await Promise.all([
      get("/analytics/summary"),
      get("/actions"),
      get("/invoices"),
    ]);

    renderKpis(summary, Array.isArray(invoices) ? invoices : []);
    renderTodos(Array.isArray(actions)  ? actions  : []);
    renderInvoices(Array.isArray(invoices) ? invoices : []);

    el.loading.classList.add("hidden");
    el.content.classList.remove("hidden");
  } catch {
    el.loading.classList.add("hidden");
    el.errorBanner.classList.remove("hidden");
  } finally {
    el.btnRefresh.classList.remove("spinning");
  }
}

// ── Events ────────────────────────────────────────────────────────────────────
el.btnOpen.addEventListener("click", () => {
  chrome.tabs.create({ url: DASH });
});

el.btnRefresh.addEventListener("click", load);

// ── Init ──────────────────────────────────────────────────────────────────────
load();
