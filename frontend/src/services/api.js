/**
 * Zach's Liquor Store — API Client v2
 */
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const api = axios.create({ baseURL: BASE_URL, timeout: 15000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  login:       (data) => api.post("/auth/login", data),
  verifyMFA:   (data) => api.post("/auth/mfa/verify", data),
  register:    (data) => api.post("/auth/register", data),
  me:          ()     => api.get("/auth/me"),
  setupTOTP:   ()     => api.post("/auth/mfa/setup/totp"),
  confirmTOTP: (code) => api.post("/auth/mfa/setup/totp/confirm", { code }),
  disableMFA:  ()     => api.post("/auth/mfa/disable"),
};

export const productsAPI = {
  list:            (params) => api.get("/products/", { params }),
  get:             (id)     => api.get(`/products/${id}`),
  create:          (data)   => api.post("/products/", data),
  update:          (id, d)  => api.patch(`/products/${id}`, d),
  delete:          (id)     => api.delete(`/products/${id}`),
  categories:      ()       => api.get("/products/categories"),
  priceSuggestions:()       => api.get("/products/price-suggestions"),
};

export const salesAPI = {
  list:   (params) => api.get("/sales/", { params }),
  create: (data)   => api.post("/sales/", data),
  get:    (id)     => api.get(`/sales/${id}`),
  delete: (id)     => api.delete(`/sales/${id}`),
};

export const expensesAPI = {
  list:           (params) => api.get("/expenses/", { params }),
  create:         (data)   => api.post("/expenses/", data),
  update:         (id, d)  => api.patch(`/expenses/${id}`, d),
  delete:         (id)     => api.delete(`/expenses/${id}`),
  listCategories: ()       => api.get("/expenses/categories"),
  createCategory: (data)   => api.post("/expenses/categories", data),
};

export const analyticsAPI = {
  dashboard:        ()       => api.get("/analytics/dashboard"),
  daily:            (days)   => api.get("/analytics/daily", { params: { days } }),
  monthly:          (year)   => api.get("/analytics/monthly", { params: year ? { year } : {} }),
  yearly:           ()       => api.get("/analytics/yearly"),
  seasonal:         (k, y)   => api.get("/analytics/seasonal", { params: { season_key: k, year: y } }),
  topProducts:      (p)      => api.get("/analytics/top-products", { params: p }),
  bottomProducts:   (p)      => api.get("/analytics/bottom-products", { params: p }),
  plSummary:        (year)   => api.get("/analytics/pl-summary", { params: year ? { year } : {} }),
  categoryBreakdown:(days)   => api.get("/analytics/category-breakdown", { params: { period_days: days } }),
  hourlyHeatmap:    (days)   => api.get("/analytics/hourly-heatmap", { params: { period_days: days } }),
  historicalSummary:()       => api.get("/analytics/historical-summary"),
  brandPerformance: (days)   => api.get("/analytics/brand-performance", { params: { period_days: days } }),
  seasonsOverview:  (year)   => api.get("/analytics/seasons-overview", { params: { year } }),
};

export const dealsAPI = {
  list:        (params) => api.get("/deals/", { params }),
  unreadCount: ()       => api.get("/deals/unread-count"),
  markRead:    (id)     => api.post(`/deals/${id}/read`),
  checkNow:    (sid)    => api.post("/deals/check-now", null, { params: sid ? { supplier_id: sid } : {} }),
};

export const promotionsAPI = {
  list:   ()         => api.get("/promotions/"),
  create: (data)     => api.post("/promotions/", data),
  update: (id, data) => api.patch(`/promotions/${id}`, data),
  delete: (id)       => api.delete(`/promotions/${id}`),
};

export default api;

// already defined above — just adding seasonsOverview
