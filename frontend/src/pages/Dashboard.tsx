import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { baqiApi } from '@/api/client'
import { formatMoney } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import {
  TrendingUp, Wallet, PiggyBank, AlertTriangle, Sparkles, ArrowRight, Bot,
  Loader2, FileSpreadsheet, Globe
} from 'lucide-react'

export default function Dashboard() {
  const { userId, user, analysis, loading, dataSource, setUserId, switchDataSource, refreshAll } = useApp()
  const [demoLoading, setDemoLoading] = useState(false)
  const [csvLoading, setCsvLoading] = useState(false)
  const navigate = useNavigate()

  const handleCSV = async () => {
    setCsvLoading(true)
    try {
      switchDataSource('csv', 1)
    } catch (err) {
      console.error(err)
    } finally {
      setCsvLoading(false)
    }
  }

  const handleDemo = async () => {
    setDemoLoading(true)
    try {
      const res = await baqiApi.generateSyntheticData()
      const newUserId = res.data.user_id
      switchDataSource('supabase', newUserId)
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

  // Onboarding state — no data source chosen yet
  if (!dataSource || !analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] text-center animate-fade-in-up">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="w-24 h-24 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6 animate-float">
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
          className="w-full max-w-2xl"
        >
          <p className="text-sm text-muted-foreground mb-4 font-medium">Choose your data source</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* CSV Option */}
            <Card
              className="p-6 cursor-pointer hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all group relative overflow-hidden"
              onClick={!csvLoading && !demoLoading ? handleCSV : undefined}
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl -mr-16 -mt-16" />
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <FileSpreadsheet className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-bold text-lg mb-1">Real Bank Statement</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Analyze actual transaction data from a US bank account — 18 months of real spending.
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-blue-200 text-xs">USD</Badge>
                  <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-blue-200 text-xs">3,000+ txns</Badge>
                  <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-blue-200 text-xs">Instant</Badge>
                </div>
                {csvLoading && (
                  <div className="absolute inset-0 bg-background/80 flex items-center justify-center rounded-lg">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                )}
              </div>
            </Card>

            {/* Demo Option */}
            <Card
              className="p-6 cursor-pointer hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all group relative overflow-hidden"
              onClick={!csvLoading && !demoLoading ? handleDemo : undefined}
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl -mr-16 -mt-16" />
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Globe className="w-6 h-6 text-emerald-600" />
                </div>
                <h3 className="font-bold text-lg mb-1">Pakistani Demo Data</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Generate a realistic Pakistani banking profile with 6 months of synthetic PKR transactions.
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-emerald-50 text-emerald-600 border-emerald-200 text-xs">PKR</Badge>
                  <Badge variant="secondary" className="bg-emerald-50 text-emerald-600 border-emerald-200 text-xs">Synthetic</Badge>
                  <Badge variant="secondary" className="bg-emerald-50 text-emerald-600 border-emerald-200 text-xs">~5 sec</Badge>
                </div>
                {demoLoading && (
                  <div className="absolute inset-0 bg-background/80 flex items-center justify-center rounded-lg">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                )}
              </div>
            </Card>
          </div>
        </motion.div>
      </div>
    )
  }

  // Dashboard with data
  const cur = analysis.currency
  const fmt = (v: number) => formatMoney(v, cur)
  const months = analysis.monthly_breakdown.length || 6

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

  const stats = [
    { label: 'Total Income', value: fmt(analysis.total_income), icon: Wallet, color: 'bg-blue-50 text-blue-600', change: `${months} months` },
    { label: 'Total Spending', value: fmt(analysis.total_spending), icon: AlertTriangle, color: 'bg-amber-50 text-amber-600', change: `${(100 - analysis.savings_rate).toFixed(1)}%` },
    { label: 'Savings Rate', value: `${analysis.savings_rate.toFixed(1)}%`, icon: PiggyBank, color: 'bg-purple-50 text-purple-600', change: 'of income' },
    { label: 'Monthly BAQI', value: fmt(analysis.baqi_amount / months), icon: TrendingUp, color: 'bg-emerald-50 text-emerald-600', change: 'investable' },
  ]

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {user ? (
              <>Welcome back, <span className="text-gradient">{user.name}</span></>
            ) : (
              <><span className="text-gradient">BAQI AI</span> Dashboard</>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">
            {dataSource === 'csv'
              ? `Real bank statement analysis — ${months} months of transaction data`
              : `Financial overview — ${user?.risk_profile || 'moderate'} risk profile`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {dataSource === 'csv' && (
            <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-blue-200">
              Live Data · USD
            </Badge>
          )}
          {dataSource === 'supabase' && (
            <Badge variant="secondary" className="bg-emerald-50 text-emerald-600 border-emerald-200">
              Demo · PKR
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-muted-foreground"
            onClick={() => {
              localStorage.removeItem('baqi_data_source')
              localStorage.removeItem('baqi_user_id')
              window.location.reload()
            }}
          >
            Switch Source
          </Button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className="card-soft">
              <CardContent className="p-0 space-y-3">
                <div className="flex items-center justify-between">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${stat.color}`}>
                    <stat.icon className="w-5 h-5" />
                  </div>
                  <Badge variant="secondary" className="bg-muted text-muted-foreground text-xs">
                    {stat.change}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground font-medium">{stat.label}</p>
                  <h3 className="text-2xl font-bold mt-0.5">{stat.value}</h3>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Trend — 2 col */}
        <Card className="card-soft lg:col-span-2 overflow-hidden">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold">Monthly Income vs Spending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthlyData}>
                  <defs>
                    <linearGradient id="green" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="red" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v: any) => `${cur === 'PKR' ? '' : '$'}${(v/1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 20px rgba(0,0,0,0.05)', background: '#fff' }}
                    formatter={(val: any) => fmt(Number(val))}
                  />
                  <Area type="monotone" dataKey="income" stroke="#10b981" strokeWidth={2} fill="url(#green)" />
                  <Area type="monotone" dataKey="spending" stroke="#ef4444" strokeWidth={2} fill="url(#red)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Spending Breakdown Pie */}
        <Card className="card-soft">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold">Spending Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} stroke="transparent" />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-2">
              {pieData.map(d => (
                <div key={d.name} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full" style={{ background: d.color }} />
                  <span className="text-muted-foreground">{d.name}</span>
                  <span className="ml-auto font-semibold">{d.value.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* CTA: AI Recommendation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Card
          className="card-soft bg-primary text-primary-foreground relative overflow-hidden border-none shadow-xl shadow-primary/20 cursor-pointer hover:scale-[1.01] transition-transform"
          onClick={() => navigate('/invest')}
        >
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32" />
          <CardContent className="pt-6 relative z-10">
            <div className="flex items-center justify-between">
              <div>
                <Badge variant="secondary" className="mb-2 bg-white/20 text-white border-white/20">
                  AI-Powered
                </Badge>
                <h3 className="text-xl font-bold mb-1">Generate Investment Recommendation</h3>
                <p className="text-sm text-blue-100">
                  Watch 5 AI agents collaborate live to build your personalized Shariah-compliant portfolio
                </p>
              </div>
              <div className="w-14 h-14 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center shrink-0 ml-4">
                <ArrowRight className="w-7 h-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
