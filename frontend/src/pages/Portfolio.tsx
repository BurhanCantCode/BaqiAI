import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { formatMoney, formatPercent } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { AnimatedCounter } from '@/components/ui/animated-counter'
import {
  Briefcase, TrendingUp, TrendingDown, Moon, Loader2
} from 'lucide-react'

const COLORS = ['#A3B570', '#6B7D3A', '#D4C9A8', '#8A9E5C', '#5A6B32', '#C65D4A']

export default function Portfolio() {
  const { portfolio: data, analysis, loading } = useApp()
  const cur = analysis?.currency
  const fmt = (v: number) => formatMoney(v, cur)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-[#A3B570]/10 flex items-center justify-center animate-glow-pulse">
            <Loader2 className="w-6 h-6 animate-spin text-[#A3B570]" />
          </div>
          <p className="text-sm text-[#8A8878]">Loading portfolio...</p>
        </div>
      </div>
    )
  }

  if (!data || !data.holdings.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-16 h-16 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center mb-4">
          <Briefcase className="w-8 h-8 text-[#8A8878]" />
        </div>
        <h2 className="text-xl font-bold mb-2 text-[#E8E4DA]">No Portfolio Yet</h2>
        <p className="text-[#8A8878]">Generate an AI recommendation and invest to see your portfolio here.</p>
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
        <h1 className="text-2xl font-bold text-[#E8E4DA]">Your Portfolio</h1>
      </motion.div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <SpotlightCard>
          <p className="text-xs text-[#8A8878] uppercase tracking-wider mb-1">Invested</p>
          <p className="text-xl font-bold text-[#E8E4DA]">
            <AnimatedCounter value={data.total_invested} formatter={(v) => formatMoney(v, cur)} />
          </p>
        </SpotlightCard>
        <SpotlightCard>
          <p className="text-xs text-[#8A8878] uppercase tracking-wider mb-1">Current Value</p>
          <p className="text-xl font-bold text-[#E8E4DA]">
            <AnimatedCounter value={data.current_value} formatter={(v) => formatMoney(v, cur)} />
          </p>
        </SpotlightCard>
        <SpotlightCard spotlightColor={isPositive ? 'rgba(163, 181, 112, 0.1)' : 'rgba(198, 93, 74, 0.1)'}>
          <p className="text-xs text-[#8A8878] uppercase tracking-wider mb-1">Return</p>
          <div className="flex items-center gap-1.5">
            {isPositive ? <TrendingUp className="w-4 h-4 text-[#A3B570]" /> : <TrendingDown className="w-4 h-4 text-[#C65D4A]" />}
            <p className={`text-xl font-bold ${isPositive ? 'text-[#A3B570]' : 'text-[#C65D4A]'}`}>
              {formatPercent(data.return_percentage)}
            </p>
          </div>
        </SpotlightCard>
      </div>

      {/* Allocation Pie */}
      <SpotlightCard>
        <h3 className="font-semibold mb-4 text-[#D4C9A8]">Allocation</h3>
        <div className="flex items-center">
          <ResponsiveContainer width="40%" height={160}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={65} paddingAngle={3} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="flex-1 space-y-2">
            {pieData.map(d => (
              <div key={d.name} className="flex items-center gap-2 text-xs">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                <span className="text-[#8A8878]">{d.name}</span>
                <span className="ml-auto font-medium text-[#E8E4DA]">{fmt(d.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </SpotlightCard>

      {/* Holdings */}
      <div className="space-y-2">
        <h3 className="font-semibold text-[#D4C9A8]">Holdings</h3>
        {data.holdings.map((h, i) => (
          <motion.div
            key={h.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <SpotlightCard className="hover:border-[#A3B570]/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ background: `${COLORS[i % COLORS.length]}20` }}
                  >
                    <span className="text-xs font-bold" style={{ color: COLORS[i % COLORS.length] }}>
                      {h.ticker.slice(0, 4)}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h4 className="font-semibold text-sm text-[#E8E4DA]">{h.asset_name}</h4>
                      <Moon className="w-3 h-3 text-[#D4C9A8]" />
                    </div>
                    <p className="text-xs text-[#8A8878]">
                      {h.quantity.toFixed(2)} units @ {fmt(h.purchase_price)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-sm text-[#E8E4DA]">{fmt(h.current_value || h.amount)}</p>
                  <p className={`text-xs ${(h.return_pct || 0) >= 0 ? 'text-[#A3B570]' : 'text-[#C65D4A]'}`}>
                    {formatPercent(h.return_pct || 0)}
                  </p>
                </div>
              </div>
            </SpotlightCard>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
