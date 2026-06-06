/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Shared type-only contracts live outside the app dir (packages/contracts).
  transpilePackages: ["@ekip/contracts"],
};

export default nextConfig;
