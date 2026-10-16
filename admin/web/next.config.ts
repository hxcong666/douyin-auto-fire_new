import type { NextConfig } from "next";

// 静态导出：构建产物由 Python 后端托管，服务器上无需运行 Node
const config: NextConfig = {
  output: "export",
  trailingSlash: false,
  images: { unoptimized: true },
  poweredByHeader: false,
  // 开发模式下把 /api 转发到本机后端（静态导出时不生效）
  ...(process.env.NODE_ENV === "development" && {
    rewrites: async () => [{ source: "/api/:path*", destination: "http://127.0.0.1:8090/api/:path*" }],
  }),
};

export default config;
