"use client";

import { useState } from "react";

export default function WatchButton() {
  const [watching, setWatching] = useState(false);

  return (
    <button
      type="button"
      onClick={() => setWatching((w) => !w)}
      className={`border px-4 py-2 text-sm font-medium transition-colors ${
        watching
          ? "border-neutral-900 bg-neutral-900 text-white"
          : "border-neutral-300 bg-white text-neutral-900 hover:border-neutral-900"
      }`}
    >
      {watching ? "Watching" : "Watch"}
    </button>
  );
}
