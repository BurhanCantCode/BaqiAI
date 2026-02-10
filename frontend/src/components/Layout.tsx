import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard, TrendingUp, Briefcase, BarChart3, Bot
} from 'lucide-react'

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/invest', icon: TrendingUp, label: 'Invest' },
  { path: '/portfolio', icon: Briefcase, label: 'Portfolio' },
  { path: '/analysis', icon: BarChart3, label: 'Analysis' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="glass border-b border-border/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center glow-green">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <span className="text-lg font-bold text-gradient">BAQI AI</span>
          </Link>
          <div className="text-xs text-muted-foreground">
            AI-Powered Islamic Investment Assistant
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {children}
      </main>

      {/* Bottom Nav (mobile-first) */}
      <nav className="glass border-t border-border/50 sticky bottom-0 z-50">
        <div className="max-w-7xl mx-auto px-4 flex justify-around">
          {NAV_ITEMS.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path
            return (
              <Link
                key={path}
                to={path}
                className={cn(
                  'flex flex-col items-center gap-1 py-3 px-4 text-xs transition-all',
                  isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                <Icon className={cn('w-5 h-5', isActive && 'drop-shadow-[0_0_6px_#10b981]')} />
                <span>{label}</span>
                {isActive && (
                  <div className="w-1 h-1 rounded-full bg-primary animate-pulse-dot" />
                )}
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
