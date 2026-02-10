import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { baqiApi } from '@/api/client'
import type { User, SpendingAnalysis, PortfolioData } from '@/types'

interface AppState {
  userId: number
  user: User | null
  analysis: SpendingAnalysis | null
  portfolio: PortfolioData | null
  loading: boolean
  refreshAll: () => Promise<void>
  refreshPortfolio: () => Promise<void>
  setUserId: (id: number) => void
}

const AppContext = createContext<AppState | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState(() =>
    Number(localStorage.getItem('baqi_user_id') || '0')
  )
  const [user, setUser] = useState<User | null>(null)
  const [analysis, setAnalysis] = useState<SpendingAnalysis | null>(null)
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [loading, setLoading] = useState(true)

  const setUserId = useCallback((id: number) => {
    localStorage.setItem('baqi_user_id', String(id))
    setUserIdState(id)
  }, [])

  const refreshAll = useCallback(async () => {
    if (!userId) { setLoading(false); return }
    setLoading(true)
    try {
      const [profileRes, analysisRes] = await Promise.all([
        baqiApi.getProfile(userId),
        baqiApi.getAnalysis(userId),
      ])
      setUser(profileRes.data)
      setAnalysis(analysisRes.data)
    } catch {
      // User might not exist yet
    }
    // Portfolio is optional — may not exist yet
    try {
      const portfolioRes = await baqiApi.getPortfolio(userId)
      setPortfolio(portfolioRes.data)
    } catch {
      setPortfolio(null)
    }
    setLoading(false)
  }, [userId])

  const refreshPortfolio = useCallback(async () => {
    if (!userId) return
    try {
      const res = await baqiApi.getPortfolio(userId)
      setPortfolio(res.data)
    } catch {
      // Portfolio may not exist
    }
  }, [userId])

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  return (
    <AppContext.Provider value={{
      userId, user, analysis, portfolio, loading,
      refreshAll, refreshPortfolio, setUserId,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
