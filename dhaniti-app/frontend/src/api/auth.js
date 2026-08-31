// auth.js — every authentication API call in one place.

import { apiFetch } from "./client.js";

export const authApi = {
  login: (email, password, remember = false) =>
    apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, remember }),
    }),

  register: (name, email, password, confirmPassword) =>
    apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, confirmPassword }),
    }),

  me: () => apiFetch("/api/auth/me"),

  updateProfile: (payload) =>
    apiFetch("/api/auth/me", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  changePassword: (currentPassword, newPassword) =>
    apiFetch("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ currentPassword, newPassword }),
    }),

  logout: () => apiFetch("/api/auth/logout", { method: "POST" }),

  sendOtp: (email, purpose = "login") =>
    apiFetch("/api/auth/send-otp", {
      method: "POST",
      body: JSON.stringify({ email, purpose }),
    }),

  verifyOtp: (email, code, purpose = "login", remember = false) =>
    apiFetch("/api/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ email, code, purpose, remember }),
    }),

  verifyResetOtp: (email, code) =>
    apiFetch("/api/auth/verify-reset-otp", {
      method: "POST",
      body: JSON.stringify({ email, code, purpose: "password_reset" }),
    }),

  resetPassword: (resetToken, newPassword) =>
    apiFetch("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ resetToken, newPassword }),
    }),

  resendVerification: (email) =>
    apiFetch("/api/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  oauthProviders: () => apiFetch("/api/auth/oauth/providers"),

  oauthExchange: (code) =>
    apiFetch("/api/auth/oauth/exchange", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),
};
