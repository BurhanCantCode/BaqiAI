import { useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import AgentPipeline from '@/components/AgentPipeline'
import { baqiApi } from '@/api/client'
import { formatMoney } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { GlowingBorder } from '@/components/ui/glowing-border'
import { MovingBorderButton } from '@/components/ui/moving-border'
import { Meteors } from '@/components/ui/meteors'
import { AnimatedCounter } from '@/components/ui/animated-counter'
import type { PortfolioAllocation } from '@/types'
import {
  Sparkles, Loader2, CheckCircle2, Moon, TrendingUp,
  ArrowRight, Briefcase, AlertCircle
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export default function Invest() {
  const {
    userId, dataSource, analysis, refreshPortfolio,
    investPhase: phase, setInvestPhase: setPhase,
    investResult: result, setInvestResult: setResult,
    investError: error, setInvestError: setError,
    invested, setInvested,
  } = useApp()

  const cur = analysis?.currency
  const fmt = (v: number) => formatMoney(v, cur)

  const handleGenerate = () => {
    const id = userId || 1
    if (!dataSource) return
    setPhase('agents')
    setResult(null)
    setError('')

    baqiApi.generateRecommendation(id, dataSource)
      .then(res => {
        setResult(res.data)
      })
      .catch(err => {
        setError(err.response?.data?.detail || 'Recommendation failed. Please try again.')
      })
  }

  const handleAgentsDone = useCallback(() => {
    if (result) {
      setPhase('result')
    } else if (error) {
      setPhase('error')
    } else {
      setPhase('loading')
      const checkInterval = setInterval(() => {
        if (result) {
          setPhase('result')
          clearInterval(checkInterval)
        }
      }, 500)
      setTimeout(() => {
        clearInterval(checkInterval)
        setPhase(prev => prev === 'loading' ? 'loading' : prev)
      }, 120000)
    }
  }, [result, error, setPhase])

  if (phase === 'loading' && result) setPhase('result')
  if (phase === 'loading' && error) setPhase('error')

  const portfolio = result?.recommendation?.portfolio || []
  const summary = result?.recommendation?.summary || ''

  const handleInvest = async () => {
    if (!portfolio.length) return
    try {
      await baqiApi.executeInvestment(userId || 1, portfolio)
      setInvested(true)
      refreshPortfolio()

      // Send fun Telegram notification about the investment
      try {
        const totalInvested = result?.recommendation?.total_invested || 0
        const expectedReturn = result?.recommendation?.expected_annual_return || 0
        const holdings = portfolio.map((a: PortfolioAllocation) => a.asset_name).join(', ')

        await fetch(
          `${API_URL}/admin/notify-investment?user_id=${userId || 1}&total=${totalInvested}&expected_return=${(expectedReturn * 100).toFixed(1)}&holdings=${encodeURIComponent(holdings)}`,
          { method: 'POST' }
        )
      } catch {
        // Telegram notification is non-critical
      }
    } catch {
      setError('Investment execution failed')
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">
          <span className="text-gradient">AI Investment Engine</span>
        </h1>
        <p className="text-[#8A8878] text-sm mt-1">
          Watch our 5 specialized agents collaborate in real-time to build your portfolio
        </p>
      </motion.div>

      {/* Idle — Big CTA */}
      {phase === 'idle' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-12 relative"
        >
          <Meteors count={10} />
          <div className="w-20 h-20 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center glow-sage mx-auto mb-6 animate-float relative z-10">
            <Sparkles className="w-10 h-10 text-[#A3B570]" />
          </div>

          {!dataSource ? (
            <div className="relative z-10">
              <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">No Data Source Selected</h2>
              <p className="text-[#8A8878] mb-4">Go to Dashboard and choose a data source first</p>
            </div>
          ) : (
            <div className="relative z-10">
              <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">Ready to Generate Your Portfolio?</h2>
              <p className="text-[#8A8878] mb-6 max-w-md mx-auto">
                Our AI pipeline analyzes your spending, assesses risk, checks Shariah compliance,
                and builds a personalized investment recommendation.
              </p>

              <MovingBorderButton onClick={handleGenerate} className="text-[#E8E4DA] font-semibold px-8 py-4 text-lg">
                <Sparkles className="w-5 h-5 mr-2 inline" />
                Launch AI Agents
              </MovingBorderButton>

              <div className="flex items-center justify-center gap-4 mt-6 text-xs text-[#8A8878]">
                <span>5 AI Agents</span>
                <span className="text-[#333D30]">|</span>
                <span>30-90 seconds</span>
                <span className="text-[#333D30]">|</span>
                <span>100% Halal</span>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Agent Pipeline Visualization */}
      {(phase === 'agents' || phase === 'loading') && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-[#A3B570] animate-pulse-dot" />
            <span className="text-sm font-medium text-[#A3B570]">AI Pipeline Active</span>
          </div>

          <AgentPipeline isRunning={phase === 'agents'} onComplete={handleAgentsDone} />

          {phase === 'loading' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-6 text-center"
            >
              <Loader2 className="w-8 h-8 animate-spin text-[#A3B570] mx-auto mb-3" />
              <p className="text-sm text-[#8A8878]">
                Finalizing your recommendation...
              </p>
              <Progress value={85} className="mt-3 max-w-xs mx-auto" />
            </motion.div>
          )}
        </div>
      )}

      {/* Error */}
      {phase === 'error' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <SpotlightCard className="border-[#C65D4A]/30 text-center" spotlightColor="rgba(198, 93, 74, 0.08)">
            <AlertCircle className="w-10 h-10 text-[#C65D4A] mx-auto mb-3" />
            <h3 className="font-bold mb-1 text-[#E8E4DA]">Recommendation Failed</h3>
            <p className="text-sm text-[#8A8878] mb-4">{error}</p>
            <Button onClick={() => setPhase('idle')} variant="outline" className="border-[#333D30] text-[#E8E4DA] hover:bg-[#2C362A]">Try Again</Button>
          </SpotlightCard>
        </motion.div>
      )}

      {/* Result — Portfolio Cards */}
      {phase === 'result' && result && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {/* Summary */}
          <GlowingBorder>
            <div className="p-6">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-[#A3B570] mt-0.5 shrink-0" />
                <div>
                  <h3 className="font-bold text-lg mb-1 text-[#E8E4DA]">Your AI Recommendation is Ready</h3>
                  <p className="text-sm text-[#8A8878]">{summary}</p>
                  {result.recommendation.expected_annual_return && (
                    <div className="flex items-center gap-4 mt-3 text-sm">
                      <Badge variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {(result.recommendation.expected_annual_return * 100).toFixed(1)}% expected return
                      </Badge>
                      <Badge variant="secondary" className="bg-[#D4C9A8]/10 text-[#D4C9A8] border-[#D4C9A8]/20">
                        <Moon className="w-3 h-3 mr-1" />
                        100% Halal
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </GlowingBorder>

          {/* Portfolio Grid */}
          <div className="grid gap-3">
            <AnimatePresence>
              {portfolio.map((alloc: PortfolioAllocation, i: number) => (
                <motion.div
                  key={alloc.ticker}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <SpotlightCard className="hover:border-[#A3B570]/30">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-[#2C362A] flex items-center justify-center">
                          <span className="text-xs font-bold text-[#A3B570]">{alloc.ticker.slice(0, 4)}</span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-sm text-[#E8E4DA]">{alloc.asset_name}</h4>
                            {alloc.is_halal && (
                              <Moon className="w-3 h-3 text-[#D4C9A8]" />
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-[#8A8878]">
                            <span>{alloc.ticker}</span>
                            <span className="text-[#333D30]">|</span>
                            <span className="capitalize">{alloc.asset_type.replace('_', ' ')}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-[#E8E4DA]">{fmt(alloc.amount_pkr)}</p>
                        <p className="text-xs text-[#A3B570]">
                          +{(alloc.expected_return * 100).toFixed(0)}% · {alloc.percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-[#8A8878] mt-2 leading-relaxed">
                      {alloc.rationale}
                    </p>
                  </SpotlightCard>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Total & Invest Button */}
          {portfolio.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <SpotlightCard>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-sm text-[#8A8878]">Total Investment</p>
                    <p className="text-2xl font-bold text-[#E8E4DA]">
                      <AnimatedCounter value={result.recommendation.total_invested || 0} formatter={(v) => formatMoney(v, cur)} />
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-[#8A8878]">Monthly BAQI</p>
                    <p className="text-2xl font-bold text-[#A3B570]">
                      <AnimatedCounter value={result.spending_analysis.monthly_baqi} formatter={(v) => formatMoney(v, cur)} />
                    </p>
                  </div>
                </div>

                {invested ? (
                  <div className="flex items-center gap-2 text-[#A3B570] bg-[#A3B570]/10 rounded-lg p-3">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-medium">Investment executed successfully! View your portfolio.</span>
                  </div>
                ) : (
                  <Button
                    onClick={handleInvest}
                    className="w-full bg-[#A3B570] hover:bg-[#8A9E5C] text-[#1B211A] font-semibold py-6 text-lg rounded-xl glow-sage"
                  >
                    <Briefcase className="w-5 h-5 mr-2" /> Invest Now — {fmt(result.recommendation.total_invested || 0)}
                  </Button>
                )}

                <p className="text-[10px] text-[#8A8878] text-center mt-2">
                  AI-generated recommendation. Not financial advice. Markets can decline.
                </p>
              </SpotlightCard>
            </motion.div>
          )}

          {/* Restart */}
          <div className="text-center">
            <Button variant="ghost" onClick={() => { setPhase('idle'); setResult(null); setInvested(false) }} className="text-[#8A8878] hover:text-[#A3B570]">
              Generate New Recommendation
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
