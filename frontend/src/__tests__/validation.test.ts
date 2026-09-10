// Wizard step-validation logic tests (mirrors validateStep rules)
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^\+?[0-9][0-9\- ]{7,14}$/;

function validate(fields: Record<string, string>): Record<string, string> {
  const e: Record<string, string> = {};
  if (!fields.first_name?.trim()) e.first_name = "First name is required";
  const age = Number(fields.age);
  if (!fields.age || Number.isNaN(age) || age < 18 || age > 100)
    e.age = "Age must be 18–100";
  if (fields.email && !EMAIL_RE.test(fields.email)) e.email = "Invalid email";
  if (fields.phone && !PHONE_RE.test(fields.phone)) e.phone = "Invalid phone";
  return e;
}

describe("wizard validation", () => {
  it("passes for a valid personal step", () => {
    expect(validate({ first_name: "Ada", age: "30" })).toEqual({});
  });

  it("requires first name", () => {
    expect(validate({ first_name: "", age: "30" }).first_name).toBeDefined();
  });

  it("rejects age under 18 and over 100", () => {
    expect(validate({ first_name: "A", age: "15" }).age).toBeDefined();
    expect(validate({ first_name: "A", age: "101" }).age).toBeDefined();
  });

  it("rejects bad email", () => {
    expect(validate({ first_name: "A", age: "30", email: "nope" }).email).toBeDefined();
  });

  it("accepts valid email", () => {
    expect(validate({ first_name: "A", age: "30", email: "a@b.co" }).email).toBeUndefined();
  });

  it("rejects bad phone", () => {
    expect(validate({ first_name: "A", age: "30", phone: "1" }).phone).toBeDefined();
  });

  it("accepts valid phone", () => {
    expect(validate({ first_name: "A", age: "30", phone: "+1-555-123-4567" }).phone).toBeUndefined();
  });
});