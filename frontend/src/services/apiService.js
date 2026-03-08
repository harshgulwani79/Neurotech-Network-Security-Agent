export const fetchHistory = async () => {
  const response = await fetch("/api/history");
  if (!response.ok) throw new Error("Failed to fetch history");
  return response.json();
};

export const injectAnomaly = async (type) => {
  const response = await fetch("/api/inject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type }),
  });
  if (!response.ok) throw new Error("Failed to inject anomaly");
  return response.json();
};

// Mode management
export const getMode = async () => {
  const response = await fetch("/api/mode");
  if (!response.ok) throw new Error("Failed to get mode");
  return response.json();
};

export const setMode = async (mode) => {
  const response = await fetch("/api/mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!response.ok) throw new Error("Failed to set mode");
  return response.json();
};

// Learned policies
export const getPolicies = async () => {
  const response = await fetch("/api/policies");
  if (!response.ok) throw new Error("Failed to fetch policies");
  return response.json();
};

export const clearPolicies = async () => {
  const response = await fetch("/api/policies/clear", {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to clear policies");
  return response.json();
};
