import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { baqiApi } from '@/api/client'
import { formatPKR } from '@/lib/utils'
import type { SpendingAnalysis, User } from '@/types'
import {
  TrendingUp, Wallet, PiggyBank, AlertTriangle, Sparkles, ArrowRight, Bot,
  Loader2
} from 'lucide-react'

export default function Dashboard() {
  const [analysis, setAnalysis] = useState<SpendingAnalysis | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [demoLoading, setDemoLoading] = useState(false)
  const navigate = useNavigate()

  const userId = Number(localStorage.getItem('baqi_user_id') || '0')

  useEffect(() => {
    if (!userId) { setLoading(false); return }
    loadData()
  }, [userId])

  const loadData = async () => {
    try {
      const [profileRes, analysisRes] = await Promise.all([
        baqiApi.getProfile(userId),
        baqiApi.getAnalysis(userId),
      ])
      setUser(profileRes.data)
      setAnalysis(analysisRes.data)
    } catch {
      // User might not exist yet
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = async () => {
    setDemoLoading(true)
    try {
      const res = await baqiApi.generateSyntheticData()
      const newUserId = res.data.user_id
      localStorage.setItem('baqi_user_id', String(newUserId))
      window.location.reload()
    } catch (err) {
      console.error(err)
    } finally {
      setDemoLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  // Onboarding state — no user yet
  if (!userId || !analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="w-24 h-24 rounded-2xl bg-primary/10 flex items-center justify-center glow-green animate-float mx-auto mb-6">
            <Bot className="w-12 h-12 text-primary" />
          </div>
          <h1 className="text-4xl font-bold mb-3">
            <span className="text-gradient">BAQI AI</span>
          </h1>
          <p className="text-muted-foreground max-w-md mx-auto text-lg">
            Discover your hidden investment potential. Our AI agents analyze your spending
            and build a personalized Shariah-compliant portfolio.
          </p>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Button
            size="lg"
            onClick={handleDemo}
            disabled={demoLoading}
            className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-8 py-6 text-lg rounded-xl glow-green"
          >
            {demoLoading ? (
              <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Setting up demo...</>
            ) : (
              <><Sparkles className="w-5 h-5 mr-2" /> Try Demo — Generate Sample Data</>
            )}
          </Button>
          <p className="text-xs text-muted-foreground mt-3">
            Creates a demo profile with 6 months of realistic PKR transactions
          </p>
        </motion.div>
      </div>
    )
  }

  // Dashboard with data
  const pieData = [
    { name: 'Fixed', value: analysis.fixed.percentage, color: '#3b82f6' },
    { name: 'Discretionary', value: analysis.discretionary.percentage, color: '#8b5cf6' },
    { name: 'Watery', value: analysis.watery.percentage, color: '#f59e0b' },
    { name: 'BAQI', value: analysis.savings_rate, color: '#10b981' },
  ]

  const monthlyData = analysis.monthly_breakdown.map(m => ({
    ...m,
    month: m.month.slice(0, 7),
  }))

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">
          Welcome back, <span className="text-gradient">{user?.name || 'User'}</span>
        </h1>
        <p className="text-muted-foreground text-sm">
          Here's your financial overview — {user?.risk_profile} risk profile
        </p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Total Income', value: formatPKR(analysis.total_income), icon: Wallet, color: 'text-blue-400' },
          { label: 'Total Spending', value: formatPKR(analysis.total_spending), icon: AlertTriangle, color: 'text-amber-400' },
          { label: 'Savings Rate', value: `${analysis.savings_rate.toFixed(1)}%`, icon: PiggyBank, color: 'text-purple-400' },
          { label: 'Monthly BAQI', value: formatPKR(analysis.baqi_amount / 6), icon: TrendingUp, color: 'text-emerald-400' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className="p-4 bg-card border-border/50 hover:border-primary/30 transition-all">
              <stat.icon className={`w-5 h-5 ${stat.color} mb-2`} />
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-lg font-bold">{stat.value}</p>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Spending Pie */}
        <Card className="p-5 bg-card border-border/50">
          <h3 className="font-semibold mb-4">Spending Breakdown</h3>
          <div className="flex items-center">
            <ResponsiveContainer width="50%" height={180}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} stroke="transparent" />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {pieData.map(d => (
                <div key={d.name} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full" style={{ background: d.color }} />
                  <span className="text-muted-foreground">{d.name}</span>
                  <span className="ml-auto font-medium">{d.value.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Monthly Trend */}
        <Card className="p-5 bg-card border-border/50">
          <h3 className="font-semibold mb-4">Monthly Trend</h3>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={monthlyData}>
              <defs>
                <linearGradient id="green" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="red" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ background: '#111118', border: '1px solid #1e293b', borderRadius: '8px' }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(val: any) => formatPKR(Number(val))}
              />
              <Area type="monotone" dataKey="income" stroke="#10b981" fill="url(#green)" />
              <Area type="monotone" dataKey="spending" stroke="#ef4444" fill="url(#red)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* CTA: AI Recommendation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Card
          className="p-6 border-gradient cursor-pointer hover:scale-[1.01] transition-transform"
          onClick={() => navigate('/invest')}
        >
          <div className="flex items-center justify-between">
            <div>
              <Badge variant="secondary" className="mb-2 bg-primary/10 text-primary border-primary/20">
                AI-Powered
              </Badge>
              <h3 className="text-xl font-bold mb-1">Generate Investment Recommendation</h3>
              <p className="text-sm text-muted-foreground">
                Watch 5 AI agents collaborate live to build your personalized portfolio
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center glow-green">
              <ArrowRight className="w-6 h-6 text-primary" />
            </div>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}
