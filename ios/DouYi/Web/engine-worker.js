// SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
// SPDX-License-Identifier: GPL-3.0-only

let engine = null;

self.onmessage = async (event) => {
  const message = event.data || {};
  if (message.type === "init") {
    try {
      importScripts("engine/rapfi-single-simd128.js");
      const engineBase = new URL("engine/", self.location.href).href;
      engine = await self.Rapfi({
        locateFile(name) {
          if (/^rapfi.*\.data$/.test(name)) name = "rapfi.data";
          return engineBase + name;
        },
        onReceiveStdout(line) { self.postMessage({type: "stdout", data: String(line)}); },
        onReceiveStderr(line) { self.postMessage({type: "stderr", data: String(line)}); },
        onExit(code) { self.postMessage({type: "exit", data: code}); },
        setStatus(status) { self.postMessage({type: "status", data: String(status)}); }
      });
      self.postMessage({type: "ready"});
    } catch (error) {
      self.postMessage({type: "error", data: error && error.message ? error.message : String(error)});
    }
  } else if (message.type === "command" && engine) {
    engine.sendCommand(String(message.data));
  }
};
