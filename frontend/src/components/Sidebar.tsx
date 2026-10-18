import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, PlusCircle, Library, Upload,
  Zap, ChevronRight, Sparkles
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/create', icon: PlusCircle, label: 'Create Listing' },
  { to: '/library', icon: Library, label: 'My Products' },
  { to: '/bulk', icon: Upload, label: 'Bulk Import' },
]

interface SidebarProps {
  collapsed?: boolean
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const { pathname } = useLocation()

  return (
    <aside className={`flex flex-col h-full bg-secondary border-r border-subtle transition-all duration-300 ${collapsed ? 'w-16' : 'w-60'}`}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-subtle">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-400 flex items-center justify-center flex-shrink-0 glow-purple">
          <Zap size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div>
            <span className="font-bold text-sm text-primary">SellerBoost</span>
            <span className="gradient-text font-bold text-sm"> AI</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {!collapsed && (
          <p className="text-xs font-semibold text-muted uppercase tracking-widest px-3 py-2">
            Navigation
          </p>
        )}
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => {
          const isActive = pathname === to || (to !== '/' && pathname.startsWith(to))
          return (
            <Link
              key={to}
              to={to}
              className={`nav-item ${isActive ? 'active' : ''} ${collapsed ? 'justify-center px-0' : ''}`}
              title={collapsed ? label : undefined}
            >
              <Icon size={17} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
              {!collapsed && isActive && <ChevronRight size={13} className="ml-auto opacity-60" />}
            </Link>
          )
        })}
      </nav>

      {/* Bottom badge */}
      {!collapsed && (
        <div className="p-3 border-t border-subtle">
          <div className="rounded-lg p-3 bg-gradient-to-br from-purple-600/10 to-purple-400/5 border border-purple-500/20">
            <div className="flex items-center gap-2 mb-1.5">
              <Sparkles size={13} className="text-purple-400" />
              <span className="text-xs font-semibold text-purple-300">Open-Weight AI</span>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Powered by Meta Llama 3.1 via Backboard
            </p>
          </div>
        </div>
      )}
    </aside>
  )
}
