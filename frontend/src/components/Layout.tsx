import React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { ModelStatusBadge } from './ModelStatusBadge'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'

export const Layout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-primary">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex flex-shrink-0">
        <Sidebar />
      </div>

      {/* Mobile Sidebar overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div className={`fixed inset-y-0 left-0 z-50 md:hidden transition-transform duration-300 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar />
      </div>

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top header */}
        <header className="flex items-center justify-between px-4 md:px-6 py-3.5 border-b border-subtle bg-secondary/80 backdrop-blur-md flex-shrink-0">
          <button
            className="md:hidden btn-ghost p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="hidden md:block" /> {/* spacer */}
          <ModelStatusBadge />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
