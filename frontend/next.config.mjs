/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // lets a production build run beside a dev server without fighting over .next
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
