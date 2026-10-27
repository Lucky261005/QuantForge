"use client";

import dynamic from "next/dynamic";

// react-plotly.js touches `window` at import time, so it must never be part of
// the server-rendered bundle — every chart in the app imports Plot from here.
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default Plot;
