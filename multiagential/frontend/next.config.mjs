/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  env: {
    // Make API URL available to all components
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4465',
  },
};

export default nextConfig;
