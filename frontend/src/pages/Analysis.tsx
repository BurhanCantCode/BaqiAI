import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Badge } from '@/components/ui/badge'
import { formatMoney } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { GlowingBorder } from '@/components/ui/glowing-border'
import { AnimatedCounter } from '@/components/ui/animated-counter'
import {
  Home, ShoppingCart, Droplets, TrendingUp, Loader2, BarChart3
} from 'lucide-react'

const CATEGORY_CONFIG = {
  fixed: { label: 'Fixed', color: '#6B7D3A', icon: Home, description: 'Rent, utilities, loan payments' },
  discretionary: { label: 'Discretionary', color: '#A3B570', icon: ShoppingCart, description: 'Groceries, transport, healthcare' },
  watery: { label: 'Watery', color: '#D4C9A8', icon: Droplets, description: 'Food delivery, shopping, entertainment — reducible!' },
}

export default function Analysis() {
  const { analysis: data, loading } = useApp()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-[#A3B570]/10 flex items-center justify-center animate-glow-pulse">
            <Loader2 className="w-6 h-6 animate-spin text-[#A3B570]" />
          </div>
          <p className="text-sm text-[#8A8878]">Analyzing your spending...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-16 h-16 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center mb-4">
          <BarChart3 className="w-8 h-8 text-[#8A8878]" />
        </div>
        <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">No Analysis Data</h2>
        <p className="text-[#8A8878]">Go to Dashboard and generate demo data first.</p>
      </div>
    )
  }

  const cur = data.currency
  const fmt = (v: number) => formatMoney(v, cur)
  const months = data.monthly_breakdown?.length || 6

  const categories = [
    { key: 'fixed' as const, data: data.fixed },
    { key: 'discretionary' as const, data: data.discretionary },
    { key: 'watery' as const, data: data.watery },
  ]

  const topMerchants = [
    ...data.fixed.items.slice(0, 3).map(m => ({ ...m, category: 'fixed' })),
    ...data.discretionary.items.slice(0, 3).map(m => ({ ...m, category: 'discretionary' })),
    ...data.watery.items.slice(0, 3).map(m => ({ ...m, category: 'watery' })),
  ].sort((a, b) => b.total - a.total).slice(0, 8)

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-[#E8E4DA]">Spending Analysis</h1>
        <p className="text-[#8A8878] text-sm mt-1">{months}-month breakdown of your transaction data</p>
      </motion.div>

      {/* BAQI Highlight */}
      <GlowingBorder>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-[#8A8878] uppercase tracking-wider mb-1">Your Monthly BAQI (Investable Surplus)</p>
              <p className="text-3xl font-bold text-[#A3B570]">
                <AnimatedCounter value={data.baqi_amount / months} formatter={(v) => formatMoney(v, cur)} />
              </p>
              <p className="text-xs text-[#8A8878] mt-2">
                {data.savings_rate.toFixed(1)}% savings rate • Potential: {fmt(data.recommended_investment / months)}/mo with watery reduction
              </p>
            </div>
            <div className="w-14 h-14 rounded-xl bg-[#A3B570]/10 flex items-center justify-center glow-sage">
              <TrendingUp className="w-7 h-7 text-[#A3B570]" />
            </div>
          </div>
        </div>
      </GlowingBorder>

      {/* Category Breakdown Cards */}
      <div className="grid gap-4">
        {categories.map(({ key, data: catData }, i) => {
          const config = CATEGORY_CONFIG[key]
          const Icon = config.icon
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <SpotlightCard spotlightColor={`${config.color}15`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${config.color}15` }}>
                      <Icon className="w-5 h-5" style={{ color: config.color }} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-[#E8E4DA]">{config.label} Spending</h3>
                      <p className="text-xs text-[#8A8878]">{config.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[#E8E4DA]">{fmt(catData.total)}</p>
                    <Badge variant="secondary" className="text-xs" style={{ background: `${config.color}15`, color: config.color, borderColor: `${config.color}30` }}>
                      {catData.percentage.toFixed(1)}%
                    </Badge>
                  </div>
                </div>

                {/* Top merchants in category */}
                <div className="space-y-2">
                  {catData.items.slice(0, 4).map((m, j) => (
                    <div key={j} className="flex items-center justify-between text-xs">
                      <span className="text-[#8A8878]">{m.merchant}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[#E8E4DA]">{fmt(m.total)}</span>
                        <div className="w-20 h-1.5 rounded-full bg-[#2C362A] overflow-hidden">
                          <motion.div
                            className="h-full rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min((m.total / catData.total) * 100, 100)}%` }}
                            transition={{ duration: 0.8, delay: 0.2 + j * 0.1 }}
                            style={{ background: config.color }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </SpotlightCard>
            </motion.div>
          )
        })}
      </div>

      {/* Top Merchants Bar Chart */}
      <SpotlightCard>
        <h3 className="font-semibold mb-4 text-[#D4C9A8]">Top Merchants by Spending</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={topMerchants} layout="vertical" margin={{ left: 80 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: '#8A8878' }} tickFormatter={v => `${cur === 'PKR' ? '' : '$'}${(v/1000).toFixed(0)}k`} axisLine={false} />
            <YAxis dataKey="merchant" type="category" tick={{ fontSize: 11, fill: '#8A8878' }} width={80} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#232B22', border: '1px solid #333D30', borderRadius: '10px', boxShadow: '0 4px 20px rgba(0,0,0,0.3)', color: '#E8E4DA', fontSize: '12px' }}
              formatter={(val: any) => fmt(Number(val))}
            />
            <Bar dataKey="total" radius={[0, 6, 6, 0]}>
              {topMerchants.map((entry, i) => (
                <Cell key={i} fill={CATEGORY_CONFIG[entry.category as keyof typeof CATEGORY_CONFIG]?.color || '#8A8878'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </SpotlightCard>
    </div>
  )
}
