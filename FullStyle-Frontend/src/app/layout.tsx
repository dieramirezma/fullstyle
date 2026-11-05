import type { Metadata } from 'next'
import { Toaster } from '@/components/ui/sonner'
import { Providers } from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'FullStyle',
  description: 'Gestión de sitios de estética y belleza',
  keywords: ['estética', 'belleza', 'peluquería', 'salón de belleza'],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        <Providers>{children}</Providers>
        <Toaster richColors />
      </body>
    </html>
  )
}
