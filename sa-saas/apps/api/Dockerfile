FROM node:22-alpine AS base
RUN corepack enable

FROM base AS deps
WORKDIR /app

COPY package.json pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/api/package.json apps/api/package.json
COPY packages/shared/package.json packages/shared/package.json
COPY packages/ai-core/package.json packages/ai-core/package.json

RUN pnpm install --no-frozen-lockfile

FROM deps AS build
WORKDIR /app
COPY . .

RUN pnpm --filter @sa/shared build
RUN pnpm --filter @sa/ai-core build
RUN pnpm --filter @sa/api prisma:generate
RUN pnpm --filter @sa/api build

FROM base AS runtime
WORKDIR /app
ENV NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/apps/api/package.json ./apps/api/package.json
COPY --from=build /app/apps/api/dist ./apps/api/dist
COPY --from=build /app/apps/api/prisma ./apps/api/prisma
COPY --from=build /app/packages/shared/package.json ./packages/shared/package.json
COPY --from=build /app/packages/shared/dist ./packages/shared/dist
COPY --from=build /app/packages/ai-core/package.json ./packages/ai-core/package.json
COPY --from=build /app/packages/ai-core/dist ./packages/ai-core/dist

WORKDIR /app/apps/api
EXPOSE 4000

CMD ["node", "dist/index.js"]
