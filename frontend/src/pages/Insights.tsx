import { motion, AnimatePresence } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatPKR } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import type { InsightItem } from '@/types'
import {
  Brain, PiggyBank, AlertTriangle, TrendingUp, Target,
  Sparkles, Loader2, Zap, BarChart3
} from 'lucide-react'

const CATEGORY_CONFIG: Record<InsightItem['category'], { icon: typeof Brain; color: string; label: string }> = {
  behavioral: { icon: Brain, color: '#8b5cf6', label: 'Behavioral' },
  saving_opportunity: { icon: PiggyBank, color: '#10b981', label: 'Savings' },
  anomaly: { icon: AlertTriangle, color: '#ef4444', label: 'Anomaly' },
  trend: { icon: TrendingUp, color: '#3b82f6', label: 'Trend' },
  optimization: { icon: Target, color: '#06b6d4', label: 'Optimize' },
}

const SEVERITY_CONFIG: Record<InsightItem['severity'], { bg: string; border: string; text: string }> = {
  info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  warning: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700' },
  opportunity: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700' },
}

export default function Insights() {
  const { userId, insights, insightsLoading, fetchInsights } = useApp()

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-5 h-5 text-primary" />
          <h1 className="text-2xl font-bold">
            <span className="text-gradient">Data Exhaust Insights</span>
          </h1>
        </div>
        <p className="text-muted-foreground text-sm">
          AI-discovered behavioral patterns hidden in your transaction data
        </p>
      </motion.div>

      {/* CTA / Loading / Results */}
      {!insights && !insightsLoading && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-12"
        >
          <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center glow-green mx-auto mb-6 animate-float">
            <Brain className="w-10 h-10 text-primary" />
          </div>

          {!userId ? (
            <div>
              <h2 className="text-xl font-bold mb-2">No Account Found</h2>
              <p className="text-muted-foreground mb-4">Go to Dashboard and click "Try Demo" first</p>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-bold mb-2">Discover Your Hidden Patterns</h2>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Our AI scans 6 months of transaction data to find behavioral patterns,
                spending anomalies, and saving opportunities you can't see on your own.
              </p>

              <Button
                size="lg"
                onClick={fetchInsights}
                className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-8 py-6 text-lg rounded-xl glow-green"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Analyze My Data Exhaust
              </Button>

              <div className="flex items-center justify-center gap-4 mt-6 text-xs text-muted-foreground">
                <span>8 Signal Types</span>
                <span className="text-muted-foreground/50">|</span>
                <span>3-5 seconds</span>
                <span className="text-muted-foreground/50">|</span>
                <span>AI-Powered</span>
              </div>
            </>
          )}
        </motion.div>
      )}

      {/* Loading State */}
      {insightsLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
          </div>
          <h2 className="text-xl font-bold mb-3">Scanning Your Data Exhaust</h2>
          <div className="max-w-sm mx-auto space-y-2">
            {[
              'Analyzing day-of-week spending patterns...',
              'Detecting recurring subscriptions...',
              'Identifying spending outliers...',
              'Computing merchant loyalty scores...',
              'Generating AI insights...',
            ].map((text, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.6 }}
                className="flex items-center gap-2 text-sm text-muted-foreground"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: i * 0.6 + 0.3 }}
                  className="w-1.5 h-1.5 rounded-full bg-primary"
                />
                {text}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Results */}
      {insights && !insightsLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {/* Summary Badge */}
          <Card className="p-4 border-gradient">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-bold">
                  {insights.insights.length} Insights Discovered
                </h3>
                <p className="text-xs text-muted-foreground">
                  From {Object.keys(insights.data_exhaust).length} data exhaust signals
                </p>
              </div>
            </div>
          </Card>

          {/* Insight Cards */}
          <AnimatePresence>
            {insights.insights.map((insight: InsightItem, i: number) => {
              const catConfig = CATEGORY_CONFIG[insight.category] || CATEGORY_CONFIG.behavioral
              const sevConfig = SEVERITY_CONFIG[insight.severity] || SEVERITY_CONFIG.info
              const Icon = catConfig.icon
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className={`p-5 border ${sevConfig.border} ${sevConfig.bg}`}>
                    <div className="flex items-start gap-4">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                        style={{ background: `${catConfig.color}15` }}
                      >
                        <Icon className="w-5 h-5" style={{ color: catConfig.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <h4 className="font-semibold text-sm">{insight.title}</h4>
                          <Badge
                            variant="secondary"
                            className="text-[10px]"
                            style={{ background: `${catConfig.color}15`, color: catConfig.color }}
                          >
                            {catConfig.label}
                          </Badge>
                          {insight.impact_pkr && (
                            <Badge variant="secondary" className="text-[10px] bg-primary/10 text-primary">
                              {formatPKR(insight.impact_pkr)} impact
                            </Badge>
                          )}
                        </div>
                        <p className={`text-sm leading-relaxed mb-2 ${sevConfig.text}`}>
                          {insight.description}
                        </p>
                        <div className="flex items-start gap-2 bg-white/60 rounded-lg p-2.5">
                          <Target className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                          <p className="text-xs font-medium text-foreground">{insight.action}</p>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {/* Data Exhaust Summary */}
          {insights.data_exhaust && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              <Card className="p-5 bg-card border-border/50">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="w-4 h-4 text-muted-foreground" />
                  <h3 className="font-semibold text-sm">Data Exhaust Signals</h3>
                </div>

                {/* Day of Week Pattern */}
                {insights.data_exhaust.day_of_week_pattern && (
                  <div className="mb-4">
                    <p className="text-xs text-muted-foreground mb-2">Spending by Day of Week</p>
                    <div className="flex items-end gap-1.5 h-16">
                      {Object.entries(insights.data_exhaust.day_of_week_pattern.totals as Record<string, number>).map(
                        ([day, total]) => {
                          const max = Math.max(
                            ...Object.values(insights.data_exhaust.day_of_week_pattern.totals as Record<string, number>)
                          )
                          const pct = max > 0 ? (total / max) * 100 : 0
                          const isPeak = day === insights.data_exhaust.day_of_week_pattern.peak_day
                          return (
                            <div key={day} className="flex-1 flex flex-col items-center gap-1">
                              <div
                                className="w-full rounded-t transition-all duration-500"
                                style={{
                                  height: `${Math.max(pct, 4)}%`,
                                  background: isPeak ? '#3b82f6' : '#e2e8f0',
                                }}
                              />
                              <span className={`text-[9px] ${isPeak ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
                                {day.slice(0, 3)}
                              </span>
                            </div>
                          )
                        }
                      )}
                    </div>
                  </div>
                )}

                {/* Detected Subscriptions */}
                {insights.data_exhaust.subscription_detection?.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Detected Subscriptions</p>
                    <div className="space-y-1.5">
                      {(insights.data_exhaust.subscription_detection as Array<{
                        merchant: string
                        monthly_cost: number
                        months_detected: number
                      }>).map((sub, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="text-foreground">{sub.merchant}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">{sub.months_detected}mo</span>
                            <span className="font-medium">{formatPKR(sub.monthly_cost)}/mo</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            </motion.div>
          )}

          {/* Regenerate */}
          <div className="text-center">
            <Button variant="ghost" onClick={fetchInsights}>
              <Sparkles className="w-4 h-4 mr-2" />
              Regenerate Insights
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
