import { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it } from "vitest";

import { apiClient } from "@/lib/api-client";

const originalAdapter = apiClient.defaults.adapter;

function respondWith401(): AxiosAdapter {
  return async (config: InternalAxiosRequestConfig) => {
    const response = { status: 401, statusText: "Unauthorized", data: { detail: "Incorrect email or password" }, headers: {}, config };
    throw new AxiosError("Unauthorized", "ERR_BAD_REQUEST", config, null, response);
  };
}

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter;
});

describe("401 handling", () => {
  it("passes a credential error straight back to the form instead of refreshing", async () => {
    apiClient.defaults.adapter = respondWith401();
    const error = await apiClient.post("/auth/login", {}).catch((e) => e);
    expect(error).toBeInstanceOf(AxiosError);
    expect(error.response.status).toBe(401);
    expect(error.response.data.detail).toBe("Incorrect email or password");
  });

  it("treats an invalid reset link the same way", async () => {
    apiClient.defaults.adapter = respondWith401();
    const error = await apiClient.post("/auth/reset-password", {}).catch((e) => e);
    expect(error.response.status).toBe(401);
  });

  it("tries a session refresh for other endpoints", async () => {
    apiClient.defaults.adapter = respondWith401();
    // No refresh token is stored, so the refresh attempt itself fails.
    const error = await apiClient.get("/backtests").catch((e) => e);
    expect(error).not.toBeInstanceOf(AxiosError);
    expect(String(error.message)).toContain("No refresh token");
  });
});
