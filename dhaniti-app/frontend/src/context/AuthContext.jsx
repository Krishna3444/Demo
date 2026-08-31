import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../api/auth.js";
import { clearAuth, getToken, getUser, setAuth } from "../api/client.js";

const AuthContext = createContext(null);

/**
 * Central authentication state:
 *   currentUser, isAuthenticated, loading,
 *   login(), logout(), refreshUser(), applySession()
 */
export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(() => getUser());
  const [loading, setLoading] = useState(() => Boolean(getToken())); // verify token on boot
  const [notice, setNotice] = useState(""); // e.g. "session expired" banner on login page

  const applySession = useCallback((token, user) => {
    setAuth(token, user);
    setCurrentUser(user);
  }, []);

  const login = useCallback(
    async (email, password, remember = false) => {
      const { token, user } = await authApi.login(email, password, remember);
      applySession(token, user);
      return user;
    },
    [applySession]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout(); // server-side session revocation
    } catch {
      // Even if the call fails (expired token / offline) clear local state.
    }
    clearAuth();
    setCurrentUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setCurrentUser(null);
      return null;
    }
    try {
      const user = await authApi.me();
      setCurrentUser(user);
      // Keep localStorage in sync with the server truth.
      setAuth(getToken(), user);
      return user;
    } catch {
      clearAuth();
      setCurrentUser(null);
      return null;
    }
  }, []);

  // On mount: verify the stored token against the backend.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (getToken()) {
        try {
          const user = await authApi.me();
          if (!cancelled) {
            setCurrentUser(user);
            setAuth(getToken(), user);
          }
        } catch {
          if (!cancelled) {
            clearAuth();
            setCurrentUser(null);
            setNotice("Your session has expired. Please sign in again.");
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      } else {
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // React to 401s raised anywhere in the app (client.js dispatches this).
  useEffect(() => {
    const onUnauthorized = () => {
      setCurrentUser(null);
      setNotice("Your session has expired. Please sign in again.");
    };
    window.addEventListener("dhaniti:unauthorized", onUnauthorized);
    return () => window.removeEventListener("dhaniti:unauthorized", onUnauthorized);
  }, []);

  const value = useMemo(
    () => ({
      currentUser,
      isAuthenticated: Boolean(currentUser),
      loading,
      notice,
      setNotice,
      login,
      logout,
      refreshUser,
      applySession,
      // Role helpers used by the UI to hide write controls.
      canWrite: Boolean(currentUser && !["Credit Analyst"].includes(currentUser.role)),
    }),
    [currentUser, loading, notice, login, logout, refreshUser, applySession]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
