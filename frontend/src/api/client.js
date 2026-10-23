/**
 * MuleNet API Client
 */

import {
  getMockAlerts,
  mockAccountDetails,
  mockBudgetCurve,
  mockDrift,
  mockGraph,
  mockHealth,
  mockSummary,
} from "../mocks/mockResponses";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

export class ApiError extends Error {
  constructor(code, message, details = {}, status = 500) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.message = message;
    this.details = details;
    this.status = status;
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  try {
    const res = await fetch(url, {
      headers: {
        Accept: "application/json",
        ...options.headers,
      },
      ...options,
    });

    let json;
    try {
      json = await res.json();
    } catch {
      json = null;
    }

    if (!res.ok) {
      if (json && json.error) {
        throw new ApiError(
          json.error.code || "API_ERROR",
          json.error.message || `API error ${res.status}`,
          json.error.details || {},
          res.status
        );
      }
      throw new ApiError("HTTP_ERROR", `HTTP ${res.status}: ${res.statusText}`, {}, res.status);
    }

    return json;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network or connection failure
    throw new ApiError(
      "NETWORK_ERROR",
      `Cannot reach the backend at ${API_BASE_URL}`,
      { originalError: err.message },
      0
    );
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getHealth() {
  if (USE_MOCKS) {
    await delay(400);
    return { ...mockHealth };
  }
  return request("/api/health");
}

export async function getSummary() {
  if (USE_MOCKS) {
    await delay(400);
    return { ...mockSummary };
  }
  return request("/api/summary");
}

export async function getAlerts({ budget = 100 } = {}) {
  if (USE_MOCKS) {
    await delay(400);
    return getMockAlerts(budget);
  }
  return request(`/api/alerts?budget=${encodeURIComponent(budget)}`);
}

export async function getAccount(accountId) {
  if (USE_MOCKS) {
    await delay(400);
    if (accountId === "ACC-99999") {
      throw new ApiError(
        "ACCOUNT_NOT_FOUND",
        `Account '${accountId}' not found`,
        { account_id: accountId },
        404
      );
    }
    const found = mockAccountDetails[accountId];
    if (found) {
      return { ...found };
    }
    // Return generic mock detail for other accounts
    return {
      account_id: accountId,
      rank: 1,
      risk_score: 0.985,
      baseline_score: 0.98,
      ground_truth_fraud: true,
      true_typology: "fan_in_fan_out",
      ring_id: "RING-001",
      reasons: [
        {
          feature: "forward_ratio_15min",
          text: "Forwarded 92% of received money within 15 minutes",
          shap: 1.5,
          value: 0.92,
        },
      ],
      features: {
        txn_count_out: 2,
        txn_count_in: 5,
        total_out_inr: 25000,
        total_in_inr: 28000,
        avg_amount_out: 12500,
        night_txn_ratio: 0,
        new_payee_ratio: 1,
        max_out_txns_10min: 1,
        account_age_days: 35,
        n_unique_senders: 5,
        n_unique_receivers: 2,
        forward_ratio_15min: 0.92,
        median_hold_minutes: 8,
        neighbour_mean_forward_ratio: 0.05,
      },
    };
  }
  return request(`/api/accounts/${encodeURIComponent(accountId)}`);
}

export async function getGraph(accountId, { hops = 1, maxNodes = 40 } = {}) {
  if (USE_MOCKS) {
    await delay(400);
    if (accountId === "ACC-99999") {
      throw new ApiError(
        "ACCOUNT_NOT_FOUND",
        `Account '${accountId}' not found`,
        { account_id: accountId },
        404
      );
    }
    return { ...mockGraph, center_id: accountId, hops };
  }
  return request(
    `/api/accounts/${encodeURIComponent(accountId)}/graph?hops=${hops}&max_nodes=${maxNodes}`
  );
}

export async function getBudgetCurve() {
  if (USE_MOCKS) {
    await delay(400);
    return { ...mockBudgetCurve };
  }
  return request("/api/budget-curve");
}

export async function getDrift() {
  if (USE_MOCKS) {
    await delay(400);
    return { ...mockDrift };
  }
  return request("/api/drift");
}

// Aliases for compatibility
export const fetchHealth = getHealth;
export const fetchSummary = getSummary;
export const fetchAlerts = (budget = 100) => getAlerts({ budget });
export const fetchAccountDetail = getAccount;
export const fetchAccountGraph = (aid, hops = 1, maxNodes = 40) =>
  getGraph(aid, { hops, maxNodes });
export const fetchBudgetCurve = getBudgetCurve;
export const fetchDrift = getDrift;
