import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { AgentStep } from '@/types'
import {
  BarChart3, Shield, TrendingUp, Moon, Briefcase, CheckCircle2, Loader2,
  Zap, ArrowRight
} from 'lucide-react'

const AGENT_CONFIGS: Omit<AgentStep, 'status' | 'output' | 'streamedText'>[] = [
  {
    id: 'spending',
    name: 'Spending Analyzer',
    role: 'Categorizing transactions into fixed, discretionary & watery spending...',
    icon: 'BarChart3',
    color: '#3b82f6',
  },
  {
    id: 'risk',
    name: 'Risk Profiler',
    role: 'Assessing investment risk tolerance based on quiz and demographics...',
    icon: 'Shield',
    color: '#8b5cf6',
  },
  {
    id: 'market',
    name: 'Market Analyst',
    role: 'Analyzing PSX stock data from BAQI Data Engine...',
    icon: 'TrendingUp',
    color: '#06b6d4',
  },
  {
    id: 'halal',
    name: 'Halal Compliance',
    role: 'Screening stocks against KMI-30 Shariah compliance criteria...',
    icon: 'Moon',
    color: '#f59e0b',
  },
  {
    id: 'investment',
    name: 'Investment Strategist',
    role: 'Building your personalized Shariah-compliant portfolio...',
    icon: 'Briefcase',
    color: '#10b981',
  },
]

const SIMULATED_STREAMS: Record<string, string[]> = {
  spending: [
    'Analyzing 6 months of transaction data...',
    'Fixed spending: rent (PKR 52,000), utilities (PKR 8,400), total 60.4%',
    'Discretionary: groceries, transport — 24.4% of income',
    'Watery spending detected: Foodpanda (PKR 12,800), Netflix, Sapphire — 15.2%',
    'Monthly BAQI (investable surplus): PKR 47,972',
    'Recommendation: Reduce food delivery by 40% to boost investment by PKR 5,120/month',
  ],
  risk: [
    'Processing risk quiz responses: [3, 4, 3, 2, 4]',
    'Base risk score: 3.2/5.0',
    'Age adjustment (28 years): +0.85 factor applied',
    'Final adjusted score: 3.4/5.0 → MODERATE risk profile',
    'Recommended allocation: 40% Equity, 30% Fixed Income, 30% Mutual Funds',
    'Time horizon compatible with growth-oriented PSX investments',
  ],
  market: [
    'Loading PSX stock data from BAQI Data Engine...',
    'Analyzing 20 KSE-100 stocks: predicted returns range 4–15%',
    'Top sectors by return: Technology (SYS +12%, TRG +15%), Oil & Gas (MARI +10%)',
    'Low PE opportunities: PSO (3.9), PPL (4.8), OGDC (5.2) — value plays',
    'Risk flags: NESTLE PE 28.5, TRG PE 25.0 — premium valuations',
    'Market outlook: BULLISH based on broad positive predicted returns',
  ],
  halal: [
    'Screening against KMI-30 Shariah compliance criteria...',
    'LUCK (Lucky Cement): HALAL — Manufacturing, debt/equity < 33%',
    'SYS (Systems Limited): HALAL — IT services, clean revenue',
    'TRG (TRG Pakistan): HALAL — Technology holding, compliant ratios',
    'MARI (Mari Petroleum): HALAL — Exploration, no haram revenue',
    'ENGRO: PARTIALLY COMPLIANT — Conglomerate, mixed revenue streams',
    '11 of 13 candidates passed Shariah screening',
  ],
  investment: [
    'Allocating PKR 48,000 across optimal Shariah-compliant assets...',
    '→ TRG Pakistan (14.1%): High-growth tech, +15% expected return',
    '→ Systems Limited (10.8%): IT blue-chip, +12% expected return',
    '→ Mari Petroleum (6.9%): Energy sector exposure, +10% return',
    '→ Lucky Cement (9.1%): Infrastructure play, +8% return',
    '→ Al Meezan Equity Fund (30%): Diversified Islamic fund, +18% return',
    '→ Al Meezan Income Fund (29.1%): Fixed income stability, +9% return',
    'Portfolio expected annual return: 12.75% | 100% Halal compliant',
  ],
}

const IconMap: Record<string, React.FC<any>> = {
  BarChart3, Shield, TrendingUp, Moon, Briefcase,
}

interface AgentPipelineProps {
  isRunning: boolean
  onComplete: () => void
}

export default function AgentPipeline({ isRunning, onComplete }: AgentPipelineProps) {
  const [agents, setAgents] = useState<AgentStep[]>(
    AGENT_CONFIGS.map(a => ({ ...a, status: 'waiting', output: '', streamedText: '' }))
  )
  const [currentAgent, setCurrentAgent] = useState(-1)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isRunning) return
    setAgents(AGENT_CONFIGS.map(a => ({ ...a, status: 'waiting', output: '', streamedText: '' })))
    setCurrentAgent(0)
  }, [isRunning])

  useEffect(() => {
    if (currentAgent < 0 || currentAgent >= AGENT_CONFIGS.length) return

    const agentId = AGENT_CONFIGS[currentAgent].id
    const lines = SIMULATED_STREAMS[agentId] || []

    // Mark agent as active
    setAgents(prev => prev.map((a, i) =>
      i === currentAgent ? { ...a, status: 'active' } : a
    ))

    let lineIdx = 0
    let charIdx = 0
    let currentText = ''

    const streamInterval = setInterval(() => {
      if (lineIdx >= lines.length) {
        clearInterval(streamInterval)
        // Mark done, move to next
        setAgents(prev => prev.map((a, i) =>
          i === currentAgent ? { ...a, status: 'done', output: lines.join('\n') } : a
        ))
        setTimeout(() => {
          if (currentAgent < AGENT_CONFIGS.length - 1) {
            setCurrentAgent(prev => prev + 1)
          } else {
            onComplete()
          }
        }, 500)
        return
      }

      const line = lines[lineIdx]
      if (charIdx < line.length) {
        currentText += line[charIdx]
        charIdx++
        setAgents(prev => prev.map((a, i) =>
          i === currentAgent ? { ...a, status: 'streaming', streamedText: currentText } : a
        ))
      } else {
        currentText += '\n'
        lineIdx++
        charIdx = 0
      }
    }, 25) // Fast typewriter speed

    return () => clearInterval(streamInterval)
  }, [currentAgent, onComplete])

  // Auto-scroll to active agent
  useEffect(() => {
    if (scrollRef.current && currentAgent >= 0) {
      const el = scrollRef.current.children[currentAgent] as HTMLElement
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [currentAgent])

  return (
    <div className="space-y-3" ref={scrollRef}>
      {/* Connection SVG lines between agents */}
      <div className="relative">
        {agents.map((agent, idx) => {
          const Icon = IconMap[agent.icon] || Briefcase
          const isActive = agent.status === 'active' || agent.status === 'streaming'
          const isDone = agent.status === 'done'
          const isWaiting = agent.status === 'waiting'

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1, duration: 0.4 }}
              className="mb-3"
            >
              {/* Connection line to next agent */}
              {idx < agents.length - 1 && (
                <div className="absolute left-6 ml-[1px] h-3 w-px" style={{
                  top: `calc(${idx * 100}% + 3rem)`,
                  background: isDone ? agent.color : '#e2e8f0',
                  transition: 'background 0.5s',
                }} />
              )}

              <div
                className={cn(
                  'rounded-xl border p-4 transition-all duration-500',
                  isActive && 'border-gradient glow-green',
                  isDone && 'border-primary/30 bg-primary/5',
                  isWaiting && 'border-border bg-card/50 opacity-50',
                  !isActive && !isDone && !isWaiting && 'border-border bg-card',
                )}
              >
                {/* Agent header */}
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-500',
                      isActive && 'animate-pulse',
                    )}
                    style={{
                      background: `${agent.color}20`,
                      boxShadow: isActive ? `0 0 20px ${agent.color}40` : 'none',
                    }}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-primary" />
                    ) : isActive ? (
                      <Loader2 className="w-5 h-5 animate-spin" style={{ color: agent.color }} />
                    ) : (
                      <Icon className="w-5 h-5" style={{ color: agent.color }} />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm">{agent.name}</h3>
                      {isActive && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="flex items-center gap-1 text-xs text-primary"
                        >
                          <Zap className="w-3 h-3" />
                          <span>LIVE</span>
                        </motion.div>
                      )}
                      {isDone && (
                        <span className="text-xs text-primary/70">Complete</span>
                      )}
                    </div>
                    {isWaiting && (
                      <p className="text-xs text-muted-foreground truncate">{agent.role}</p>
                    )}
                  </div>

                  {idx < agents.length - 1 && isDone && (
                    <ArrowRight className="w-4 h-4 text-primary/50" />
                  )}
                </div>

                {/* Streaming output */}
                <AnimatePresence>
                  {(isActive || isDone) && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-2 rounded-lg bg-muted/50 p-3 font-mono text-xs leading-relaxed">
                        {isDone ? (
                          agent.output.split('\n').map((line, i) => (
                            <motion.div
                              key={i}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="text-muted-foreground"
                            >
                              <span className="text-primary/40 mr-2">{'>'}</span>
                              {line}
                            </motion.div>
                          ))
                        ) : (
                          <div>
                            {agent.streamedText.split('\n').map((line, i) => (
                              <div key={i} className="text-foreground/80">
                                {line && <span className="text-primary/40 mr-2">{'>'}</span>}
                                {line}
                              </div>
                            ))}
                            <span className="animate-cursor" />
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
