import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { baqiApi } from '@/api/client'
import { formatMoney } from '@/lib/utils'
import { useApp } from '@/context/AppContext'
import UploadCSV from '@/components/UploadCSV'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { TextGenerate } from '@/components/ui/text-generate'
import { AnimatedCounter } from '@/components/ui/animated-counter'
import { Meteors } from '@/components/ui/meteors'
import { GlowingBorder } from '@/components/ui/glowing-border'
import { MovingBorderButton } from '@/components/ui/moving-border'
import {
  TrendingUp, Wallet, PiggyBank, AlertTriangle, Sparkles, ArrowRight, Bot,
  Loader2, FileSpreadsheet, Globe
} from 'lucide-react'

export default function Dashboard() {
  const { userId, user, analysis, loading, dataSource, setUserId, switchDataSource, refreshAll } = useApp()
  const [demoLoading, setDemoLoading] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const navigate = useNavigate()

  const handleUploadComplete = async (uploadData: any) => {
    setShowUploadModal(false)
    const uploadUserId = uploadData.user_id || 1
    switchDataSource('csv', uploadUserId)
  }

  const handleCSVClick = () => {
    setShowUploadModal(true)
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
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-[#A3B570]/10 flex items-center justify-center animate-glow-pulse">
            <Loader2 className="w-6 h-6 animate-spin text-[#A3B570]" />
          </div>
          <p className="text-sm text-[#8A8878]">Loading your financial data...</p>
        </div>
      </div>
    )
  }

  // Onboarding state — no data source chosen yet
  if (!dataSource || !analysis) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[75vh] text-center relative">
        {/* Meteors background */}
        <Meteors count={15} />

        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="mb-10 relative z-10"
        >
          <div className="w-20 h-20 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center mx-auto mb-6 animate-float glow-sage">
            <Bot className="w-10 h-10 text-[#A3B570]" />
          </div>
          <h1 className="text-5xl font-bold mb-4">
            <span className="text-gradient">BAQI AI</span>
          </h1>
          <div className="text-lg text-[#8A8878] max-w-lg mx-auto">
            <TextGenerate
              words="Discover your hidden investment potential. Our AI agents analyze your spending and build a personalized Shariah-compliant portfolio."
              delay={200}
            />
          </div>
        </motion.div>

        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="w-full max-w-2xl relative z-10"
        >
          <p className="text-xs text-[#8A8878] mb-4 font-medium uppercase tracking-wider">Choose your data source</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* CSV Upload Option */}
            <SpotlightCard
              className="cursor-pointer group"
              spotlightColor="rgba(163, 181, 112, 0.1)"
            >
              <div onClick={handleCSVClick}>
                <div className="w-11 h-11 rounded-xl bg-[#A3B570]/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <FileSpreadsheet className="w-5 h-5 text-[#A3B570]" />
                </div>
                <h3 className="font-bold text-lg mb-1 text-[#E8E4DA]">Upload Bank Statement</h3>
                <p className="text-sm text-[#8A8878] mb-3">
                  Upload your own CSV bank statement for personalized analysis.
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20 text-xs">Your Data</Badge>
                  <Badge variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20 text-xs">CSV</Badge>
                  <Badge variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20 text-xs">Instant</Badge>
                </div>
              </div>
            </SpotlightCard>

            {/* Demo Option */}
            <SpotlightCard
              className="cursor-pointer group"
              spotlightColor="rgba(212, 201, 168, 0.08)"
            >
              <div onClick={!demoLoading ? handleDemo : undefined}>
                <div className="w-11 h-11 rounded-xl bg-[#D4C9A8]/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Globe className="w-5 h-5 text-[#D4C9A8]" />
                </div>
                <h3 className="font-bold text-lg mb-1 text-[#E8E4DA]">Pakistani Demo Data</h3>
                <p className="text-sm text-[#8A8878] mb-3">
                  Explore with synthetic transaction data tailored to Pakistani spending patterns.
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-[#D4C9A8]/10 text-[#D4C9A8] border-[#D4C9A8]/20 text-xs">PKR</Badge>
                  <Badge variant="secondary" className="bg-[#D4C9A8]/10 text-[#D4C9A8] border-[#D4C9A8]/20 text-xs">Demo</Badge>
                  <Badge variant="secondary" className="bg-[#D4C9A8]/10 text-[#D4C9A8] border-[#D4C9A8]/20 text-xs">~5 sec</Badge>
                </div>
                {demoLoading && (
                  <div className="absolute inset-0 bg-card/90 flex items-center justify-center rounded-2xl z-20">
                    <Loader2 className="w-6 h-6 animate-spin text-[#A3B570]" />
                  </div>
                )}
              </div>
            </SpotlightCard>
          </div>

          {/* Upload Modal */}
          <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-card border-border">
              <UploadCSV
                userId={userId || undefined}
                onUploadComplete={handleUploadComplete}
                onCancel={() => setShowUploadModal(false)}
              />
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    )
  }

  // Dashboard with data
  const cur = analysis.currency
  const fmt = (v: number) => formatMoney(v, cur)
  const months = analysis.monthly_breakdown.length || 6

  const pieData = [
    { name: 'Fixed', value: analysis.fixed.percentage, color: '#6B7D3A' },
    { name: 'Discretionary', value: analysis.discretionary.percentage, color: '#A3B570' },
    { name: 'Watery', value: analysis.watery.percentage, color: '#D4C9A8' },
    { name: 'BAQI', value: analysis.savings_rate, color: '#8A9E5C' },
  ]

  const monthlyData = analysis.monthly_breakdown.map(m => ({
    ...m,
    month: m.month.slice(0, 7),
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-[#E8E4DA]">
            {user ? `Welcome back, ${user.name?.split(' ')[0] || 'there'}` : 'Welcome back'}
          </h1>
          <p className="text-sm text-[#8A8878] mt-1">
            {months}-month analysis
          </p>
        </div>
        <Badge variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20">
          {dataSource === 'csv' ? 'CSV Data' : 'Demo Data'}
        </Badge>
      </motion.div>

      {/* BAQI Highlight Card */}
      <GlowingBorder>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-[#8A8878] uppercase tracking-wider mb-1">Your Monthly BAQI</p>
              <p className="text-3xl font-bold text-[#A3B570]">
                <AnimatedCounter
                  value={analysis.baqi_amount / months}
                  formatter={(v) => formatMoney(v, cur)}
                />
              </p>
              <p className="text-xs text-[#8A8878] mt-2">
                {analysis.savings_rate.toFixed(1)}% savings rate • Potential: {fmt(analysis.recommended_investment / months)}/mo
              </p>
            </div>
            <div className="w-14 h-14 rounded-xl bg-[#A3B570]/10 flex items-center justify-center glow-sage">
              <TrendingUp className="w-7 h-7 text-[#A3B570]" />
            </div>
          </div>
        </div>
      </GlowingBorder>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SpotlightCard>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-[#6B7D3A]/15 flex items-center justify-center">
              <Wallet className="w-4 h-4 text-[#A3B570]" />
            </div>
            <p className="text-xs text-[#8A8878] uppercase tracking-wider">Total Income</p>
          </div>
          <p className="text-2xl font-bold text-[#E8E4DA]">
            <AnimatedCounter value={analysis.total_income} formatter={(v) => formatMoney(v, cur)} />
          </p>
          <p className="text-xs text-[#8A8878] mt-1">{fmt(analysis.total_income / months)}/month avg</p>
        </SpotlightCard>

        <SpotlightCard>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-[#D4C9A8]/10 flex items-center justify-center">
              <PiggyBank className="w-4 h-4 text-[#D4C9A8]" />
            </div>
            <p className="text-xs text-[#8A8878] uppercase tracking-wider">Total Expenses</p>
          </div>
          <p className="text-2xl font-bold text-[#E8E4DA]">
            <AnimatedCounter value={analysis.total_spending} formatter={(v) => formatMoney(v, cur)} />
          </p>
          <p className="text-xs text-[#8A8878] mt-1">{fmt(analysis.total_spending / months)}/month avg</p>
        </SpotlightCard>

        <SpotlightCard spotlightColor="rgba(198, 93, 74, 0.08)">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-[#C65D4A]/10 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-[#C65D4A]" />
            </div>
            <p className="text-xs text-[#8A8878] uppercase tracking-wider">Watery Spending</p>
          </div>
          <p className="text-2xl font-bold text-[#E8E4DA]">
            <AnimatedCounter value={analysis.watery.total} formatter={(v) => formatMoney(v, cur)} />
          </p>
          <p className="text-xs text-[#C65D4A] mt-1">{analysis.watery.percentage.toFixed(1)}% of expenses — reducible</p>
        </SpotlightCard>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Spending Pie */}
        <SpotlightCard className="lg:col-span-2">
          <h3 className="font-semibold text-sm text-[#D4C9A8] mb-4">Spending Breakdown</h3>
          <div className="flex items-center">
            <ResponsiveContainer width="50%" height={160}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={65} paddingAngle={3} dataKey="value">
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} stroke="transparent" />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2.5">
              {pieData.map(d => (
                <div key={d.name} className="flex items-center gap-2 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                  <span className="text-[#8A8878]">{d.name}</span>
                  <span className="ml-auto font-medium text-[#E8E4DA]">{d.value.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        </SpotlightCard>

        {/* Monthly Trend */}
        <SpotlightCard className="lg:col-span-3">
          <h3 className="font-semibold text-sm text-[#D4C9A8] mb-4">Monthly Trend</h3>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={monthlyData}>
              <defs>
                <linearGradient id="gradientIncome" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#A3B570" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#A3B570" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientExpense" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#D4C9A8" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#D4C9A8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#8A8878' }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Tooltip
                contentStyle={{
                  background: '#232B22',
                  border: '1px solid #333D30',
                  borderRadius: '10px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                  color: '#E8E4DA',
                  fontSize: '12px',
                }}
                formatter={(val: any) => fmt(Number(val))}
              />
              <Area type="monotone" dataKey="income" stroke="#A3B570" fill="url(#gradientIncome)" strokeWidth={2} />
              <Area type="monotone" dataKey="spending" stroke="#D4C9A8" fill="url(#gradientExpense)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </SpotlightCard>
      </div>

      {/* AI Recommendation CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card
          className="p-0 overflow-hidden cursor-pointer border-border hover:border-[#A3B570]/30 transition-all group"
          onClick={() => navigate('/invest')}
        >
          <div className="relative p-6 bg-gradient-to-r from-[#232B22] via-[#2C362A] to-[#232B22]">
            <div className="absolute inset-0 bg-gradient-to-r from-[#A3B570]/5 via-transparent to-[#6B7D3A]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="flex items-center justify-between relative z-10">
              <div>
                <Badge variant="secondary" className="mb-2 bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20 text-xs">
                  AI-Powered
                </Badge>
                <h3 className="text-lg font-bold mb-1 text-[#E8E4DA]">
                  Generate Investment Recommendation
                </h3>
                <p className="text-sm text-[#8A8878]">
                  Watch 5 AI agents collaborate to build your Shariah-compliant portfolio
                </p>
              </div>
              <div className="w-12 h-12 bg-[#A3B570]/10 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <ArrowRight className="w-6 h-6 text-[#A3B570]" />
              </div>
            </div>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}
