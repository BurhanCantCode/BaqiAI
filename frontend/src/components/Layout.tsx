import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard, TrendingUp, Briefcase, BarChart3, Bot, Bell, Search, Settings, Brain
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/insights', icon: Brain, label: 'AI Insights' },
  { path: '/invest', icon: TrendingUp, label: 'Invest' },
  { path: '/portfolio', icon: Briefcase, label: 'Portfolio' },
  { path: '/analysis', icon: BarChart3, label: 'Analysis' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background flex font-sans text-foreground">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-screen w-[260px] bg-white border-r border-[#eef2f7] flex flex-col z-50">
        {/* Logo Area */}
        <div className="p-6 mb-2">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <Bot className="w-6 h-6" />
            </div>
            <span className="text-xl font-semibold tracking-tight text-foreground">BAQI AI</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 space-y-1">
          {NAV_ITEMS.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path
            return (
              <Link
                key={path}
                to={path}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group',
                  isActive 
                    ? 'bg-[#f1f5f9] text-[#0f172a] font-medium' 
                    : 'text-[#64748b] hover:bg-[#f8fafc] hover:text-[#0f172a]'
                )}
              >
                <Icon className={cn('w-5 h-5', isActive ? 'text-primary' : 'text-[#94a3b8] group-hover:text-[#64748b]')} />
                <span>{label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="p-4 border-t border-[#eef2f7]">
           <button className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-[#64748b] hover:bg-[#f8fafc] hover:text-[#0f172a] transition-all duration-200">
              <Settings className="w-5 h-5 text-[#94a3b8]" />
              <span>Settings</span>
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-[260px] min-h-screen flex flex-col">
        {/* Header */}
        <header className="h-20 bg-transparent flex items-center justify-between px-8 py-4 sticky top-0 z-40 backdrop-blur-sm">
          {/* Breadcrumb / Title Context - mostly static for now or derived from path */}
          <div className="flex flex-col justify-center">
             {/* Dynamic Title could go here */}
          </div>

          <div className="flex items-center gap-4">
             {/* Search */}
             <div className="relative hidden md:block">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#94a3b8]" />
                <input 
                  type="text" 
                  placeholder="Search..." 
                  className="pl-10 pr-4 py-2 rounded-full bg-white border border-[#e2e8f0] text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 w-64 shadow-sm"
                />
             </div>

             {/* Notifications */}
             <button className="w-10 h-10 rounded-full bg-white border border-[#e2e8f0] flex items-center justify-center text-[#64748b] shadow-sm hover:text-primary transition-colors relative">
                <Bell className="w-5 h-5" />
                <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-red-500 border-2 border-white"></span>
             </button>

             {/* User Profile */}
             <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-blue-400 p-0.5 shadow-md cursor-pointer">
                <div className="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
                   <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
                </div>
             </div>
          </div>
        </header>

        {/* Content Scrollable Area */}
        <div className="flex-1 px-8 pb-8 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
