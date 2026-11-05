import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  /* config options here */
  // diabled eslint in build
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'pub-d585d94603de45d289b5d891f8c5d079.r2.dev',
      },
      {
        protocol: 'https',
        hostname: 'chart.googleapis.com',
      },
      {
        protocol: 'https',
        hostname: 'example.com',
      },
    ],
  },

  async rewrites() {
    return [
      {
        source: '/api/graphql/:path*',
        destination: `${process.env.INTERNAL_GRAPHQL_URL ?? 'http://gateway:4000'}/:path*`,
      },
      {
        source: '/api/logic/:path*',
        destination: `${process.env.BUSINESS_URL ?? 'http://backend:5000/api'}/:path*`,
      },
      {
        source: '/api/chat/:path*',
        destination: `${process.env.INTERNAL_CHAT_URL ?? 'http://chatbot:8080/api/v1/chat'}/:path*`,
      },
    ]
  },

  // CONFIGURACIÓN PARA LOAD BALANCER
  // Exponer variables de entorno al navegador
  env: {
    NEXT_PUBLIC_INSTANCE_ID:
      process.env.INSTANCE_ID ??
      process.env.NEXT_PUBLIC_INSTANCE_ID ??
      'unknown',
  },

  // Configuración de runtime para acceso desde el cliente
  publicRuntimeConfig: {
    instanceId:
      process.env.INSTANCE_ID ??
      process.env.NEXT_PUBLIC_INSTANCE_ID ??
      'unknown',
    nodeEnv: process.env.NODE_ENV || 'development',
  },
}

export default nextConfig
