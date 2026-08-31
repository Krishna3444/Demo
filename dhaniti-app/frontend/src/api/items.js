// items.js — loan-application CRUD + analytics endpoints.

import { apiFetch } from "./client.js";

export const itemsApi = {
  // ---- CRUD ----
  getItems: (params = {}) => {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "" && value !== "all") {
        search.set(key, value);
      }
    });
    const qs = search.toString();
    return apiFetch(`/api/applications${qs ? "?" + qs : ""}`);
  },

  getItem: (id) => apiFetch(`/api/applications/${encodeURIComponent(id)}`),

  createItem: (payload) =>
    apiFetch("/api/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateItem: (id, payload) =>
    apiFetch(`/api/applications/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  updateStatus: (id, status) =>
    apiFetch(`/api/applications/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify({ applicationStatus: status }),
    }),

  deleteItem: (id) =>
    apiFetch(`/api/applications/${encodeURIComponent(id)}`, { method: "DELETE" }),

  // ---- Analytics (existing dashboard functionality) ----
  kpis: () => apiFetch("/api/kpis"),
  charts: () => apiFetch("/api/charts"),
  insights: () => apiFetch("/api/insights"),
  dataQuality: () => apiFetch("/api/data-quality"),
  filters: () => apiFetch("/api/filters"),
};

// ----------------------------- formatters -----------------------------
export function formatINR(n) {
  if (n === null || n === undefined) return "\u2014";
  const s = Math.round(n).toString();
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3);
  const restGrouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return "\u20b9" + (rest ? restGrouped + "," : "") + last3;
}

export function formatINRCompact(n) {
  if (n >= 1e7) return "\u20b9" + (n / 1e7).toFixed(2) + " Cr";
  if (n >= 1e5) return "\u20b9" + (n / 1e5).toFixed(2) + " L";
  if (n >= 1e3) return "\u20b9" + (n / 1e3).toFixed(1) + " K";
  return "\u20b9" + n;
}

export function statusClass(s) {
  return `badge-status-${String(s).toLowerCase().replace(/\s+/g, "-")}`;
}

export function attentionClass(a) {
  if (a === "Low Attention") return "badge-attention-low";
  if (a === "Review Required") return "badge-attention-review";
  return "badge-attention-high";
}
