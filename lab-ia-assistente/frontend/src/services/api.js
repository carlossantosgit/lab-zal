const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const API_BASE = process.env.REACT_APP_API_BASE || "/api/v1";

const client = {
  async get(endpoint) {
    const response = await fetch(`${API_URL}${API_BASE}${endpoint}`);
    return response.json();
  },

  async post(endpoint, data) {
    const response = await fetch(`${API_URL}${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return response.json();
  },
};

export const analysisService = {
  async analyze(hours = 24) {
    return client.post("/analysis/analyze", { hours });
  },

  async generatePDF(hours = 24) {
    return client.post("/analysis/generate-pdf", { hours });
  },

  async getStatus() {
    return client.get("/analysis/status");
  },
};

export const alertsService = {
  async getAlerts(hours = 24) {
    return client.get(`/alerts?hours=${hours}`);
  },

  async getAlert(id) {
    return client.get(`/alerts/${id}`);
  },
};
