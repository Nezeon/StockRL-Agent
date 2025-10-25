/**
 * Basic ESLint config for React + TypeScript + Vite.
 * Keeps rules modest to avoid noisy errors while enabling helpful checks.
 */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
  },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint', 'react-hooks'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: [
    'dist/',
    'node_modules/',
    'vite.config.ts',
    'tsconfig*.json',
  ],
  rules: {
    // Allow "any" while the codebase stabilizes; tighten later
    '@typescript-eslint/no-explicit-any': 'off',
    // Permit unused vars prefixed with _ (common for placeholders)
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    // Prefer const when possible (safe auto-fix)
    'prefer-const': 'warn',
  },
}
