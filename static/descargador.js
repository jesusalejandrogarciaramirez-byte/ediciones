/* Una cola por pestaña. Solo un PDF se carga en el navegador a la vez. */
(() => {
  if (window.__edicionesDownloads) return;

  const sent = new Set();
  const states = new Map();
  let pending = [];
  let wanted = new Set();
  let running = false;
  let active = null;
  const storageKey = (id) => `ediciones_descargado_${id}`;
  const pause = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

  function wasSent(id) {
    if (sent.has(id)) return true;
    try {
      if (window.sessionStorage.getItem(storageKey(id)) === "1") {
        sent.add(id);
        return true;
      }
    } catch (_) {}
    return false;
  }

  async function drain() {
    if (running) return;
    running = true;
    try {
      while (pending.length) {
        const file = pending.shift();
        if (!wanted.has(file.id) || wasSent(file.id)) continue;
        const controller = new AbortController();
        active = { id: file.id, controller };
        let objectUrl = null;
        let blob = null;
        try {
          states.set(file.id, "preparing");
          const url = new URL(file.url, window.location.href);
          if (url.origin !== window.location.origin) {
            throw new Error("La descarga debe proceder de esta aplicación.");
          }
          const response = await window.fetch(url.href, {
            cache: "no-store", credentials: "same-origin", signal: controller.signal
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          blob = await response.blob();
          if (blob.size !== file.size) throw new Error("El archivo recibido está incompleto.");
          if (!(await blob.slice(0, 1024).text()).includes("%PDF-")) {
            throw new Error("La respuesta no contiene el PDF.");
          }
          if (!wanted.has(file.id) || controller.signal.aborted) continue;
          objectUrl = window.URL.createObjectURL(blob);
          const anchor = document.createElement("a");
          anchor.href = objectUrl;
          anchor.download = file.filename;
          anchor.style.display = "none";
          document.body.appendChild(anchor);
          anchor.click();
          anchor.remove();
          // Registrar el envío después de activar la descarga, nunca antes.
          sent.add(file.id);
          try { window.sessionStorage.setItem(storageKey(file.id), "1"); } catch (_) {}
          states.set(file.id, "sent");
          // Dar tiempo al navegador para iniciar el guardado antes de liberar el Blob.
          await pause(1000);
        } catch (error) {
          if (error.name !== "AbortError") {
            states.set(file.id, "error");
            console.warn("No se pudo iniciar la descarga automática:", file.filename, error.message);
          }
        } finally {
          if (objectUrl) window.URL.revokeObjectURL(objectUrl);
          blob = null;
          if (active && active.id === file.id) active = null;
        }
      }
    } finally {
      running = false;
      if (pending.length) void drain();
    }
  }

  window.__edicionesDownloads = {
    enqueue(files) {
      wanted = new Set(files.map((file) => file.id));
      pending = pending.filter((file) => wanted.has(file.id));
      if (active && !wanted.has(active.id)) active.controller.abort();
      for (const file of files) {
        if (wasSent(file.id)) {
          states.set(file.id, "sent");
          continue;
        }
        if ((active && active.id === file.id) || pending.some((item) => item.id === file.id)) continue;
        states.set(file.id, "queued");
        pending.push(file);
      }
      void drain();
    },
    status(ids) {
      return ids.map((id) => wasSent(id) ? "sent" : (states.get(id) || "queued"));
    }
  };
})();
