// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const element = () => ({
  className: "",
  classList: {add(){}, remove(){}, toggle(){}},
  getContext: () => context2d,
  getBoundingClientRect: () => ({width: 390, height: 390, left: 0, top: 0}),
  addEventListener(){},
  innerHTML: "",
  textContent: "",
  hidden: false,
});

const context2d = new Proxy({}, {
  get(target, property) {
    if (!(property in target)) target[property] = () => ({addColorStop(){}});
    return target[property];
  },
  set(target, property, value) { target[property] = value; return true; },
});

const elements = new Map();
const sandbox = {
  console,
  devicePixelRatio: 2,
  document: {getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); }},
  window: {addEventListener(){}},
  Worker: class { constructor() { throw new Error("WASM intentionally unavailable in unit test"); } },
  clearTimeout(){},
  setTimeout(){ return 1; },
  setInterval(){ return 1; },
};

const source = fs.readFileSync(new URL("../android/app/src/main/assets/app.js", import.meta.url), "utf8");
const tests = `
  board = blankBoard(); moves = []; winner = EMPTY; winningLine = [];
  for (let x=3; x<=6; x++) { board[7][x] = BLACK; moves.push({x,y:7,stone:BLACK}); }
  let move = chooseLocalMove(BLACK);
  globalThis.__winningMove = move;

  board = blankBoard(); moves = []; winner = EMPTY; winningLine = [];
  for (let x=3; x<=6; x++) { board[7][x] = WHITE; moves.push({x,y:7,stone:WHITE}); }
  move = chooseLocalMove(BLACK);
  globalThis.__blockingMove = move;
`;

vm.runInNewContext(`${source}\n${tests}`, sandbox, {filename: "app.js"});
assert.equal(sandbox.engineMode, undefined, "top-level lexical state should stay encapsulated");
assert.equal(sandbox.__winningMove.y, 7);
assert.ok([2, 7].includes(sandbox.__winningMove.x), "AI should complete an open four");
assert.equal(sandbox.__blockingMove.y, 7);
assert.ok([2, 7].includes(sandbox.__blockingMove.x), "AI should block an opponent open four");
console.log("mobile local AI tactics OK");
