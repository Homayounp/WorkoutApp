// frontend/src/api.js
import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// ─── Attach token to every request ───────────────────
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Auto-refresh on 401 ────────────────────────────
API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes("/auth/")
    ) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");

      if (refresh) {
        try {
          const res = await axios.post("http://127.0.0.1:8000/auth/refresh", {
            refresh_token: refresh,
          });
          const newToken = res.data.access_token;
          localStorage.setItem("access_token", newToken);
          original.headers.Authorization = `Bearer ${newToken}`;
          return API(original);
        } catch (refreshError) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
          return Promise.reject(refreshError);
        }
      } else {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default API;



// ═══════════════════════════════════════════════════════════════════════════════
// SMART PROGRESSION API CALLS
// ═══════════════════════════════════════════════════════════════════════════════

// Get smart targets for a day
export const getSmartTargets = (dayId) => 
  API.get(`/mesocycle-days/${dayId}/smart-targets`);

// Get smart targets with soreness overrides
export const getSmartTargetsWithSoreness = (dayId, sorenessData) =>
  API.post(`/mesocycle-days/${dayId}/smart-targets`, sorenessData);

// Evaluate a logged set
export const evaluateSet = (setLogId) =>
  API.post(`/sets/${setLogId}/evaluate`);

// Get exercise progression history
export const getExerciseHistory = (exerciseId, limit = 10) =>
  API.get(`/exercises/${exerciseId}/progression-history?limit=${limit}`);
