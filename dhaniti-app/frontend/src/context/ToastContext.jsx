import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

const ToastContext = createContext(null);

let nextId = 1;

/**
 * Bootstrap-styled toast notifications.
 *   const toast = useToast();
 *   toast.success("Record created successfully");
 *   toast.error("Unable to save record");
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});

  const dismiss = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
    if (timers.current[id]) {
      clearTimeout(timers.current[id]);
      delete timers.current[id];
    }
  }, []);

  const push = useCallback(
    (variant, message, options = {}) => {
      const id = nextId++;
      const toast = {
        id,
        variant,
        message,
        title: options.title || (variant === "success" ? "Success" : variant === "error" ? "Error" : "Notice"),
        duration: options.duration ?? 4500,
      };
      setToasts((list) => [...list.slice(-4), toast]); // keep max 5 visible
      timers.current[id] = setTimeout(() => dismiss(id), toast.duration);
      return id;
    },
    [dismiss]
  );

  const toast = useMemo(
    () => ({
      success: (message, options) => push("success", message, options),
      error: (message, options) => push("error", message, options),
      info: (message, options) => push("info", message, options),
      warning: (message, options) => push("warning", message, options),
      dismiss,
    }),
    [push, dismiss]
  );

  const variantClass = {
    success: "text-bg-success",
    error: "text-bg-danger",
    info: "text-bg-primary",
    warning: "text-bg-warning",
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        className="toast-container position-fixed top-0 end-0 p-3"
        style={{ zIndex: 1090, maxWidth: 380 }}
        aria-live="polite"
        aria-atomic="true"
      >
        {toasts.map((t) => (
          <div key={t.id} className={`toast show align-items-center border-0 ${variantClass[t.variant]}`} role="alert">
            <div className="d-flex">
              <div className="toast-body">
                <strong className="d-block mb-1">{t.title}</strong>
                {t.message}
              </div>
              <button
                type="button"
                className="btn-close btn-close-white me-2 m-auto"
                aria-label="Close"
                onClick={() => dismiss(t.id)}
              />
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}
