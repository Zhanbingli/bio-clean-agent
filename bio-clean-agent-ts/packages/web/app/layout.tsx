import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Bio Clean Agent',
  description:
    'Intelligent biomedical data cleaning powered by medical standards and evidence-based AI',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col font-sans">
        <Providers>
          {/* Header */}
          <header className="gradient-bg text-white shadow-lg sticky top-0 z-50">
            <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
              <Link
                href="/"
                className="flex items-center gap-2 font-bold text-xl tracking-tight hover:opacity-90 transition-opacity"
              >
                <span className="text-2xl">🧬</span>
                <span>Bio Clean Agent</span>
              </Link>
              <div className="flex items-center gap-1 sm:gap-2">
                <NavLink href="/">Home</NavLink>
                <NavLink href="/jobs">Jobs</NavLink>
                <NavLink href="/knowledge">Knowledge</NavLink>
              </div>
            </nav>
          </header>

          {/* Main */}
          <main className="flex-1">{children}</main>

          {/* Footer */}
          <footer className="bg-white border-t border-gray-100 py-6 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
              <p className="text-sm text-gray-500">
                Bio Clean Agent &mdash; Intelligent Biomedical Data Quality
              </p>
              <p className="text-sm text-gray-400">
                Powered by evidence-based medical standards
              </p>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-lg text-sm font-medium text-white/90 hover:text-white hover:bg-white/15 transition-all duration-150"
    >
      {children}
    </Link>
  );
}
