import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000",
});

// Surface the backend's own error text (FastAPI `detail`) instead of axios'
// generic "Request failed with status code 404". Requests that never got a
// response keep their network message so the UI can tell "offline" apart.
api.interceptors.response.use(undefined, (error) => {
  const detail = error?.response?.data?.detail;
  if (detail) {
    error.message = typeof detail === "string" ? detail : JSON.stringify(detail);
  }
  return Promise.reject(error);
});

export const getDashboard = () => api.get("/api/v1/dashboard").then((r) => r.data);
export const getOrders = (limit = 50) =>
  api.get(`/api/v1/orders?limit=${limit}`).then((r) => r.data);
export const getOrder = (id: number) => api.get(`/api/v1/orders/${id}`).then((r) => r.data);
export const predictLate = (order_id: number) =>
  api.post("/api/v1/predictions/late-delivery", { order_id }).then((r) => r.data);
export const predictDuration = (order_id: number) =>
  api.post("/api/v1/predictions/delivery-duration", { order_id }).then((r) => r.data);
export const predictInventoryStockout = (order_id: number) =>
  api.post("/api/v1/predictions/inventory-stockout", { order_id }).then((r) => r.data);
export const getAnomaly = (order_id: number) =>
  api.get(`/api/v1/predictions/anomaly/${order_id}`).then((r) => r.data);
export const getVendors = () => api.get("/api/v1/vendors").then((r) => r.data);
export const getVendorSegments = () =>
  api.get("/api/v1/vendors/segments").then((r) => r.data);
export const ragQuery = (query: string) =>
  api.post("/api/v1/rag/query", { query }).then((r) => r.data);
export const runInvestigation = (query: string, order_id?: number) =>
  api.post("/api/v1/investigations/run", { query, order_id }).then((r) => r.data);
export const getEvidence = () => api.get("/api/v1/evidence").then((r) => r.data);
export const getShap = () =>
  api.get("/api/v1/explainability/shap/summary").then((r) => r.data);

export default api;
