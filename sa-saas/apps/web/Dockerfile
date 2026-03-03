FROM node:22-alpine AS base
RUN corepack enable

FROM base AS deps
WORKDIR /app

COPY package.json pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json

RUN pnpm install --no-frozen-lockfile

FROM deps AS build
WORKDIR /app
COPY . .
RUN pnpm --filter @sa/web build

FROM base AS runtime
WORKDIR /app
ENV NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=build /app/tsconfig.base.json ./tsconfig.base.json
COPY --from=build /app/apps/web ./apps/web

EXPOSE 3000
WORKDIR /app/apps/web
CMD ["node", "/app/node_modules/next/dist/bin/next", "start", "-p", "3000"]
