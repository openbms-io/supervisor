# Repository Guidelines

## Project Structure & Module Organization

- apps/designer: Next.js app (UI, React Flow, Zustand, Drizzle ORM)
  - src/lib/db: DB client, schema, repository, migrations
  - src/components: UI components and canvas tools
  - src/store: Zustand slices and hooks
  - src/app: Next.js routes/pages
- packages/bms-schemas: Shared Zod schemas/utilities used across apps
- specs: Product/engineering specifications

## Build, Test, and Development Commands

- Install (workspace): `pnpm install`
- Dev (designer): `pnpm --filter designer dev`
- Build (CI/Vercel): `pnpm --filter bms-schemas build && pnpm --filter designer build`
- Lint: `pnpm --filter designer lint`
- Tests (serial): `pnpm --filter designer test`
- DB (designer):
  - Generate migrations: `pnpm --filter designer db:generate`
  - Apply migrations: `pnpm --filter designer db:migrate`

## Coding Style & Naming Conventions

- Language: TypeScript (ES modules)
- Linting: ESLint; Formatting: Prettier
- Components/hooks: `kebab-case` filenames, `PascalCase` for React components, `camelCase` for functions/vars
- Avoid `require()`; use `import` syntax
- Keep functions small and focused; prefer pure functions where possible

## Testing Guidelines

- Runner: Jest; React tests: @testing-library/react
- Location: colocated `*.spec.ts`/`*.spec.tsx` near source or under `src/**`
- Database tests run in-band and migrate schema once in Jest setup
- Aim for fast, deterministic tests; mock network as needed

## Commit & Pull Request Guidelines

- Commits: Imperative mood, concise summary (e.g., "Add workflow loader overlay")
- Group related changes; avoid unrelated refactors in the same commit
- PRs: Include clear description, screenshots for UI, and linked issues/specs
- Ensure CI passes (build, lint, tests) and migrations are included when schema changes

## Security & Configuration Tips

- Local SQLite (dev/tests): `DATABASE_PATH` controls DB file path
- Remote DB (Turso/libSQL): set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`; do not run runtime migrations there
- Do not commit secrets; use environment variables and Vercel project settings

## Notes for Workspace Builds

- Always build shared packages first, e.g.: `pnpm --filter bms-schemas build` before designer
- Next.js will consume compiled output from `bms-schemas`
