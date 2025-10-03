/** @type {import('jest').Config} */
export default {
  projects: [
    "<rootDir>/packages/bms-schemas",
    "<rootDir>/packages/mqtt_topics",
  ],
  collectCoverageFrom: [
    "packages/*/src/**/*.ts",
    "packages/*/*.ts",
    "!**/*.d.ts",
    "!**/*.spec.{ts,tsx}",
    "!**/*.test.{ts,tsx}",
  ],
  coverageDirectory: "<rootDir>/coverage",
  coverageReporters: ["text", "lcov", "html"],
};
