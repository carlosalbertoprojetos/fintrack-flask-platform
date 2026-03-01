import { z } from "zod";

export const registerUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  fullName: z.string().min(3),
  workspaceName: z.string().min(2)
});

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

export type RegisterUserInput = z.infer<typeof registerUserSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
