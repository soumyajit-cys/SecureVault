import { useEffect, useState } from "react";

const GLYPHS =
  "01abcdef<>[]{}#*+=%@$&!?;:·—";

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

interface ScrambleTextProps {
  /** Plaintext line that scrambles into ciphertext and resolves back. */
  text: string;
  /** Full cycle duration in ms. */
  durationMs?: number;
  className?: string;
}

/**
 * The landing hero's "real" animation: a line of text that dissolves into
 * random ciphertext glyphs and resolves back to plaintext, looping slowly —
 * a visual metaphor for seal/open. Pure React + CSS, no animation library.
 * Static plaintext is rendered when reduced motion is preferred.
 */
export default function ScrambleText({
  text,
  durationMs = 5200,
  className = ""
}: ScrambleTextProps) {
  const [frame, setFrame] = useState(text);
  const [phase, setPhase] = useState<"plain" | "sealing" | "sealed" | "opening">(
    "plain"
  );

  useEffect(() => {
    if (prefersReducedMotion()) {
      setFrame(text);
      return;
    }
    let raf = 0;
    let timeout = 0;
    let cancelled = false;

    const randomize = (revealFrom: "left" | "right", progress: number) => {
      const out = text.split("").map((ch, i) => {
        if (ch === " ") return " ";
        const t = revealFrom === "left" ? i / text.length : 1 - i / text.length;
        if (t < progress) return ch;
        return GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
      });
      setFrame(out.join(""));
    };

    const animate = (
      revealFrom: "left" | "right",
      invert: boolean,
      done: () => void
    ) => {
      const start = performance.now();
      const span = 900;
      const tick = (now: number) => {
        if (cancelled) return;
        const p = Math.min(1, (now - start) / span);
        randomize(revealFrom, invert ? 1 - p : p);
        if (p < 1) raf = requestAnimationFrame(tick);
        else done();
      };
      raf = requestAnimationFrame(tick);
    };

    const cycle = () => {
      if (cancelled) return;
      // plain → sealing (left reveals ciphertext) → sealed hold →
      // opening (right resolves plaintext) → plain hold
      setPhase("sealing");
      animate("left", false, () => {
        if (cancelled) return;
        setPhase("sealed");
        timeout = window.setTimeout(() => {
          if (cancelled) return;
          setPhase("opening");
          animate("right", true, () => {
            if (cancelled) return;
            setPhase("plain");
            timeout = window.setTimeout(
              cycle,
              Math.max(1200, durationMs - 1800 - 1400)
            );
          });
        }, 1400);
      });
    };

    timeout = window.setTimeout(cycle, 1200);
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      window.clearTimeout(timeout);
    };
  }, [text, durationMs]);

  const phaseLabel =
    phase === "plain"
      ? "plaintext"
      : phase === "sealed"
        ? "ciphertext — sealed"
        : phase === "sealing"
          ? "sealing…"
          : "opening…";

  return (
    <div className={className}>
      <p
        aria-live="off"
        className="min-h-[3.5rem] break-all font-mono text-sm leading-7 sm:text-[15px]"
      >
        <span aria-hidden="true">{frame}</span>
        <span className="sr-only">{text}</span>
        <span
          aria-hidden="true"
          className="ml-1 inline-block h-4 w-2 translate-y-[3px] animate-blink bg-current"
        />
      </p>
      <p
        aria-hidden="true"
        className="mt-1 font-mono text-[11px] uppercase tracking-[0.2em] opacity-60"
      >
        {phaseLabel}
      </p>
    </div>
  );
}
