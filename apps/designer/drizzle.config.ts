import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema: './src/lib/db/schema/index.ts',
  out: './src/lib/db/migrations',
  dialect: 'sqlite',
  dbCredentials: {
    url: './designer.db',
  },
  verbose: true,
  strict: true,
})
