import { useEffect, useRef, useState, type ReactNode } from "react";

interface RevealProps {
  children: ReactNode;
  /** Extra classes for the wrapper. */
  className?: string;
  /** Transition delay in ms, for staggered grids. Keep small. */
  delay?: number;
  as?: "div" | "section" | "li";
}

/**
 * Sparing scroll-triggered reveal: fades content up once when it enters the
 * viewport. Uses IntersectionObserver (no animation library) and never hides
 * content from assistive tech — before reveal the element is visible to
 * screen readers, only visually translated. Honors
 * `prefers-reduced-motion` via the global CSS override.
 */
export default function Reveal({
  children,
  className = "",
  delay = 0,
  as = "div"
}: RevealProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
          }
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const Tag = as;

  return (
    <Tag
      ref={ref as never}
      style={delay > 0 ? { transitionDelay: `${delay}ms` } : undefined}
      className={`transition-all duration-500 ease-out will-change-transform ${
        visible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
      } motion-reduce:translate-y-0 motion-reduce:opacity-100 motion-reduce:transition-none ${className}`}
    >
      {children}
    </Tag>
  );
}
