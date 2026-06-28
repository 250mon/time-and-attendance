import { z } from "zod";

const _slugOptional = z
  .string()
  .max(64)
  .regex(/^[a-z0-9][a-z0-9-]*[a-z0-9]$|^$/, "Use lowercase letters, numbers, and hyphens")
  .optional()
  .or(z.literal(""));

const _slugRequired = z
  .string()
  .min(3, "Clinic ID is required")
  .max(64)
  .regex(/^[a-z0-9][a-z0-9-]*[a-z0-9]$/, "Use lowercase letters, numbers, and hyphens");

export const loginSchema = z.object({
  clinic_slug:
    process.env.NEXT_PUBLIC_MULTI_TENANT_ENABLED === "true" ? _slugRequired : _slugOptional,
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

export const staffCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email address"),
  phone: z.string().optional(),
  password: z.string().min(6, "Password must be at least 6 characters"),
  role: z.enum(["OWNER", "ADMIN", "MANAGER", "STAFF"]),
  employment_type: z.enum(["FULL_TIME", "PART_TIME", "CONTRACT", "TEMPORARY"]),
  hire_date: z.string().optional(),
});

export const staffUpdateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email address"),
  phone: z.string().optional(),
  role: z.enum(["OWNER", "ADMIN", "MANAGER", "STAFF"]),
  employment_type: z.enum(["FULL_TIME", "PART_TIME", "CONTRACT", "TEMPORARY"]),
  hire_date: z.string().optional(),
  status: z.enum(["ACTIVE", "INACTIVE", "TERMINATED"]),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type StaffCreateFormValues = z.infer<typeof staffCreateSchema>;
export type StaffUpdateFormValues = z.infer<typeof staffUpdateSchema>;
