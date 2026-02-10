import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import AgentPipeline from '@/components/AgentPipeline'
import { baqiApi } from '@/api/client'
import { formatPKR } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import type { RecommendationResult, PortfolioAllocation } from '@/types'
import {
  Sparkles, Loader2, CheckCircle2, Moon, TrendingUp,
  ArrowRight, Briefcase, AlertCircle
} from 'lucide-react'

type Phase = 'idle' | 'agents' | 'loading' | 'result' | 'error'

export default function Invest() {
  const { userId, refreshPortfolio } = useApp()
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<RecommendationResult | null>(null)
  const [error, setError] = useState('')
  const [investing, setInvesting] = useState(false)
  const [invested, setInvested] = useState(false)

  const handleGenerate = () => {
    if (!userId) return
    setPhase('agents')
    setResult(null)
    setError('')

    // Start the real API call in background
    baqiApi.generateRecommendation(userId)
      .then(res => {
        setResult(res.data)
      })
      .catch(err => {
        setError(err.response?.data?.detail || 'Recommendation failed. Please try again.')
      })
  }

  const handleAgentsDone = useCallback(() => {
    // If API result is already here, show it
    // Otherwise show loading state until API completes
    if (result) {
      setPhase('result')
    } else if (error) {
      setPhase('error')
    } else {
      setPhase('loading')
      // Poll for result
      const checkInterval = setInterval(() => {
        if (result) {
          setPhase('result')
          clearInterval(checkInterval)
        }
      }, 500)
      // Also watch for state changes
      setTimeout(() => {
        clearInterval(checkInterval)
        setPhase(prev => prev === 'loading' ? 'loading' : prev)
      }, 120000)
    }
  }, [result, error])

  // Watch for result/error during loading phase
  if (phase === 'loading' && result) setPhase('result')
  if (phase === 'loading' && error) setPhase('error')

  const portfolio = result?.recommendation?.portfolio || []
  const summary = result?.recommendation?.summary || ''

  const handleInvest = async () => {
    if (!portfolio.length) return
    setInvesting(true)
    try {
      await baqiApi.executeInvestment(userId, portfolio)
      setInvested(true)
      refreshPortfolio()
    } catch {
      setError('Investment execution failed')
    } finally {
      setInvesting(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">
          <span className="text-gradient">AI Investment Engine</span>
        </h1>
        <p className="text-muted-foreground text-sm">
          Watch our 5 specialized agents collaborate in real-time to build your portfolio
        </p>
      </motion.div>

      {/* Idle — Big CTA */}
      {phase === 'idle' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-12"
        >
          <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center glow-green mx-auto mb-6 animate-float">
            <Sparkles className="w-10 h-10 text-primary" />
          </div>

          {!userId ? (
            <div>
              <h2 className="text-xl font-bold mb-2">No Account Found</h2>
              <p className="text-muted-foreground mb-4">Go to Dashboard and click "Try Demo" first</p>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-bold mb-2">Ready to Generate Your Portfolio?</h2>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Our AI pipeline analyzes your spending, assesses risk, checks Shariah compliance,
                and builds a personalized investment recommendation.
              </p>

              <Button
                size="lg"
                onClick={handleGenerate}
                className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-8 py-6 text-lg rounded-xl glow-green"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Launch AI Agents
              </Button>

              <div className="flex items-center justify-center gap-4 mt-6 text-xs text-muted-foreground">
                <span>5 AI Agents</span>
                <span className="text-muted-foreground/50">|</span>
                <span>30-90 seconds</span>
                <span className="text-muted-foreground/50">|</span>
                <span>100% Halal</span>
              </div>
            </>
          )}
        </motion.div>
      )}

      {/* Agent Pipeline Visualization */}
      {(phase === 'agents' || phase === 'loading') && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse-dot" />
            <span className="text-sm font-medium text-primary">AI Pipeline Active</span>
          </div>

          <AgentPipeline isRunning={phase === 'agents'} onComplete={handleAgentsDone} />

          {phase === 'loading' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-6 text-center"
            >
              <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
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
          <Card className="p-6 border-destructive/30 bg-destructive/5 text-center">
            <AlertCircle className="w-10 h-10 text-destructive mx-auto mb-3" />
            <h3 className="font-bold mb-1">Recommendation Failed</h3>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => setPhase('idle')} variant="outline">Try Again</Button>
          </Card>
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
          <Card className="p-5 border-gradient">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-primary mt-0.5 shrink-0" />
              <div>
                <h3 className="font-bold text-lg mb-1">Your AI Recommendation is Ready</h3>
                <p className="text-sm text-muted-foreground">{summary}</p>
                {result.recommendation.expected_annual_return && (
                  <div className="flex items-center gap-4 mt-3 text-sm">
                    <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      {(result.recommendation.expected_annual_return * 100).toFixed(1)}% expected return
                    </Badge>
                    <Badge variant="secondary" className="bg-amber-500/10 text-amber-400 border-amber-500/20">
                      <Moon className="w-3 h-3 mr-1" />
                      100% Halal
                    </Badge>
                  </div>
                )}
              </div>
            </div>
          </Card>

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
                  <Card className="p-4 bg-card border-border/50 hover:border-primary/30 transition-all">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
                          <span className="text-xs font-bold text-primary">{alloc.ticker.slice(0, 4)}</span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-sm">{alloc.asset_name}</h4>
                            {alloc.is_halal && (
                              <Moon className="w-3 h-3 text-amber-400" />
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{alloc.ticker}</span>
                            <span className="text-muted-foreground/50">|</span>
                            <span className="capitalize">{alloc.asset_type.replace('_', ' ')}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{formatPKR(alloc.amount_pkr)}</p>
                        <p className="text-xs text-primary">
                          +{(alloc.expected_return * 100).toFixed(0)}% · {alloc.percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                      {alloc.rationale}
                    </p>
                  </Card>
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
              <Card className="p-5 bg-card border-border/50">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Investment</p>
                    <p className="text-2xl font-bold">{formatPKR(result.recommendation.total_invested || 0)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Monthly BAQI</p>
                    <p className="text-2xl font-bold text-primary">
                      {formatPKR(result.spending_analysis.monthly_baqi)}
                    </p>
                  </div>
                </div>

                {invested ? (
                  <div className="flex items-center gap-2 text-primary bg-primary/10 rounded-lg p-3">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-medium">Investment executed successfully! View your portfolio.</span>
                  </div>
                ) : (
                  <Button
                    onClick={handleInvest}
                    disabled={investing}
                    className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-6 text-lg rounded-xl glow-green"
                  >
                    {investing ? (
                      <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Executing...</>
                    ) : (
                      <><Briefcase className="w-5 h-5 mr-2" /> Invest Now — {formatPKR(result.recommendation.total_invested || 0)}</>
                    )}
                  </Button>
                )}

                <p className="text-[10px] text-muted-foreground text-center mt-2">
                  AI-generated recommendation. Not financial advice. Markets can decline. Past returns don't guarantee future results.
                </p>
              </Card>
            </motion.div>
          )}

          {/* Restart */}
          <div className="text-center">
            <Button variant="ghost" onClick={() => { setPhase('idle'); setResult(null); setInvested(false) }}>
              Generate New Recommendation
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
