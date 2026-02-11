import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { baqiApi, type DataSource } from '@/api/client'
import type { User, SpendingAnalysis, PortfolioData, InsightsResponse, RecommendationResult } from '@/types'

type InvestPhase = 'idle' | 'agents' | 'loading' | 'result' | 'error'

interface AppState {
  userId: number
  user: User | null
  analysis: SpendingAnalysis | null
  portfolio: PortfolioData | null
  insights: InsightsResponse | null
  insightsLoading: boolean
  insightsError: string | null
  loading: boolean
  dataSource: DataSource | null
  refreshAll: () => Promise<void>
  refreshPortfolio: () => Promise<void>
  fetchInsights: () => Promise<void>
  setUserId: (id: number) => void
  switchDataSource: (source: DataSource, newUserId?: number) => void
  // Invest page state (persisted across navigation)
  investPhase: InvestPhase
  setInvestPhase: (phase: InvestPhase) => void
  investResult: RecommendationResult | null
  setInvestResult: (result: RecommendationResult | null) => void
  investError: string
  setInvestError: (error: string) => void
  invested: boolean
  setInvested: (invested: boolean) => void
}

const AppContext = createContext<AppState | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState(() =>
    Number(localStorage.getItem('baqi_user_id') || '0')
  )
  const [dataSource, setDataSource] = useState<DataSource | null>(() =>
    (localStorage.getItem('baqi_data_source') as DataSource) || null
  )
  const [user, setUser] = useState<User | null>(null)
  const [analysis, setAnalysis] = useState<SpendingAnalysis | null>(null)
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [insights, setInsights] = useState<InsightsResponse | null>(null)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [insightsError, setInsightsError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Invest page state — lives in context so it survives navigation
  const [investPhase, setInvestPhase] = useState<InvestPhase>('idle')
  const [investResult, setInvestResult] = useState<RecommendationResult | null>(null)
  const [investError, setInvestError] = useState('')
  const [invested, setInvested] = useState(false)

  const setUserId = useCallback((id: number) => {
    localStorage.setItem('baqi_user_id', String(id))
    setUserIdState(id)
  }, [])

  const switchDataSource = useCallback((source: DataSource, newUserId?: number) => {
    localStorage.setItem('baqi_data_source', source)
    setDataSource(source)
    // Clear stale data from previous source
    setAnalysis(null)
    setInsights(null)
    setInsightsError(null)
    setPortfolio(null)
    setUser(null)
    // Reset invest state for new data source
    setInvestPhase('idle')
    setInvestResult(null)
    setInvestError('')
    setInvested(false)
    if (newUserId !== undefined) {
      setUserId(newUserId)
    }
  }, [setUserId])

  const refreshAll = useCallback(async () => {
    if (!dataSource) {
      setLoading(false)
      return
    }

    setLoading(true)
    const id = userId || 1

    try {
      const analysisRes = await baqiApi.getAnalysis(id, dataSource)
      setAnalysis(analysisRes.data)
    } catch {
      // No data available for this source
    }

    // Profile + Portfolio only relevant for supabase users
    if (userId && dataSource === 'supabase') {
      try {
        const profileRes = await baqiApi.getProfile(userId)
        setUser(profileRes.data)
      } catch {
        // User might not exist
      }
      try {
        const portfolioRes = await baqiApi.getPortfolio(userId)
        setPortfolio(portfolioRes.data)
      } catch {
        setPortfolio(null)
      }
    }

    setLoading(false)
  }, [userId, dataSource])

  const refreshPortfolio = useCallback(async () => {
    if (!userId) return
    try {
      const res = await baqiApi.getPortfolio(userId)
      setPortfolio(res.data)
    } catch {
      // Portfolio may not exist
    }
  }, [userId])

  const fetchInsights = useCallback(async () => {
    const id = userId || 1
    if (!dataSource) return
    setInsightsLoading(true)
    setInsightsError(null)
    try {
      const res = await baqiApi.getInsights(id, dataSource)
      setInsights(res.data)
    } catch (err: any) {
      const msg = err?.response?.data?.detail
        || (err?.code === 'ECONNABORTED' ? 'Request timed out — the AI is processing a large dataset. Please try again.' : null)
        || err?.message
        || 'Failed to generate insights. Please try again.'
      setInsightsError(msg)
    } finally {
      setInsightsLoading(false)
    }
  }, [userId, dataSource])

  useEffect(() => {
    if (dataSource) {
      refreshAll()
    }
  }, [refreshAll, dataSource])

  return (
    <AppContext.Provider value={{
      userId, user, analysis, portfolio, insights, insightsLoading, insightsError, loading,
      dataSource, refreshAll, refreshPortfolio, fetchInsights, setUserId, switchDataSource,
      investPhase, setInvestPhase, investResult, setInvestResult,
      investError, setInvestError, invested, setInvested,
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
