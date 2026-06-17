import { loginSchema } from "@/lib/validation";

describe("loginSchema", () => {
  it("accepts valid credentials", () => {
    const result = loginSchema.safeParse({
      email: "staff@clinic.example",
      password: "password123",
    });

    expect(result.success).toBe(true);
  });

  it("rejects invalid email addresses", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "password123",
    });

    expect(result.success).toBe(false);
  });
});
