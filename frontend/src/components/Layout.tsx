import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard, TrendingUp, Briefcase, BarChart3, Bot, Bell, Search, Settings, Brain,
  FileSpreadsheet, Send, MessageSquare
} from 'lucide-react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import UploadCSV from '@/components/UploadCSV'
import { useApp } from '@/context/AppContext'

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/insights', icon: Brain, label: 'AI Insights' },
  { path: '/invest', icon: TrendingUp, label: 'Invest' },
  { path: '/portfolio', icon: Briefcase, label: 'Portfolio' },
  { path: '/analysis', icon: BarChart3, label: 'Analysis' },
  { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
  { path: '/telegram', icon: Send, label: 'Telegram' },
  { path: '/admin', icon: Settings, label: 'Admin' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const { userId, switchDataSource } = useApp()
  const [showUploadModal, setShowUploadModal] = useState(false)

  const handleUploadComplete = async (uploadData: any) => {
    setShowUploadModal(false)
    const uploadUserId = uploadData.user_id || 1
    switchDataSource('csv', uploadUserId)
  }

  return (
    <div className="min-h-screen bg-background flex font-sans text-foreground">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-screen w-[240px] bg-[#1B211A] border-r border-[#333D30]/50 flex flex-col z-50">
        {/* Logo Area */}
        <div className="px-5 py-6 mb-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#A3B570]/15 flex items-center justify-center">
              <Bot className="w-5 h-5 text-[#A3B570]" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-[#E8E4DA]">
              BAQI AI
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 space-y-0.5">
          {NAV_ITEMS.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path
            return (
              <Link
                key={path}
                to={path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative',
                  isActive
                    ? 'text-[#E8E4DA]'
                    : 'text-[#8A8878] hover:text-[#D4C9A8]'
                )}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full bg-[#A3B570] shadow-[0_0_8px_rgba(163,181,112,0.5)]" />
                )}
                {isActive && (
                  <div className="absolute inset-0 rounded-lg bg-[#A3B570]/8" />
                )}
                <Icon className={cn(
                  'w-[18px] h-[18px] relative z-10 transition-colors',
                  isActive ? 'text-[#A3B570]' : 'text-[#8A8878] group-hover:text-[#A3B570]/70'
                )} />
                <span className="text-sm relative z-10">{label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="px-3 py-4 border-t border-[#333D30]/50 space-y-1">
          {/* Upload CSV — always accessible */}
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-[#A3B570] hover:bg-[#A3B570]/10 transition-all duration-200 group"
          >
            <FileSpreadsheet className="w-[18px] h-[18px] group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium">Upload CSV</span>
          </button>

          <button className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-[#8A8878] hover:text-[#D4C9A8] transition-all duration-200">
            <Settings className="w-[18px] h-[18px]" />
            <span className="text-sm">Settings</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-[240px] min-h-screen flex flex-col">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-8 sticky top-0 z-40 glass-surface border-b border-[#333D30]/30">
          <div />

          <div className="flex items-center gap-3">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8878]" />
              <input
                type="text"
                placeholder="Search..."
                className="pl-9 pr-4 py-2 rounded-lg bg-[#232B22] border border-[#333D30] text-sm text-[#E8E4DA] placeholder:text-[#8A8878] focus:outline-none focus:ring-1 focus:ring-[#A3B570]/30 w-56 transition-all"
              />
            </div>

            <button className="w-9 h-9 rounded-lg bg-[#232B22] border border-[#333D30] flex items-center justify-center text-[#8A8878] hover:text-[#A3B570] transition-colors relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#C65D4A]" />
            </button>

            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#A3B570] to-[#6B7D3A] p-[2px] cursor-pointer">
              <div className="w-full h-full rounded-[6px] bg-[#232B22] flex items-center justify-center overflow-hidden">
                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" className="w-full h-full" />
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 px-8 py-6 overflow-auto">
          {children}
        </div>
      </main>

      {/* Upload CSV Modal — accessible from any page */}
      <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-card border-border">
          <UploadCSV
            userId={userId || undefined}
            onUploadComplete={handleUploadComplete}
            onCancel={() => setShowUploadModal(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
