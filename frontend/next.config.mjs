/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // lets a production build run beside a dev server without fighting over .next
  distDir: process.env.NEXT_DIST_DIR || ".next",
  poweredByHeader: false,
  // Baseline security headers for every page. A Content-Security-Policy is not set here:
  // Plotly, GSAP and Next's inline scripts need a policy tested against a real deployment.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
