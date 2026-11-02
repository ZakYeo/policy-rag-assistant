import { RuleTester } from 'eslint';
import parser from '@typescript-eslint/parser';
import rule from './mvvm.mjs';

const tester = new RuleTester({ languageOptions: { parser, parserOptions: { ecmaFeatures: { jsx: true } } } });
const file = (layer, code) => ({ filename: `/project/frontend/src/${layer}/example.tsx`, code });
const invalid = (layer, code) => ({ ...file(layer, code), errors: [{ messageId: 'boundary' }] });

tester.run('mvvm', rule, {
  valid: [
    file('views', 'import type { State } from "../contracts/types"; export const View = (p: State) => <p>{p.answer}</p>;'),
    file('viewmodels', 'import { useReducer } from "react"; import { api } from "@/models/api";'),
    file('models', 'export const request = () => fetch("/api/ask");'),
    file('views', 'import { useId } from "react";'),
    file('composition', 'import { useDesk } from "../viewmodels/desk"; import { View } from "../views/Desk";'),
  ],
  invalid: [
    invalid('views', 'import { api } from "../models/api";'),
    invalid('views', 'import { api } from "@/models/api";'),
    invalid('views', 'export { api } from "../models/api";'),
    invalid('views', 'export * from "@/viewmodels/desk";'),
    invalid('views', 'import { useState as state } from "react";'),
    invalid('views', 'import React from "react"; React.useEffect(() => {});'),
    invalid('views', 'fetch("/api/ask");'),
    invalid('views', 'window.localStorage.getItem("theme");'),
    invalid('views', 'globalThis.fetch("/api/ask");'),
    invalid('views', 'const x = await import("../models/api");'),
    invalid('views', 'const get = fetch;'),
    invalid('views', 'const { localStorage } = window;'),
    invalid('views', 'const api = require("../models/api");'),
    invalid('viewmodels', 'document.querySelector("main");'),
    invalid('viewmodels', 'import { View } from "../views/Desk";'),
    invalid('viewmodels', 'export const x = <p/>;'),
    invalid('models', 'import React from "react";'),
    invalid('contracts', 'import { api } from "../models/api";'),
  ],
});
