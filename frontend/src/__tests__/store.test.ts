// Unit tests for the Zustand onboarding store
import { useOnboarding, EMPTY_FORM } from "@/store/onboarding";

describe("onboarding store", () => {
  beforeEach(() => {
    useOnboarding.getState().reset();
  });

  it("starts empty at step 0", () => {
    const s = useOnboarding.getState();
    expect(s.step).toBe(0);
    expect(s.form).toEqual(EMPTY_FORM);
    expect(s.summary).toBeNull();
  });

  it("setField updates a single field", () => {
    useOnboarding.getState().setField("first_name", "Ada");
    const s = useOnboarding.getState();
    expect(s.form.first_name).toBe("Ada");
    expect(s.form.last_name).toBe("");
  });

  it("setStep moves the wizard", () => {
    useOnboarding.getState().setStep(3);
    expect(useOnboarding.getState().step).toBe(3);
  });

  it("reset clears everything", () => {
    useOnboarding.getState().setField("first_name", "Ada");
    useOnboarding.getState().setStep(2);
    useOnboarding.getState().reset();
    const s = useOnboarding.getState();
    expect(s.form).toEqual(EMPTY_FORM);
    expect(s.step).toBe(0);
    expect(s.summary).toBeNull();
  });
});