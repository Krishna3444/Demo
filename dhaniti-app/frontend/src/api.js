// api.js — backward-compatible re-export layer.
//
// The original single-file API client was split into:
//   src/api/client.js  (HTTP + token handling)
//   src/api/auth.js    (authentication calls)
//   src/api/items.js   (CRUD + analytics calls)
//
// Existing components (KpiCards, Charts, Insights, DataQuality,
// ApplicationsTable, Dashboard) keep importing from "../api.js" unchanged.

import { getToken, setAuth, clearAuth, getUser } from "./api/client.js";
import { authApi } from "./api/auth.js";
import { itemsApi, formatINR, formatINRCompact, statusClass, attentionClass } from "./api/items.js";

export { getToken, setAuth, clearAuth, getUser };
export { formatINR, formatINRCompact, statusClass, attentionClass };
export { authApi, itemsApi };

// Legacy-shaped `api` object (same methods as the original client).
export const api = {
  login: (email, password) => authApi.login(email, password),
  kpis: () => itemsApi.kpis(),
  charts: () => itemsApi.charts(),
  insights: () => itemsApi.insights(),
  dataQuality: () => itemsApi.dataQuality(),
  filters: () => itemsApi.filters(),
  applications: (params = "") => {
    if (typeof params === "string") {
      return itemsApi.getItems(params ? Object.fromEntries(new URLSearchParams(params)) : {});
    }
    return itemsApi.getItems(params);
  },
  updateStatus: (id, status) => itemsApi.updateStatus(id, status),
};

export default api;
