"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { useEffect, useRef } from "react";

/** Home page motion: smooth scroll plus the scroll reveals. Renders nothing. */
export function HomeMotion() {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = root.current!;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    gsap.registerPlugin(ScrollTrigger);
    const lenis = new Lenis();
    lenis.on("scroll", ScrollTrigger.update);
    const raf = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(raf);
    gsap.ticker.lagSmoothing(0);

    const ctx = gsap.context(() => {
      // Headings tick up out of their line masks as they enter.
      gsap.utils.toArray<HTMLElement>("[data-rise]").forEach((h) => {
        gsap.from(h.querySelectorAll("[data-rise-line]"), {
          yPercent: 105,
          duration: 0.8,
          stagger: 0.06,
          ease: "power3.out",
          scrollTrigger: { trigger: h, start: "top 85%" },
        });
      });

      // Contract note rows print in one after another; the total settles last.
      gsap.from("[data-row]", {
        autoAlpha: 0,
        y: 8,
        duration: 0.35,
        stagger: 0.12,
        ease: "power3.out",
        scrollTrigger: { trigger: "[data-note]", start: "top 70%" },
      });

    }, el.parentElement!);

    return () => {
      ctx.revert();
      gsap.ticker.remove(raf);
      lenis.destroy();
    };
  }, []);

  return <div ref={root} hidden />;
}
