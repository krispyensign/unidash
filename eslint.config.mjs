import { defineConfig, globalIgnores } from "eslint/config";
import prettier from "eslint-plugin-prettier";
import tsParser from "@typescript-eslint/parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";

import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default defineConfig([
    // globalIgnores(["node_modules/*", "dist/*"]), 
    {
        // extends: compat.extends(".prettierrc.mjs", "plugin:@typescript-eslint/recommended"),

        files: ["src/**/*.ts"],

        plugins: {
            prettier,
            "@typescript-eslint": tsPlugin,
        },

        languageOptions: {
            parser: tsParser,
            ecmaVersion: "latest",
            sourceType: "module",
        },

        rules: {
            "prettier/prettier": "error",
            "block-scoped-var": "error",
            eqeqeq: "error",
            "eol-last": "error",

            "max-len": ["error", {
                code: 100,
            }],

            "prefer-arrow-callback": "error",

            quotes: ["warn", "single", {
                avoidEscape: true,
            }],

            "require-atomic-updates": "off",
            semi: "off",
            "prefer-const": "off",
            "no-trailing-spaces": "error",
            "no-var": "error",
            "no-loss-of-precision": "off",
            "no-dupe-class-members": "off",

            "no-restricted-properties": ["error", {
                object: "describe",
                property: "only",
            }, {
                object: "it",
                property: "only",
            }],

            "@typescript-eslint/array-type": ["error", {
                default: "array",
            }],

            "@typescript-eslint/ban-types": "off",
            "@typescript-eslint/camelcase": "off",
            "@typescript-eslint/explicit-function-return-type": "error",
            "@typescript-eslint/explicit-module-boundary-types": "error",
            "@typescript-eslint/member-delimiter-style": "off",
            // "@typescript-eslint/prefer-optional-chain": "error",
            "@typescript-eslint/no-non-null-assertion": "off",
            "@typescript-eslint/no-warning-comments": "off",
            "@typescript-eslint/no-empty-function": "off",
            "@typescript-eslint/no-use-before-define": "error",
            "@typescript-eslint/no-confusing-non-null-assertion": "error",
            "@typescript-eslint/no-extra-non-null-assertion": "error",
            "@typescript-eslint/no-inferrable-types": "error",
            "@typescript-eslint/no-loss-of-precision": "error",
        },
}]);