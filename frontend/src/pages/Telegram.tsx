import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { GlowingBorder } from '@/components/ui/glowing-border'
import { Meteors } from '@/components/ui/meteors'
import {
  Send, CheckCircle2, Loader2,
  Shield, Zap, ArrowRight, RefreshCw, XCircle,
  MessageCircle, BarChart3, Brain, ExternalLink
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export default function Telegram() {
  const [status, setStatus] = useState<'loading' | 'bot_offline' | 'connected'>('loading')
  const [botUsername, setBotUsername] = useState<string | null>(null)
  const [botLink, setBotLink] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/telegram/status`)
      const data = await res.json()

      if (data.running) {
        setStatus('connected')
        setBotUsername(data.bot_username)
        setBotLink(data.bot_link)
      } else {
        setStatus('bot_offline')
        setBotUsername(null)
        setBotLink(null)
      }
    } catch {
      setStatus('bot_offline')
      setBotUsername(null)
      setBotLink(null)
    }
  }

  useEffect(() => {
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, 5000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  // Stop polling once connected
  useEffect(() => {
    if (status === 'connected' && pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [status])

  const features = [
    {
      icon: BarChart3,
      title: 'Spending Alerts',
      desc: 'Get notified when you overspend on coffee, food, or shopping with detailed breakdowns',
    },
    {
      icon: MessageCircle,
      title: 'Chat Commands',
      desc: 'Send /balance, /spending, or /insights to get instant financial data',
    },
    {
      icon: Zap,
      title: 'Smart Notifications',
      desc: 'Proactive alerts when unusual spending patterns are detected',
    },
    {
      icon: Shield,
      title: 'Shariah Insights',
      desc: 'Receive Halal-compliant investment suggestions via chat',
    },
    {
      icon: Brain,
      title: 'AI Persona Analysis',
      desc: 'Understand your spending personality and get tailored tips',
    },
  ]

  const commands = [
    { cmd: '/start', desc: 'Welcome message & account setup' },
    { cmd: '/balance', desc: 'Income, expenses & investable surplus' },
    { cmd: '/spending', desc: 'Category breakdown + overspending alerts' },
    { cmd: '/insights', desc: 'AI-powered financial tips & persona' },
    { cmd: '/help', desc: 'Show all available commands' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-[#E8E4DA]">Telegram Assistant</h1>
          <p className="text-sm text-[#8A8878] mt-1">
            Your personal financial assistant — track spending & get alerts on Telegram
          </p>
        </div>
      </motion.div>

      {/* Connection Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <GlowingBorder>
          <div className="p-6 relative overflow-hidden">
            <Meteors count={8} />
            <div className="relative z-10">
              <div className="flex items-start gap-6">
                {/* Left — Status */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-12 h-12 rounded-xl bg-[#0088cc]/10 flex items-center justify-center">
                      <Send className="w-6 h-6 text-[#0088cc]" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-[#E8E4DA]">Telegram Bot</h2>
                      <p className="text-xs text-[#8A8878]">Connect via Telegram to receive financial alerts & manage your finances</p>
                    </div>
                  </div>

                  {/* Loading */}
                  {status === 'loading' && (
                    <div className="flex items-center gap-3 text-[#8A8878] py-6">
                      <Loader2 className="w-5 h-5 animate-spin text-[#0088cc]" />
                      <span className="text-sm">Checking bot status...</span>
                    </div>
                  )}

                  {/* Bot Offline */}
                  {status === 'bot_offline' && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 px-3 py-2 bg-[#C65D4A]/10 border border-[#C65D4A]/20 rounded-lg">
                        <XCircle className="w-4 h-4 text-[#C65D4A]" />
                        <span className="text-sm text-[#C65D4A]">Bot is not running</span>
                      </div>
                      <div className="bg-[#232B22] border border-[#333D30] rounded-xl p-4">
                        <p className="text-xs text-[#8A8878] mb-2">To start the Telegram bot:</p>
                        <div className="space-y-2">
                          <div>
                            <p className="text-xs text-[#8A8878] mb-1">1. Create a bot via <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="text-[#0088cc] hover:underline">@BotFather</a> on Telegram</p>
                          </div>
                          <div>
                            <p className="text-xs text-[#8A8878] mb-1">2. Add the token to your <code className="text-[#A3B570]">.env</code> file:</p>
                            <code className="block bg-[#1B211A] border border-[#333D30] rounded-lg px-3 py-2 text-xs text-[#A3B570] font-mono">
                              TELEGRAM_BOT_TOKEN=your_token_here
                            </code>
                          </div>
                          <div>
                            <p className="text-xs text-[#8A8878] mb-1">3. Restart the backend server:</p>
                            <code className="block bg-[#1B211A] border border-[#333D30] rounded-lg px-3 py-2 text-xs text-[#A3B570] font-mono">
                              uvicorn app.main:app --reload --port 8000
                            </code>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={fetchStatus}
                        className="flex items-center gap-2 px-4 py-2 bg-[#232B22] border border-[#333D30] text-[#8A8878] hover:text-[#E8E4DA] rounded-lg text-sm transition-all"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        Retry Connection
                      </button>
                    </div>
                  )}

                  {/* Connected */}
                  {status === 'connected' && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 px-3 py-2 bg-[#0088cc]/10 border border-[#0088cc]/20 rounded-lg">
                        <CheckCircle2 className="w-4 h-4 text-[#0088cc]" />
                        <span className="text-sm text-[#0088cc] font-medium">
                          Bot is running{botUsername ? ` — @${botUsername}` : ''}
                        </span>
                      </div>
                      <p className="text-sm text-[#8A8878]">
                        Your Telegram bot is live! Open the bot and send <span className="text-[#A3B570] font-medium">/start</span> to get started.
                        You'll receive spending alerts and can query your financial data anytime.
                      </p>
                      {botLink && (
                        <a
                          href={botLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#0088cc] hover:bg-[#0088cc]/90 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-[#0088cc]/20 hover:shadow-[#0088cc]/30"
                        >
                          <Send className="w-4 h-4" />
                          Open in Telegram
                          <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                        </a>
                      )}
                    </div>
                  )}
                </div>

                {/* Right — Bot Icon or Connected Icon */}
                <div className="hidden md:flex flex-col items-center justify-center">
                  {status === 'connected' ? (
                    <div className="w-32 h-32 rounded-2xl bg-[#0088cc]/10 flex items-center justify-center animate-float">
                      <CheckCircle2 className="w-16 h-16 text-[#0088cc]" />
                    </div>
                  ) : (
                    <div className="w-32 h-32 rounded-2xl bg-[#0088cc]/10 flex items-center justify-center animate-float">
                      <Send className="w-12 h-12 text-[#0088cc]/50" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </GlowingBorder>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h3 className="text-sm font-semibold text-[#D4C9A8] mb-3">What you can do</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {features.map((feat, i) => (
            <SpotlightCard key={i} spotlightColor="rgba(0, 136, 204, 0.06)">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-[#0088cc]/10 flex items-center justify-center flex-shrink-0">
                  <feat.icon className="w-4 h-4 text-[#0088cc]" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-[#E8E4DA] mb-1">{feat.title}</h4>
                  <p className="text-xs text-[#8A8878]">{feat.desc}</p>
                </div>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </motion.div>

      {/* Commands Reference */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <SpotlightCard spotlightColor="rgba(0, 136, 204, 0.05)">
          <h3 className="text-sm font-semibold text-[#D4C9A8] mb-4">Available Commands</h3>
          <div className="space-y-2.5">
            {commands.map((cmd, i) => (
              <div key={i} className="flex items-center gap-3 group">
                <div className="flex items-center gap-2 min-w-[120px]">
                  <Send className="w-3 h-3 text-[#0088cc]/50" />
                  <code className="text-sm font-mono text-[#0088cc] font-medium">{cmd.cmd}</code>
                </div>
                <ArrowRight className="w-3 h-3 text-[#333D30]" />
                <span className="text-xs text-[#8A8878]">{cmd.desc}</span>
              </div>
            ))}
          </div>
        </SpotlightCard>
      </motion.div>

      {/* How It Works */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <SpotlightCard spotlightColor="rgba(0, 136, 204, 0.04)">
          <h3 className="text-sm font-semibold text-[#D4C9A8] mb-4">How Spending Alerts Work</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-[#0088cc]/10 flex items-center justify-center flex-shrink-0 text-xs font-bold text-[#0088cc]">1</div>
              <div>
                <p className="text-sm text-[#E8E4DA]">Your spending data is analyzed automatically</p>
                <p className="text-xs text-[#8A8878]">Categories: fixed, discretionary, and watery (reducible) expenses</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-[#0088cc]/10 flex items-center justify-center flex-shrink-0 text-xs font-bold text-[#0088cc]">2</div>
              <div>
                <p className="text-sm text-[#E8E4DA]">The bot identifies overspending patterns</p>
                <p className="text-xs text-[#8A8878]">E.g., "You spent PKR 15,000 on coffee this month — that's 40% above average!"</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-[#0088cc]/10 flex items-center justify-center flex-shrink-0 text-xs font-bold text-[#0088cc]">3</div>
              <div>
                <p className="text-sm text-[#E8E4DA]">Get personalized financial tips</p>
                <p className="text-xs text-[#8A8878]">AI persona analysis + actionable savings recommendations + monthly trends</p>
              </div>
            </div>
          </div>
        </SpotlightCard>
      </motion.div>
    </div>
  )
}
