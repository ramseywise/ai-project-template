/** @type {import('jest').Config} */
// package.json has "type": "module" — ts-jest must run in ESM mode (useESM) and
// .ts imports need their extensionless specifiers mapped, or Jest's CommonJS
// loader chokes on `import` syntax before ts-jest ever gets a chance to transform it.
module.exports = {
  testEnvironment: "node",
  extensionsToTreatAsEsm: [".ts"],
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "tsconfig.test.json", isolatedModules: true, useESM: true }],
  },
  testMatch: ["**/tests/**/*.test.ts"],
};
