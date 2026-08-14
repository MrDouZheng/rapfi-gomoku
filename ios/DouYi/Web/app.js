// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

"use strict";

const SIZE = 15;
const EMPTY = 0, BLACK = 1, WHITE = 2;
const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const ui = Object.fromEntries(["engineBadge","singleMode","doubleMode","colorPicker","blackColor","whiteColor","statusKicker","statusTitle","moveCount","timer","undoButton","newButton","toast"].map(id => [id, document.getElementById(id)]));

let board, moves, winner, winningLine, mode = "single", human = BLACK;
let thinking = false, engineReady = false, engineMode = "loading", worker = null;
let startedAt = Date.now(), toastTimer, aiGeneration = 0;

function blankBoard(){ return Array.from({length: SIZE}, () => Array(SIZE).fill(EMPTY)); }
function currentPlayer(){ return moves.length % 2 === 0 ? BLACK : WHITE; }
function opponent(stone){ return stone === BLACK ? WHITE : BLACK; }

function startWorker(){
  aiGeneration++;
  if (worker) worker.terminate();
  worker = null; engineReady = false; engineMode = "loading";
  ui.engineBadge.className = "badge loading";
  ui.engineBadge.innerHTML = "<span></span>引擎加载中";
  try {
    if (typeof Worker !== "function") throw new Error("当前 WebView 不支持 Web Worker");
    worker = new Worker("engine-worker.js");
    worker.onmessage = onEngineMessage;
    worker.onerror = event => activateLocalEngine(event.message || "Rapfi WebAssembly 启动失败");
    worker.postMessage({type:"init"});
  } catch (error) {
    activateLocalEngine(error && error.message ? error.message : String(error));
  }
}

function command(text){ if (worker) worker.postMessage({type:"command", data:text}); }

function onEngineMessage(event){
  const {type, data} = event.data || {};
  if (type === "ready") {
    command(`START ${SIZE}`);
  } else if (type === "stdout") {
    const line = String(data).trim();
    if (line === "OK") {
      engineReady = true; engineMode = "rapfi";
      ui.engineBadge.className = "badge";
      ui.engineBadge.innerHTML = "<span></span>RAPFI 就绪";
      maybeAiMove();
    } else if (thinking && /^\d+\s*,\s*\d+$/.test(line)) {
      const [x,y] = line.split(",").map(Number);
      thinking = false;
      if (inside(x,y) && board[y][x] === EMPTY) place(x,y);
      else engineError("Rapfi 返回了非法落点");
    } else if (/^ERROR/i.test(line)) {
      engineError(line);
    }
  } else if (type === "error" || type === "exit") {
    activateLocalEngine(type === "exit" ? `Rapfi 已退出 (${data})` : data);
  }
}

function activateLocalEngine(reason){
  if (engineMode === "local") return;
  if (worker) worker.terminate();
  worker = null; thinking = false; engineReady = true; engineMode = "local";
  ui.engineBadge.className = "badge local";
  ui.engineBadge.innerHTML = "<span></span>本地 AI 就绪";
  if (reason) showToast("Rapfi 不可用，已切换本地 AI");
  updateStatus(); maybeAiMove();
}

function engineError(message){
  activateLocalEngine(message || "Rapfi 引擎异常");
}

function newGame(restart = false){
  if (thinking || restart) startWorker();
  board = blankBoard(); moves = []; winner = EMPTY; winningLine = [];
  thinking = false; startedAt = Date.now();
  draw(); updateStatus(); maybeAiMove();
}

function place(x,y){
  if (winner || !inside(x,y) || board[y][x] !== EMPTY) return false;
  const stone = currentPlayer();
  board[y][x] = stone; moves.push({x,y,stone});
  winningLine = findLine(x,y,stone);
  if (winningLine.length >= 5) winner = stone;
  draw(); updateStatus();
  if (!winner) maybeAiMove();
  return true;
}

function maybeAiMove(){
  if (mode !== "single" || winner || currentPlayer() === human || thinking || !engineReady) return;
  thinking = true; updateStatus();
  if (engineMode === "local") {
    const generation = aiGeneration;
    setTimeout(() => {
      if (generation !== aiGeneration || !thinking || winner || currentPlayer() === human) return;
      const move = chooseLocalMove(currentPlayer());
      thinking = false;
      if (move) place(move.x, move.y); else updateStatus();
    }, 180);
    return;
  }
  ["INFO RULE 0","INFO THREAD_NUM 1","INFO HASH_SIZE 32768","INFO TIMEOUT_TURN 950","INFO TIMEOUT_MATCH 30000","INFO TIME_LEFT 30000","INFO MAX_DEPTH 22","INFO SHOW_DETAIL 0"].forEach(command);
  const position = moves.map(m => `${m.x},${m.y},${m.stone}`).join(" ");
  command(`YXBOARD${position ? " " + position : ""} DONE`);
  command("YXNBEST 1");
}

function chooseLocalMove(stone){
  if (!moves.length) return {x:7,y:7};
  const rival = opponent(stone), candidates = [];
  let best = -Infinity;
  for (let y=0;y<SIZE;y++) for (let x=0;x<SIZE;x++) {
    if (board[y][x] !== EMPTY || !nearExistingStone(x,y)) continue;
    const attack = tacticalScore(x,y,stone);
    const defense = tacticalScore(x,y,rival);
    const center = 14 - Math.abs(7-x) - Math.abs(7-y);
    const score = attack >= 100000 ? 1000000 : defense >= 100000 ? 900000 : attack * 1.15 + defense + center;
    if (score > best) { best = score; candidates.length = 0; candidates.push({x,y}); }
    else if (score === best) candidates.push({x,y});
  }
  return candidates.length ? candidates[moves.length % candidates.length] : null;
}

function nearExistingStone(x,y){
  for (let dy=-2;dy<=2;dy++) for (let dx=-2;dx<=2;dx++) {
    if ((dx || dy) && inside(x+dx,y+dy) && board[y+dy][x+dx] !== EMPTY) return true;
  }
  return false;
}

function tacticalScore(x,y,stone){
  let score = 0;
  for (const [dx,dy] of [[1,0],[0,1],[1,1],[1,-1]]) {
    let count = 1, open = 0;
    for (const sign of [-1,1]) {
      let step = 1;
      while (inside(x+dx*step*sign,y+dy*step*sign) && board[y+dy*step*sign][x+dx*step*sign] === stone) { count++; step++; }
      if (inside(x+dx*step*sign,y+dy*step*sign) && board[y+dy*step*sign][x+dx*step*sign] === EMPTY) open++;
    }
    if (count >= 5) score += 100000;
    else if (count === 4) score += open === 2 ? 12000 : 4000;
    else if (count === 3) score += open === 2 ? 900 : 240;
    else if (count === 2) score += open === 2 ? 90 : 24;
    else score += open * 3;
  }
  return score;
}

function undo(){
  if (!moves.length) return;
  aiGeneration++;
  const wasThinking = thinking;
  if (wasThinking) startWorker();
  const count = mode === "single" && !wasThinking ? 2 : 1;
  for (let i=0;i<count && moves.length;i++) {
    const move = moves.pop(); board[move.y][move.x] = EMPTY;
  }
  winner = EMPTY; winningLine = []; thinking = false;
  draw(); updateStatus(); maybeAiMove();
}

function findLine(x,y,stone){
  for (const [dx,dy] of [[1,0],[0,1],[1,1],[1,-1]]) {
    const line = [[x,y]];
    for (let s=1; inside(x-dx*s,y-dy*s) && board[y-dy*s][x-dx*s]===stone; s++) line.unshift([x-dx*s,y-dy*s]);
    for (let s=1; inside(x+dx*s,y+dy*s) && board[y+dy*s][x+dx*s]===stone; s++) line.push([x+dx*s,y+dy*s]);
    if (line.length >= 5) return line;
  }
  return [];
}

function inside(x,y){ return x>=0 && x<SIZE && y>=0 && y<SIZE; }

function draw(){
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(devicePixelRatio || 1, 3);
  const pixels = Math.max(260, Math.floor(rect.width * dpr));
  if (canvas.width !== pixels || canvas.height !== pixels) { canvas.width = pixels; canvas.height = pixels; }
  const scale = pixels / 500, margin = 38*scale, cell = (pixels-margin*2)/(SIZE-1);
  const gradient = ctx.createLinearGradient(0,0,pixels,pixels);
  gradient.addColorStop(0,"#e1b469"); gradient.addColorStop(1,"#bd7f38");
  ctx.fillStyle=gradient; ctx.fillRect(0,0,pixels,pixels);
  ctx.strokeStyle="#6a461f"; ctx.lineWidth=Math.max(1,dpr*.65);
  for(let i=0;i<SIZE;i++){ const p=margin+i*cell; ctx.beginPath();ctx.moveTo(margin,p);ctx.lineTo(pixels-margin,p);ctx.stroke();ctx.beginPath();ctx.moveTo(p,margin);ctx.lineTo(p,pixels-margin);ctx.stroke(); }
  ctx.fillStyle="#68451f";
  for(const [x,y] of [[3,3],[11,3],[7,7],[3,11],[11,11]]){ctx.beginPath();ctx.arc(margin+x*cell,margin+y*cell,3.2*scale,0,Math.PI*2);ctx.fill();}
  ctx.font=`600 ${10*scale}px sans-serif`;ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillStyle="#70491f";
  for(let i=0;i<SIZE;i++){ctx.fillText(String.fromCharCode(65+i),margin+i*cell,16*scale);ctx.fillText(String(SIZE-i),16*scale,margin+i*cell);}
  moves.forEach((m,index)=>drawStone(m,index,margin,cell,scale));
  if(winningLine.length){const a=winningLine[0],b=winningLine[winningLine.length-1];ctx.strokeStyle="#e65347";ctx.lineWidth=4*scale;ctx.lineCap="round";ctx.beginPath();ctx.moveTo(margin+a[0]*cell,margin+a[1]*cell);ctx.lineTo(margin+b[0]*cell,margin+b[1]*cell);ctx.stroke();}
}

function drawStone(move,index,margin,cell,scale){
  const x=margin+move.x*cell,y=margin+move.y*cell,r=cell*.42;
  ctx.save();ctx.shadowColor="#4b2d16aa";ctx.shadowBlur=3*scale;ctx.shadowOffsetY=2*scale;
  const g=ctx.createRadialGradient(x-r*.35,y-r*.4,r*.08,x,y,r);
  if(move.stone===BLACK){g.addColorStop(0,"#55595c");g.addColorStop(.3,"#242729");g.addColorStop(1,"#050607");}else{g.addColorStop(0,"#fff");g.addColorStop(.35,"#f2efe8");g.addColorStop(1,"#bab9b5");}
  ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.restore();
  if(index===moves.length-1){ctx.fillStyle="#e65347";ctx.fillRect(x-2.5*scale,y-2.5*scale,5*scale,5*scale);}
}

function updateStatus(){
  ui.moveCount.textContent=String(moves.length);
  if(winner){const name=winner===BLACK?"黑方":"白方";ui.statusTitle.textContent=`${name}获胜`;ui.statusKicker.textContent="五子连珠 · 对局结束";}
  else if(thinking){ui.statusTitle.textContent=engineMode==="rapfi"?"Rapfi 思考中":"本地 AI 思考中";ui.statusKicker.textContent="正在计算最佳落点…";}
  else{const name=currentPlayer()===BLACK?"黑方":"白方";ui.statusTitle.textContent=`${name}落子`;ui.statusKicker.textContent=mode==="double"?"本地双人对战":currentPlayer()===human?"轮到你了":"等待 Rapfi";}
}

function selectMode(next){mode=next;ui.singleMode.classList.toggle("selected",mode==="single");ui.doubleMode.classList.toggle("selected",mode==="double");ui.colorPicker.hidden=mode!=="single";newGame(thinking);}
function selectColor(next){human=next;ui.blackColor.classList.toggle("selected",human===BLACK);ui.whiteColor.classList.toggle("selected",human===WHITE);newGame(thinking);}
function showToast(text){clearTimeout(toastTimer);ui.toast.textContent=text;ui.toast.classList.add("show");toastTimer=setTimeout(()=>ui.toast.classList.remove("show"),2600);}

canvas.addEventListener("click",event=>{if(thinking||winner||(mode==="single"&&currentPlayer()!==human))return;const rect=canvas.getBoundingClientRect(),margin=38,cell=(rect.width-margin*2)/(SIZE-1);const x=Math.round((event.clientX-rect.left-margin)/cell),y=Math.round((event.clientY-rect.top-margin)/cell);if(inside(x,y))place(x,y);});
ui.singleMode.onclick=()=>selectMode("single");ui.doubleMode.onclick=()=>selectMode("double");ui.blackColor.onclick=()=>selectColor(BLACK);ui.whiteColor.onclick=()=>selectColor(WHITE);ui.undoButton.onclick=undo;ui.newButton.onclick=()=>newGame(thinking);
window.addEventListener("resize",draw);setInterval(()=>{const seconds=Math.floor((Date.now()-startedAt)/1000);ui.timer.textContent=`${String(Math.floor(seconds/60)).padStart(2,"0")}:${String(seconds%60).padStart(2,"0")}`;},500);

newGame();startWorker();
