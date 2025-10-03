/** @type {import('jest').Config} */
export default {
  preset: "ts-jest/presets/default-esm",
  extensionsToTreatAsEsm: [".ts"],
  testEnvironment: "node",
  roots: ["<rootDir>/src"],
  testMatch: ["**/*.spec.ts", "**/*.test.ts"],
  transform: {
    "^.+\\.ts$": [
      "ts-jest",
      {
        useESM: true,
      },
    ],
  },
  collectCoverageFrom: [
    "src/**/*.ts",
    "!src/**/*.d.ts",
    "!src/**/*.spec.ts",
    "!src/**/*.test.ts",
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "html"],
};
