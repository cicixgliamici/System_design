// ESLint configuration for the System Design TypeScript layer.
//
// =============================================================================
// WHY ESLINT?
// =============================================================================
//
// ESLint is the standard JavaScript/TypeScript linter. It catches:
//   - Common programming errors (unused variables, unreachable code)
//   - Style issues that differ from team conventions
//   - TypeScript-specific anti-patterns (any, unsafe assignments, etc.)
//
// We use @typescript-eslint, the official TypeScript ESLint plugin, which
// understands TypeScript's type system and can catch type-level errors that
// the compiler itself allows (e.g., accessing a possibly-undefined property
// without a null check).
//
// =============================================================================
// RULE PHILOSOPHY FOR AN EDUCATIONAL REPO
// =============================================================================
//
// Rules are kept "strict but not pedantic":
//   - We enable type-aware rules that catch real bugs (@typescript-eslint/recommended-type-checked).
//   - We allow console.log (educational demos need it).
//   - We allow explicit `any` with a comment (sometimes needed in demos).
//   - We do NOT enforce opinionated formatting rules (use prettier/tsc for that).
//
// Each rule override below is commented to explain WHY it was chosen.

/** @type {import("eslint").Linter.Config} */
module.exports = {
  // root: true prevents ESLint from searching for config files in parent
  // directories. Always set this in a repo's own config.
  root: true,

  // parser: tells ESLint to use the TypeScript parser instead of the
  // default Babel/Espree parser. Required for any TypeScript-specific rules.
  parser: "@typescript-eslint/parser",

  parserOptions: {
    // ecmaVersion: which JavaScript syntax is allowed.
    // "latest" allows all modern syntax (optional chaining, nullish coalescing, etc.)
    ecmaVersion: "latest",

    // sourceType: "module" enables ES module syntax (import/export).
    sourceType: "module",

    // project: points to the tsconfig used for type-aware ESLint rules.
    // We use tsconfig.eslint.json (not tsconfig.json) because the main
    // tsconfig excludes *.spec.ts files (they should not be emitted to dist).
    // ESLint needs a project that includes spec files too, otherwise it errors:
    // "ESLint was configured to run on <spec.ts> but tsconfig does not include this file"
    project: "./tsconfig.eslint.json",
  },

  // plugins: registers the @typescript-eslint plugin so its rules are available.
  plugins: ["@typescript-eslint"],

  // extends: pull in recommended rule sets as a baseline.
  extends: [
    // eslint:recommended: ESLint's own curated set of rules for common bugs.
    // Catches: no-unused-vars, no-undef, no-duplicate-case, etc.
    "eslint:recommended",

    // plugin:@typescript-eslint/recommended: TypeScript-specific rules.
    // Adds: no implicit any, prefer const, no non-null assertion abuse, etc.
    "plugin:@typescript-eslint/recommended",

    // plugin:@typescript-eslint/recommended-requiring-type-checking:
    // Type-aware rules that require the TypeScript compiler to be run.
    // These are the most powerful rules but also the slowest.
    // Examples: no-floating-promises, no-misused-promises, await-thenable.
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
  ],

  // rules: override or extend the rules from the extended configs above.
  rules: {
    // console.log is allowed in educational demos and examples.
    // Real production code should use a proper logging library, but for a
    // demo repo showing system design patterns, console output is fine.
    "no-console": "off",

    // Allow explicit `any` type with a comment explaining why.
    // The recommended config sets this to "warn" — we keep it as warn too,
    // but remind contributors to add a comment when they use it.
    "@typescript-eslint/no-explicit-any": "warn",

    // Unused variables are usually bugs or dead code.
    // We turn off the base rule and use the TypeScript-aware version,
    // which understands type-only imports and destructuring ignores.
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": [
      "error",
      {
        // Variables starting with _ are intentionally unused (common convention).
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
      },
    ],

    // Require all Promises to be either awaited, returned, or void-cast.
    // This prevents silent async failures (a common source of bugs in Node.js).
    "@typescript-eslint/no-floating-promises": "error",

    // Disallow async functions passed where a sync callback is expected.
    // E.g., array.forEach(async (item) => ...) looks right but errors are swallowed.
    "@typescript-eslint/no-misused-promises": "error",
  },

  // ignore: skip files that should not be linted.
  ignorePatterns: [
    // Don't lint compiled output — it's generated, not authored.
    "dist/",
    // Don't lint node_modules.
    "node_modules/",
    // Jest config is plain JS, not TypeScript — simpler to exclude.
    "jest.config.js",
  ],
};
