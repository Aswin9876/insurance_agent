// Zustand store: wizard form state + result, persisted to localStorage
// ("Save progress" feature — refresh the page and your data is still here).
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { CustomerForm, WorkflowSummary } from "@/lib/types";

export const EMPTY_FORM: CustomerForm = {
  first_name: "", last_name: "", email: "", phone: "", age: "",
  gender: "", location: "", occupation: "", annual_income: "",
  marital_status: "", health_conditions: "", smoker: "no",
  insurance_needs: "", budget: "", consent_given: false,
};

interface OnboardingState {
  form: CustomerForm;
  step: number;
  summary: WorkflowSummary | null;
  setField: (key: keyof CustomerForm, value: string | boolean) => void;
  setStep: (step: number) => void;
  setSummary: (s: WorkflowSummary | null) => void;
  reset: () => void;
}

export const useOnboarding = create<OnboardingState>()(
  persist(
    (set) => ({
      form: EMPTY_FORM,
      step: 0,
      summary: null,
      setField: (key, value) =>
        set((s) => ({ form: { ...s.form, [key]: value } })),
      setStep: (step) => set({ step }),
      setSummary: (summary) => set({ summary }),
      reset: () => set({ form: EMPTY_FORM, step: 0, summary: null }),
    }),
    { name: "insurance-onboarding", storage: createJSONStorage(() => localStorage) }
  )
);