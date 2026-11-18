// the small animations used across the app
// rules (from the design-motion-principles skill, "restraint and speed" for a booking tool):
//  - only transform, opacity and filter move, never width or height
//  - short: about 0.2 s, springs with no bounce
//  - things people do many times a day (page changes, filters) stay quick or do not animate
//  - <MotionConfig reducedMotion="user"> in App.jsx turns all of it off when Windows/Linux asks for less motion
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion, animate } from "motion/react";
import mojs from "@mojs/core";

// the spring we use everywhere: smooth stop, no overshoot
export const SPRING = { type: "spring", duration: 0.3, bounce: 0 };

// a page or panel comes into focus: small lift and fade
// (no blur: pages change many times a day and blurred text is slower to read)
export function PageEnter(props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", duration: 0.2, bounce: 0 }}
      style={props.style}
    >
      {props.children}
    </motion.div>
  );
}

// a list where the items come in one after the other, only the first 8 wait
// (after that the stagger would only slow people down)
export function StaggerItem(props) {
  let index = props.index || 0;
  if (index > 7) {
    index = 7;
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", duration: 0.3, bounce: 0, delay: index * 0.03 }}
      style={props.style}
    >
      {props.children}
    </motion.div>
  );
}

// the seats bar: grows with scaleX from the left (no width animation)
export function SeatMeter(props) {
  let ratio = 0;
  if (props.total > 0) {
    ratio = (props.total - props.remaining) / props.total;
  }
  if (ratio < 0) {
    ratio = 0;
  }
  if (ratio > 1) {
    ratio = 1;
  }
  let color = "#1677ff";
  if (ratio >= 0.9) {
    color = "#d97706";
  }
  return (
    <div style={{ height: 6, borderRadius: 100, background: "rgba(0,0,0,.06)", overflow: "hidden" }}>
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: ratio }}
        transition={{ type: "spring", duration: 0.45, bounce: 0 }}
        style={{ height: "100%", background: color, transformOrigin: "left center" }}
      />
    </div>
  );
}

// a number that counts to its new value (used for totals when the guests change)
export function CountUp(props) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(props.value);
  const last = useRef(props.value);

  useEffect(
    function () {
      if (reduce) {
        setShown(props.value);
        last.current = props.value;
        return undefined;
      }
      const controls = animate(last.current, props.value, {
        duration: 0.25,
        ease: [0.23, 1, 0.32, 1],
        onUpdate: function (v) {
          setShown(v);
        },
      });
      last.current = props.value;
      return function () {
        controls.stop();
      };
    },
    [props.value, reduce]
  );

  return <span style={{ fontVariantNumeric: "tabular-nums" }}>{props.format(shown)}</span>;
}

// a short side shake for a refused action (two small moves, 4px)
export function Shake(props) {
  return (
    <motion.div
      key={props.trigger}
      animate={props.trigger ? { x: [0, -4, 4, -3, 3, 0] } : { x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {props.children}
    </motion.div>
  );
}

// one burst of small dots, only for "booking confirmed" (a rare, happy moment)
export function Burst(props) {
  const holder = useRef(null);
  const reduce = useReducedMotion();

  useEffect(
    function () {
      if (!props.play || reduce || !holder.current) {
        return undefined;
      }
      const burst = new mojs.Burst({
        parent: holder.current,
        left: "50%",
        top: "50%",
        radius: { 16: 56 },
        count: 10,
        children: {
          shape: "circle",
          radius: { 5: 0 },
          fill: ["#1677ff", "#16a34a", "#fadb14"],
          duration: 650,
          easing: "quad.out",
        },
      });
      burst.play();
      return function () {
        burst.stop();
        if (burst.el && burst.el.parentNode) {
          burst.el.parentNode.removeChild(burst.el);
        }
      };
    },
    [props.play, reduce]
  );

  return (
    <div ref={holder} style={{ position: "relative", display: "inline-block" }}>
      {props.children}
    </div>
  );
}
