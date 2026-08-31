import React, { useEffect, useRef } from "react";

/**
 * N-box verification code input with auto-advance, paste support and
 * keyboard navigation. Calls onComplete(code) when every box is filled.
 */
export default function OtpInput({ length = 6, value, onChange, onComplete, disabled = false, autoFocus = true }) {
  const inputsRef = useRef([]);
  const chars = Array.from({ length }, (_, i) => (value || "")[i] || "");

  useEffect(() => {
    if (autoFocus && inputsRef.current[0] && !disabled) {
      inputsRef.current[0].focus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function emit(nextChars) {
    const code = nextChars.join("");
    onChange(code);
    if (code.length === length && !nextChars.includes("")) {
      onComplete && onComplete(code);
    }
  }

  function handleChange(index, raw) {
    const digit = raw.replace(/\D/g, "").slice(-1); // keep last digit typed
    const next = [...chars];
    next[index] = digit;
    emit(next);
    if (digit && index < length - 1) {
      inputsRef.current[index + 1]?.focus();
      inputsRef.current[index + 1]?.select();
    }
  }

  function handleKeyDown(index, e) {
    if (e.key === "Backspace") {
      e.preventDefault();
      const next = [...chars];
      if (next[index]) {
        next[index] = "";
        emit(next);
      } else if (index > 0) {
        next[index - 1] = "";
        emit(next);
        inputsRef.current[index - 1]?.focus();
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      e.preventDefault();
      inputsRef.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < length - 1) {
      e.preventDefault();
      inputsRef.current[index + 1]?.focus();
    }
  }

  function handlePaste(e) {
    e.preventDefault();
    const pasted = (e.clipboardData.getData("text") || "").replace(/\D/g, "").slice(0, length);
    if (!pasted) return;
    const next = Array.from({ length }, (_, i) => pasted[i] || "");
    emit(next);
    const focusIdx = Math.min(pasted.length, length - 1);
    inputsRef.current[focusIdx]?.focus();
  }

  return (
    <div className="d-flex justify-content-center gap-2 otp-inputs" onPaste={handlePaste}>
      {chars.map((char, index) => (
        <input
          key={index}
          ref={(el) => (inputsRef.current[index] = el)}
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={1}
          className="form-control otp-box"
          value={char}
          disabled={disabled}
          aria-label={`Digit ${index + 1} of ${length}`}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onFocus={(e) => e.target.select()}
        />
      ))}
    </div>
  );
}
