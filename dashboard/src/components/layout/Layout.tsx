import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ToastContainer } from '../ui/Toast';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <div className="flex flex-col h-screen w-screen bg-bg-light dark:bg-bg-dark overflow-hidden">
      {/* Top Header */}
      <Header onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)} menuOpen={mobileMenuOpen} />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Navigation Sidebar - Desktop (shown inline) vs Mobile (drawer overlay) */}
        <div className={`
          absolute md:relative z-40 h-full transition-transform duration-300 md:translate-x-0 bg-bg-light dark:bg-bg-dark
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}>
          <Sidebar onItemClick={() => setMobileMenuOpen(false)} />
        </div>

        {/* Mobile menu backdrop */}
        {mobileMenuOpen && (
          <div 
            onClick={() => setMobileMenuOpen(false)} 
            className="absolute inset-0 bg-black/40 z-30 md:hidden animate-fade-in"
          />
        )}

        {/* Core Content Window */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 bg-bg-light dark:bg-bg-dark w-full">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>

      {/* Global alert notifications */}
      <ToastContainer />
    </div>
  );
};
