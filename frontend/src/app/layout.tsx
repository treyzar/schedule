import React from 'react';
import type { Metadata, Viewport } from 'next';
import { AuthProvider } from '@/contexts/AuthContext';
import Header from '@/components/common/Header';
import AuthGuard from '@/components/auth/AuthGuard';
import '../styles/index.css';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export const metadata: Metadata = {
  title: 'SmartScheduler - Умное планирование расписания',
  description: 'Интеллектуальная система планирования расписания с интеграцией Google Calendar и AI помощником',
  icons: {
    icon: [{ url: '/favicon.ico', type: 'image/x-icon' }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body className="min-h-screen bg-background font-body text-foreground antialiased">
        <AuthProvider>
          <div className="flex min-h-screen flex-col">
            <Header />
            <main className="flex-1 pt-[60px]">
              <AuthGuard>
                {children}
              </AuthGuard>
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
