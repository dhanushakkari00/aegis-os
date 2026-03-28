import type { NextConfig } from "next";
import path from "node:path";

const publicApiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
const internalApiOrigin =
  (process.env.INTERNAL_API_ORIGIN?.trim() || "http://127.0.0.1:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, ".."),
  experimental: {
    optimizePackageImports: ["lucide-react"]
  },
  async rewrites() {
    if (publicApiBase) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${internalApiOrigin}/api/:path*`
      }
    ];
  }
};

export default nextConfig;
