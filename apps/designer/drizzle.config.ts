import { defineConfig } from 'drizzle-kit'

const shouldUseTurso = !!process.env.TURSO_DATABASE_URL

export default defineConfig({
  schema: './src/lib/db/schema/index.ts',
  out: './src/lib/db/migrations',
  dialect: shouldUseTurso ? 'turso' : 'sqlite',
  ...(shouldUseTurso
    ? {
        // Migrate against Turso/libSQL when env is provided
        dbCredentials: {
          url: process.env.TURSO_DATABASE_URL!,
          authToken: process.env.TURSO_AUTH_TOKEN,
        },
      }
    : {
        // Default to local file DB
        dbCredentials: {
          url: './designer.db',
        },
      }),
  verbose: true,
  strict: true,
})
