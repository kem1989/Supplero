import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from './contexts/AuthContext';
import { TracingProvider } from './contexts/TracingContext';

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Supplero - AI-Powered Procurement & Supplier Risk Management',
  description: 'Intelligent procurement and supplier risk management platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <TracingProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </TracingProvider>
      </body>
    </html>
  );
} 