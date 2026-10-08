// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../android/app/src/main/assets/app.js", import.meta.url), "utf8");

function harness(rapfi = false) {
  const timers = new Map(), elements = new Map(), workers = [];
  let nextId = 0, now = 0;
  const context2d = new Proxy({}, {get: (target, key) => target[key] ?? (() => ({addColorStop(){}}))});
  const element = () => ({classList: {add(){}, remove(){}, toggle(){}},
    getContext: () => context2d, getBoundingClientRect: () => ({width:390,left:0,top:0}),
    addEventListener(type, fn) { this[type] = fn; }, textContent:"", hidden:false});
  const sandbox = vm.createContext({console, devicePixelRatio:2,
    document: {getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); }},
    window: {addEventListener(){}},
    Worker: class {
      constructor() { if (!rapfi) throw Error("WASM unavailable"); workers.push(this); this.commands=[]; }
      postMessage(message) { this.commands.push(message); }
      terminate() { this.terminated=true; }
    },
    setTimeout(fn, delay) { const id=++nextId; timers.set(id,{fn,at:now+delay}); return id; },
    clearTimeout(id) { timers.delete(id); }, setInterval(){},
  });
  const run = code => vm.runInContext(code, sandbox);
  run(source);
  function advance(ms) {
    const until = now + ms;
    for (let count=0;count<10000;count++) {
      const pending = [...timers].filter(([,t])=>t.at<=until).sort((a,b)=>a[1].at-b[1].at)[0];
      if (!pending) { now=until; return; }
      const [id,timer]=pending; timers.delete(id); now=timer.at; timer.fn();
    }
    throw Error("timer loop did not terminate");
  }
  const send = (worker,type,data) => worker.onmessage({data:{type,data}});
  return {run,advance,elements,workers,send,timers};
}

{
  const h=harness();
  h.run('selectMode("ai"); setAiSpeed("500")');
  h.advance(5000);
  assert.ok(h.run("moves.length")>=2, "both AIs should play automatically");
  assert.equal(h.run("moves.every((m,i)=>m.stone===(i%2?WHITE:BLACK))"),true);
  h.run("toggleAiPause()");
  const count=h.run("moves.length"); h.advance(10000);
  assert.equal(h.run("moves.length"),count,"pause must stop timers and in-flight local search");
  h.run("stepAi(); stepAi()"); h.advance(1000);
  assert.equal(h.run("moves.length"),count+1,"one step must place exactly one stone");
  assert.equal(h.run("aiPaused"),true);
  h.run("undo()"); h.advance(5000);
  assert.equal(h.run("moves.length"),count);
  assert.equal(h.run("aiPaused"),true,"undo should pause for study");
  h.run("toggleAiPause()"); h.advance(200000);
  assert.equal(h.run("gameFinished()"),true,"AI game must finish");
  const finished=h.run("moves.length"); h.advance(10000);
  assert.equal(h.run("moves.length"),finished,"no moves after the game ends");
  assert.equal(h.run("new Set(moves.map(m=>`${m.x},${m.y}`)).size===moves.length"),true);
  assert.equal(h.elements.get("pauseButton").disabled,true);
  assert.match(h.elements.get("moveList").textContent,/1\. ● H8/);
}

{
  const h=harness();
  h.run('selectMode("ai")'); h.advance(1200); // local calculation has started
  h.run('newGame(); toggleAiPause()'); h.advance(5000);
  assert.equal(h.run("moves.length"),0,"old local result must not land on a restarted board");
  h.run('selectMode("double")'); h.advance(5000);
  assert.equal(h.run("moves.length"),0);
  h.run("place(4,4); place(5,5)"); h.advance(5000);
  assert.equal(h.run("moves.length"),2,"double mode stays manual");
  h.run('selectMode("single"); selectColor(WHITE)'); h.advance(1000);
  assert.equal(h.run("moves.length"),1,"single white still gets a black AI opening");
}

{
  const h=harness(true), old=h.workers[0];
  h.send(old,"ready"); h.send(old,"stdout","OK");
  h.run('selectMode("ai")'); h.advance(1200);
  assert.equal(h.run("thinking"),true);
  assert.equal(old.commands.at(-1).data,"YXNBEST 1");
  h.send(old,"stdout","7,7"); h.advance(1200);
  h.send(old,"stdout","7,8");
  assert.equal(h.run("moves.length"),2,"Rapfi must search for both colors");
  assert.ok(old.commands.some(m=>m.data==="YXBOARD 7,7,1 DONE"));
  h.advance(1200); h.run("toggleAiPause()");
  assert.equal(old.terminated,true);
  h.send(old,"stdout","8,8");
  assert.equal(h.run("moves.length"),2,"retired worker results must be ignored");
  const next=h.workers.at(-1); h.send(next,"ready"); h.send(next,"stdout","OK");
  assert.equal(h.elements.get("stepButton").disabled,false,"ready worker must enable paused stepping");
  h.advance(10000); assert.equal(h.run("moves.length"),2);
  h.run("stepAi()"); h.send(next,"stdout","8,8"); h.advance(10000);
  assert.equal(h.run("moves.length"),3,"Rapfi single step must stay paused");
  h.run("toggleAiPause()"); h.advance(1200);
  h.send(next,"error","test failure"); h.advance(5000);
  assert.equal(h.run("engineMode"),"local");
  assert.ok(h.run("moves.length")>3,"fallback AI should continue both colors");
}

{
  const h=harness();
  h.run('selectMode("ai"); toggleAiPause(); board=blankBoard(); moves=[]; for(let y=0;y<SIZE;y++)for(let x=0;x<SIZE;x++){if(x===14&&y===14)continue;const stone=(x+2*y)%4<2?BLACK:WHITE;board[y][x]=stone;moves.push({x,y,stone});} place(14,14)');
  assert.equal(h.run("winner"),0);
  assert.equal(h.run("gameFinished()"),true);
  assert.equal(h.elements.get("statusTitle").textContent,"和棋");
}

console.log("mobile spectator autoplay, controls, cancellation, Rapfi handoff and draw OK");
