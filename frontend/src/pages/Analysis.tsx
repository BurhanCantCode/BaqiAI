import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatMoney } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import {
  Home, ShoppingCart, Droplets, TrendingUp, Loader2, BarChart3
} from 'lucide-react'

const CATEGORY_CONFIG = {
  fixed: { label: 'Fixed', color: '#3b82f6', icon: Home, description: 'Rent, utilities, loan payments' },
  discretionary: { label: 'Discretionary', color: '#8b5cf6', icon: ShoppingCart, description: 'Groceries, transport, healthcare' },
  watery: { label: 'Watery', color: '#f59e0b', icon: Droplets, description: 'Food delivery, shopping, entertainment — reducible!' },
}

export default function Analysis() {
  const { analysis: data, loading } = useApp()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <BarChart3 className="w-12 h-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-bold mb-2">No Analysis Data</h2>
        <p className="text-muted-foreground">Go to Dashboard and generate demo data first.</p>
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
        <h1 className="text-2xl font-bold">Spending Analysis</h1>
        <p className="text-muted-foreground text-sm">{months}-month breakdown of your transaction data</p>
      </motion.div>

      {/* BAQI Highlight */}
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
        <Card className="p-5 border-gradient">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Your Monthly BAQI (Investable Surplus)</p>
              <p className="text-3xl font-bold text-primary">{fmt(data.baqi_amount / months)}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {data.savings_rate.toFixed(1)}% savings rate | Potential: {fmt(data.recommended_investment / months)}/mo with watery reduction
              </p>
            </div>
            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center glow-green">
              <TrendingUp className="w-7 h-7 text-primary" />
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Category Breakdown Cards */}
      <div className="grid gap-3">
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
              <Card className="p-4 bg-card border-border/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${config.color}15` }}>
                      <Icon className="w-5 h-5" style={{ color: config.color }} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm">{config.label} Spending</h3>
                      <p className="text-xs text-muted-foreground">{config.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{fmt(catData.total)}</p>
                    <Badge variant="secondary" className="text-xs" style={{ background: `${config.color}15`, color: config.color }}>
                      {catData.percentage.toFixed(1)}%
                    </Badge>
                  </div>
                </div>

                {/* Top merchants in category */}
                <div className="space-y-1.5">
                  {catData.items.slice(0, 4).map((m, j) => (
                    <div key={j} className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{m.merchant}</span>
                      <div className="flex items-center gap-2">
                        <span>{fmt(m.total)}</span>
                        <div className="w-16 h-1.5 rounded-full bg-secondary overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min((m.total / catData.total) * 100, 100)}%`,
                              background: config.color,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Top Merchants Bar Chart */}
      <Card className="p-5 bg-card border-border/50">
        <h3 className="font-semibold mb-4">Top Merchants by Spending</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={topMerchants} layout="vertical" margin={{ left: 80 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} tickFormatter={v => `${cur === 'PKR' ? '' : '$'}${(v/1000).toFixed(0)}k`} />
            <YAxis dataKey="merchant" type="category" tick={{ fontSize: 11, fill: '#94a3b8' }} width={80} />
            <Tooltip
              contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}
              formatter={(val: any) => fmt(Number(val))}
            />
            <Bar dataKey="total" radius={[0, 4, 4, 0]}>
              {topMerchants.map((entry, i) => (
                <Cell key={i} fill={CATEGORY_CONFIG[entry.category as keyof typeof CATEGORY_CONFIG]?.color || '#94a3b8'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}
