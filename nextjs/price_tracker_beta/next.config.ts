import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  env: {
    PYTHON_API_URL: process.env.PYTHON_API_URL,
  },
};

export default nextConfig;
