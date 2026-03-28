"use client";

import { useEffect, useState } from "react";

type AccessibilityState = {
  highContrast: boolean;
  reducedMotion: boolean;
};

const STORAGE_KEY = "aegis-os-accessibility";

export function useAccessibility() {
  const [state, setState] = useState<AccessibilityState>({
    highContrast: false,
    reducedMotion: false
  });

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return;
    }

    try {
      setState(JSON.parse(raw) as AccessibilityState);
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.contrast = state.highContrast ? "high" : "default";
    document.documentElement.dataset.motion = state.reducedMotion ? "reduced" : "default";
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  return {
    state,
    setHighContrast(value: boolean) {
      setState((current) => ({ ...current, highContrast: value }));
    },
    setReducedMotion(value: boolean) {
      setState((current) => ({ ...current, reducedMotion: value }));
    }
  };
}
