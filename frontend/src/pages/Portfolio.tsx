import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { Card } from '@/components/ui/card'
import { formatMoney, formatPercent } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import {
  Briefcase, TrendingUp, TrendingDown, Moon, Loader2
} from 'lucide-react'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#06b6d4', '#ef4444']

export default function Portfolio() {
  const { portfolio: data, analysis, loading } = useApp()
  const cur = analysis?.currency
  const fmt = (v: number) => formatMoney(v, cur)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!data || !data.holdings.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <Briefcase className="w-12 h-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-bold mb-2">No Portfolio Yet</h2>
        <p className="text-muted-foreground">Generate an AI recommendation and invest to see your portfolio here.</p>
      </div>
    )
  }

  const isPositive = data.total_return >= 0
  const pieData = data.holdings.map((h, i) => ({
    name: h.ticker,
    value: h.amount,
    color: COLORS[i % COLORS.length],
  }))

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">Your Portfolio</h1>
      </motion.div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="p-4 bg-card border-border/50">
          <p className="text-xs text-muted-foreground">Invested</p>
          <p className="text-lg font-bold">{fmt(data.total_invested)}</p>
        </Card>
        <Card className="p-4 bg-card border-border/50">
          <p className="text-xs text-muted-foreground">Current Value</p>
          <p className="text-lg font-bold">{fmt(data.current_value)}</p>
        </Card>
        <Card className={`p-4 border-border/50 ${isPositive ? 'bg-primary/5' : 'bg-destructive/5'}`}>
          <p className="text-xs text-muted-foreground">Return</p>
          <div className="flex items-center gap-1">
            {isPositive ? <TrendingUp className="w-4 h-4 text-primary" /> : <TrendingDown className="w-4 h-4 text-destructive" />}
            <p className={`text-lg font-bold ${isPositive ? 'text-primary' : 'text-destructive'}`}>
              {formatPercent(data.return_percentage)}
            </p>
          </div>
        </Card>
      </div>

      {/* Allocation Pie */}
      <Card className="p-5 bg-card border-border/50">
        <h3 className="font-semibold mb-3">Allocation</h3>
        <div className="flex items-center">
          <ResponsiveContainer width="40%" height={160}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={65} paddingAngle={2} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="flex-1 space-y-1.5">
            {pieData.map(d => (
              <div key={d.name} className="flex items-center gap-2 text-xs">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                <span className="text-muted-foreground">{d.name}</span>
                <span className="ml-auto font-medium">{fmt(d.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Holdings */}
      <div className="space-y-2">
        <h3 className="font-semibold">Holdings</h3>
        {data.holdings.map((h, i) => (
          <motion.div
            key={h.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="p-4 bg-card border-border/50 hover:border-primary/20 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ background: `${COLORS[i % COLORS.length]}15` }}
                  >
                    <span className="text-xs font-bold" style={{ color: COLORS[i % COLORS.length] }}>
                      {h.ticker.slice(0, 4)}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h4 className="font-semibold text-sm">{h.asset_name}</h4>
                      <Moon className="w-3 h-3 text-amber-400" />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {h.quantity.toFixed(2)} units @ {fmt(h.purchase_price)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-sm">{fmt(h.current_value || h.amount)}</p>
                  <p className={`text-xs ${(h.return_pct || 0) >= 0 ? 'text-primary' : 'text-destructive'}`}>
                    {formatPercent(h.return_pct || 0)}
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
