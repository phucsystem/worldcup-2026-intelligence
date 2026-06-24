"use client";

import { useState } from "react";

interface Props {
  fixtureId: number;
  label?: string;
  shareTitle?: string;
}

type Status = "idle" | "working" | "copied" | "shared" | "downloaded" | "error";

const MESSAGES: Record<Status, string> = {
  idle: "",
  working: "Generating…",
  copied: "Image copied — paste it to a friend",
  shared: "Shared",
  downloaded: "Image downloaded",
  error: "Couldn't share — try again",
};

function downloadBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Desktop-first share: copy the server-rendered PNG to the clipboard (the
// ClipboardItem is built synchronously from the fetch promise so Safari keeps
// the user-activation), then fall back to the native share sheet, then download.
export default function ShareResultButton({ fixtureId, label = "Share result", shareTitle = "World Cup 2026" }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const url = `/match/${fixtureId}/share-image`;
  const fileName = `wc2026-match-${fixtureId}.png`;

  async function handleClick() {
    setStatus("working");

    // One fetch shared by both paths. Built before clipboard.write so the
    // ClipboardItem receives a promise synchronously (keeps Safari's
    // user-activation), and reused by the share/download fallback.
    const blobPromise = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`share-image ${r.status}`);
      return r.blob();
    });

    if (typeof ClipboardItem !== "undefined" && navigator.clipboard?.write) {
      try {
        await navigator.clipboard.write([new ClipboardItem({ "image/png": blobPromise })]);
        setStatus("copied");
        resetSoon();
        return;
      } catch {
        // fall through to share / download, reusing the same in-flight blob
      }
    }

    try {
      const blob = await blobPromise;
      const file = new File([blob], fileName, { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: shareTitle });
        setStatus("shared");
      } else {
        downloadBlob(blob, fileName);
        setStatus("downloaded");
      }
      resetSoon();
    } catch {
      setStatus("error");
      resetSoon();
    }
  }

  function resetSoon() {
    setTimeout(() => setStatus("idle"), 4000);
  }

  return (
    <div className="share-result">
      <button
        type="button"
        className="share-result-btn"
        onClick={handleClick}
        disabled={status === "working"}
        aria-label={label}
      >
        <span aria-hidden="true">↗</span> {label}
      </button>
      <span className="share-result-status" role="status" aria-live="polite">
        {MESSAGES[status]}
      </span>
    </div>
  );
}
