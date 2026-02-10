import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useApp } from '@/context/AppContext'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { GlowingBorder } from '@/components/ui/glowing-border'
import { MovingBorderButton } from '@/components/ui/moving-border'
import { Meteors } from '@/components/ui/meteors'
import type { InsightItem } from '@/types'
import {
  Brain, PiggyBank, AlertTriangle, TrendingUp, Target, User2,
  Sparkles, Loader2, Zap, BarChart3, MapPin, Coffee, Globe, Compass
} from 'lucide-react'

const CATEGORY_CONFIG: Record<string, { icon: typeof Brain; color: string; label: string }> = {
  behavioral: { icon: Brain, color: '#A3B570', label: 'Behavioral' },
  saving_opportunity: { icon: PiggyBank, color: '#8A9E5C', label: 'Savings' },
  anomaly: { icon: AlertTriangle, color: '#C65D4A', label: 'Anomaly' },
  trend: { icon: TrendingUp, color: '#6B7D3A', label: 'Trend' },
  optimization: { icon: Target, color: '#D4C9A8', label: 'Optimize' },
  lifestyle: { icon: Coffee, color: '#A3B570', label: 'Lifestyle' },
  personality: { icon: User2, color: '#D4C9A8', label: 'Personality' },
}

const SEVERITY_CONFIG: Record<InsightItem['severity'], { bg: string; border: string; text: string }> = {
  info: { bg: 'bg-[#A3B570]/5', border: 'border-[#A3B570]/20', text: 'text-[#A3B570]' },
  warning: { bg: 'bg-[#D4C9A8]/5', border: 'border-[#D4C9A8]/20', text: 'text-[#D4C9A8]' },
  opportunity: { bg: 'bg-[#6B7D3A]/10', border: 'border-[#6B7D3A]/20', text: 'text-[#A3B570]' },
}

export default function Insights() {
  const { dataSource, analysis, insights, insightsLoading, insightsError, fetchInsights } = useApp()
  const cur = analysis?.currency
  const prefix = cur === 'PKR' ? 'PKR ' : '$'

  const persona = insights?.persona
  const exhaust = insights?.data_exhaust

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-5 h-5 text-[#A3B570]" />
          <h1 className="text-2xl font-bold">
            <span className="text-gradient">Data Exhaust Insights</span>
          </h1>
        </div>
        <p className="text-[#8A8878] text-sm">
          AI-discovered personality traits and behavioral patterns from your transaction data
        </p>
      </motion.div>

      {/* CTA */}
      {!insights && !insightsLoading && !insightsError && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-12 relative"
        >
          <Meteors count={10} />
          <div className="w-20 h-20 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center glow-sage mx-auto mb-6 animate-float relative z-10">
            <Brain className="w-10 h-10 text-[#A3B570]" />
          </div>

          {!dataSource ? (
            <div className="relative z-10">
              <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">No Data Source Selected</h2>
              <p className="text-[#8A8878] mb-4">Go to Dashboard and choose a data source first</p>
            </div>
          ) : (
            <div className="relative z-10">
              <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">Who Are You, Really?</h2>
              <p className="text-[#8A8878] mb-6 max-w-md mx-auto">
                Our AI scans your real transaction data to build a financial personality profile,
                detect geographic patterns, uncover hidden habits, and reveal things about you
                that you can't see yourself.
              </p>

              <MovingBorderButton onClick={fetchInsights} className="text-[#E8E4DA] font-semibold px-8 py-4 text-lg">
                <Sparkles className="w-5 h-5 mr-2 inline" />
                Analyze My Data Exhaust
              </MovingBorderButton>

              <div className="flex items-center justify-center gap-4 mt-6 text-xs text-[#8A8878]">
                <span>14 Signal Types</span>
                <span className="text-[#333D30]">|</span>
                <span>3,000+ Transactions</span>
                <span className="text-[#333D30]">|</span>
                <span>AI-Powered</span>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Error State */}
      {!insights && !insightsLoading && insightsError && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-12"
        >
          <div className="w-20 h-20 rounded-2xl bg-[#C65D4A]/10 flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-10 h-10 text-[#C65D4A]" />
          </div>
          <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">Something Went Wrong</h2>
          <p className="text-[#8A8878] mb-6 max-w-md mx-auto text-sm">{insightsError}</p>
          <MovingBorderButton onClick={fetchInsights} className="text-[#E8E4DA] font-semibold px-8 py-4 text-lg">
            <Sparkles className="w-5 h-5 mr-2 inline" />
            Try Again
          </MovingBorderButton>
        </motion.div>
      )}

      {/* Loading State */}
      {insightsLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-20 h-20 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center mx-auto mb-6 animate-glow-pulse">
            <Loader2 className="w-10 h-10 text-[#A3B570] animate-spin" />
          </div>
          <h2 className="text-xl font-bold mb-3 text-[#E8E4DA]">Scanning Your Data Exhaust</h2>
          <div className="max-w-sm mx-auto space-y-2">
            {[
              'Parsing 3,000+ real transactions...',
              'Clustering merchants into behavioral groups...',
              'Detecting geographic footprint...',
              'Identifying subscriptions & recurring patterns...',
              'Computing spending velocity & binge days...',
              'Building your financial personality profile...',
              'Generating AI-powered insights...',
            ].map((text, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.5 }}
                className="flex items-center gap-2 text-sm text-[#8A8878]"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: i * 0.5 + 0.25 }}
                  className="w-1.5 h-1.5 rounded-full bg-[#A3B570]"
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
          {/* Persona Card */}
          {persona && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <GlowingBorder>
                <div className="p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-48 h-48 bg-[#A3B570]/5 rounded-full blur-3xl -mr-24 -mt-24" />
                  <div className="relative z-10">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-14 h-14 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center glow-sage">
                        <Compass className="w-7 h-7 text-[#A3B570]" />
                      </div>
                      <div>
                        <p className="text-xs text-[#8A8878] font-medium uppercase tracking-wider">Your Financial Archetype</p>
                        <h2 className="text-2xl font-bold text-gradient">{persona.archetype}</h2>
                      </div>
                    </div>

                    <p className="text-sm text-[#8A8878] leading-relaxed mb-4">
                      {persona.lifestyle_summary}
                    </p>

                    <div className="flex flex-wrap gap-2 mb-3">
                      {persona.traits?.map((trait, i) => (
                        <Badge key={i} variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20 text-xs">
                          {trait}
                        </Badge>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 text-xs text-[#8A8878]">
                      <span><strong className="text-[#E8E4DA]">Type:</strong> {persona.financial_type}</span>
                      <span className="text-[#333D30]">|</span>
                      <span><strong className="text-[#E8E4DA]">Style:</strong> {persona.spending_personality}</span>
                    </div>
                  </div>
                </div>
              </GlowingBorder>
            </motion.div>
          )}

          {/* Overview Stats */}
          {exhaust?.overview && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <SpotlightCard>
                  <p className="text-[10px] text-[#8A8878] uppercase tracking-wider">Transactions</p>
                  <p className="text-lg font-bold text-[#E8E4DA]">{exhaust.overview.total_transactions?.toLocaleString()}</p>
                </SpotlightCard>
                <SpotlightCard>
                  <p className="text-[10px] text-[#8A8878] uppercase tracking-wider">Months</p>
                  <p className="text-lg font-bold text-[#E8E4DA]">{exhaust.overview.months_covered}</p>
                </SpotlightCard>
                <SpotlightCard>
                  <p className="text-[10px] text-[#8A8878] uppercase tracking-wider">Avg Daily</p>
                  <p className="text-lg font-bold text-[#E8E4DA]">{prefix}{exhaust.overview.avg_daily_spend?.toLocaleString()}</p>
                </SpotlightCard>
                <SpotlightCard>
                  <p className="text-[10px] text-[#8A8878] uppercase tracking-wider">Avg Txn</p>
                  <p className="text-lg font-bold text-[#E8E4DA]">{prefix}{exhaust.overview.avg_transaction_size?.toLocaleString()}</p>
                </SpotlightCard>
              </div>
            </motion.div>
          )}

          {/* Geographic Footprint */}
          {exhaust?.geographic_signals && Object.keys(exhaust.geographic_signals).length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
            >
              <SpotlightCard>
                <div className="flex items-center gap-2 mb-3">
                  <Globe className="w-4 h-4 text-[#A3B570]" />
                  <h3 className="font-semibold text-sm text-[#D4C9A8]">Geographic Footprint</h3>
                </div>
                <div className="space-y-2">
                  {Object.entries(exhaust.geographic_signals as Record<string, {
                    transactions: number; total_spent: number; date_range: string; avg_per_transaction: number
                  }>).map(([region, data]) => (
                    <div key={region} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-3.5 h-3.5 text-[#8A8878]" />
                        <span className="text-sm font-medium text-[#E8E4DA]">{region}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-[#8A8878]">
                        <span>{data.transactions} txns</span>
                        <span className="font-medium text-[#E8E4DA]">{prefix}{data.total_spent.toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </SpotlightCard>
            </motion.div>
          )}

          {/* Insight Cards */}
          <div className="flex items-center gap-2 pt-2">
            <Zap className="w-4 h-4 text-[#A3B570]" />
            <h3 className="font-semibold text-sm text-[#D4C9A8]">{insights.insights.length} AI-Discovered Insights</h3>
          </div>

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
                  transition={{ delay: 0.2 + i * 0.08 }}
                >
                  <SpotlightCard className={`${sevConfig.border} border`} spotlightColor={`${catConfig.color}10`}>
                    <div className="flex items-start gap-4">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                        style={{ background: `${catConfig.color}15` }}
                      >
                        <Icon className="w-5 h-5" style={{ color: catConfig.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <h4 className="font-semibold text-sm text-[#E8E4DA]">{insight.title}</h4>
                          <Badge
                            variant="secondary"
                            className="text-[10px]"
                            style={{ background: `${catConfig.color}15`, color: catConfig.color, borderColor: `${catConfig.color}30` }}
                          >
                            {catConfig.label}
                          </Badge>
                          {insight.impact_amount && (
                            <Badge variant="secondary" className="text-[10px] bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20">
                              {prefix}{Math.abs(insight.impact_amount).toLocaleString()} impact
                            </Badge>
                          )}
                        </div>
                        <p className={`text-sm leading-relaxed mb-2 ${sevConfig.text}`}>
                          {insight.description}
                        </p>
                        <div className="flex items-start gap-2 bg-[#2C362A]/60 rounded-lg p-2.5">
                          <Target className="w-3.5 h-3.5 text-[#A3B570] mt-0.5 shrink-0" />
                          <p className="text-xs font-medium text-[#E8E4DA]">{insight.action}</p>
                        </div>
                      </div>
                    </div>
                  </SpotlightCard>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {/* Data Exhaust Summary */}
          {exhaust && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
            >
              <SpotlightCard>
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="w-4 h-4 text-[#8A8878]" />
                  <h3 className="font-semibold text-sm text-[#D4C9A8]">Raw Data Exhaust Signals</h3>
                </div>

                {/* Day of Week Pattern */}
                {exhaust.day_of_week_pattern && (
                  <div className="mb-4">
                    <p className="text-xs text-[#8A8878] mb-2">Spending by Day of Week</p>
                    <div className="flex items-end gap-1.5 h-16">
                      {Object.entries(exhaust.day_of_week_pattern.totals as Record<string, number>).map(
                        ([day, total]) => {
                          const max = Math.max(
                            ...Object.values(exhaust.day_of_week_pattern.totals as Record<string, number>)
                          )
                          const pct = max > 0 ? (total / max) * 100 : 0
                          const isPeak = day === exhaust.day_of_week_pattern.peak_day
                          return (
                            <div key={day} className="flex-1 flex flex-col items-center gap-1">
                              <motion.div
                                className="w-full rounded-t transition-all duration-500"
                                initial={{ height: 0 }}
                                animate={{ height: `${Math.max(pct, 4)}%` }}
                                transition={{ duration: 0.6, delay: 0.1 }}
                                style={{
                                  background: isPeak ? '#A3B570' : '#333D30',
                                }}
                              />
                              <span className={`text-[9px] ${isPeak ? 'text-[#A3B570] font-bold' : 'text-[#8A8878]'}`}>
                                {day.slice(0, 3)}
                              </span>
                            </div>
                          )
                        }
                      )}
                    </div>
                  </div>
                )}

                {/* Merchant Clusters */}
                {exhaust.merchant_clusters && Object.keys(exhaust.merchant_clusters).length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-[#8A8878] mb-2">Behavioral Clusters</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(exhaust.merchant_clusters as Record<string, { count: number; total: number }>).map(
                        ([cluster, data]) => (
                          <Badge key={cluster} variant="outline" className="text-[10px] gap-1 border-[#333D30] text-[#D4C9A8]">
                            {cluster.replace(/_/g, ' ')}
                            <span className="text-[#8A8878]">({data.count})</span>
                          </Badge>
                        )
                      )}
                    </div>
                  </div>
                )}

                {/* Detected Subscriptions */}
                {exhaust.subscription_detection?.length > 0 && (
                  <div>
                    <p className="text-xs text-[#8A8878] mb-2">Detected Subscriptions</p>
                    <div className="space-y-1.5">
                      {(exhaust.subscription_detection as Array<{
                        merchant: string; monthly_cost: number; months_detected: number
                      }>).slice(0, 8).map((sub, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="text-[#E8E4DA] truncate">{sub.merchant}</span>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[#8A8878]">{sub.months_detected}mo</span>
                            <span className="font-medium text-[#E8E4DA]">{prefix}{sub.monthly_cost.toFixed(2)}/mo</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </SpotlightCard>
            </motion.div>
          )}

          {/* Regenerate */}
          <div className="text-center">
            <Button variant="ghost" onClick={fetchInsights} className="text-[#8A8878] hover:text-[#A3B570]">
              <Sparkles className="w-4 h-4 mr-2" />
              Regenerate Insights
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
