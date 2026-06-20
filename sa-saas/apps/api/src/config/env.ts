import { existsSync } from "node:fs";
import path from "node:path";
import dotenv from "dotenv";
import { z } from "zod";

const envCandidates = [
  path.resolve(process.cwd(), ".env"),
  path.resolve(process.cwd(), "../../.env")
];

for (const candidate of envCandidates) {
  if (existsSync(candidate)) {
    dotenv.config({ path: candidate });
    break;
  }
}

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  API_PORT: z.coerce.number().int().positive().default(4000),
  DATABASE_URL: z.string().min(1).optional(),
  DATABASE_HOST: z.string().min(1).optional(),
  DATABASE_PORT: z.coerce.number().int().positive().default(5432),
  DATABASE_NAME: z.string().min(1).optional(),
  DATABASE_USER: z.string().min(1).optional(),
  DATABASE_PASSWORD: z.string().optional(),
  JWT_SECRET: z.string().min(16),
  LOG_LEVEL: z.string().default("info"),
  AI_PROVIDER: z.enum(["mock", "openai", "anthropic"]).default("mock"),
  OPENAI_API_KEY: z.string().optional(),
  ANTHROPIC_API_KEY: z.string().optional()
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  const errors = parsed.error.issues.map((issue) => `${issue.path.join(".")}: ${issue.message}`).join("; ");
  throw new Error(`Invalid environment: ${errors}`);
}

function buildDatabaseUrl(values: z.infer<typeof envSchema>): string {
  if (values.DATABASE_URL) {
    return values.DATABASE_URL;
  }

  const requiredFields = [
    "DATABASE_HOST",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD"
  ] as const;

  const missingFields = requiredFields.filter((field) => !values[field]);
  if (missingFields.length > 0) {
    throw new Error(
      `Invalid environment: provide DATABASE_URL or fill ${missingFields.join(", ")}`
    );
  }

  const user = encodeURIComponent(values.DATABASE_USER ?? "");
  const password = encodeURIComponent(values.DATABASE_PASSWORD ?? "");
  const host = values.DATABASE_HOST ?? "localhost";
  const port = values.DATABASE_PORT;
  const databaseName = values.DATABASE_NAME ?? "";

  return `postgresql://${user}:${password}@${host}:${port}/${databaseName}`;
}

export const env = {
  ...parsed.data,
  DATABASE_URL: buildDatabaseUrl(parsed.data)
};
