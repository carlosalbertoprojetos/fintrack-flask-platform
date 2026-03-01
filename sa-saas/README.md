# SA SaaS - Social Authority SaaS Intelligence System

Production-oriented monorepo with:
- Next.js (web)
- Node.js + TypeScript (api)
- PostgreSQL + Prisma
- AI provider abstraction and prompt versioning

## Workspaces
- apps/web
- apps/api
- packages/shared
- packages/ai-core

## Quick start
1. Copy `.env.example` to `.env` in `sa-saas/`.
2. Run PostgreSQL locally (or via Docker).
3. Install dependencies with `pnpm install`.
4. Run `pnpm dev`.

## Architecture notes
- Modular services by domain engine.
- Prompt orchestration isolated from provider implementation.
- Feedback layer scaffolded for future engagement learning.
