import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { GlowingBorder } from '@/components/ui/glowing-border'
import { Meteors } from '@/components/ui/meteors'
import {
  Settings, Send, Loader2, CheckCircle2, XCircle,
  CreditCard, BarChart3, MessageSquare, Users, Clock,
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

interface TelegramUser {
  id: number
  name: string
  telegram_id: string
}

interface NotificationLog {
  type: string
  user: string
  message: string
  success: boolean
  timestamp: string
}

export default function Admin() {
  const [users, setUsers] = useState<TelegramUser[]>([])
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [botOnline, setBotOnline] = useState(false)
  const [botUsername, setBotUsername] = useState<string | null>(null)

  // Simulate Transaction
  const [txUser, setTxUser] = useState<number | ''>('')
  const [txMerchant, setTxMerchant] = useState('')
  const [txAmount, setTxAmount] = useState('')
  const [txLoading, setTxLoading] = useState(false)
  const [txResult, setTxResult] = useState<string | null>(null)

  // Weekly Report
  const [reportUser, setReportUser] = useState<number | ''>('')
  const [reportLoading, setReportLoading] = useState(false)
  const [reportResult, setReportResult] = useState<string | null>(null)

  // Custom Notification
  const [notifUser, setNotifUser] = useState<number | ''>('')
  const [notifMessage, setNotifMessage] = useState('')
  const [notifLoading, setNotifLoading] = useState(false)
  const [notifResult, setNotifResult] = useState<string | null>(null)

  // Notification log
  const [logs, setLogs] = useState<NotificationLog[]>([])

  useEffect(() => {
    fetchUsers()
    fetchBotStatus()
  }, [])

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/users`)
      const data = await res.json()
      setUsers(data)
      if (data.length > 0) {
        setTxUser(data[0].id)
        setReportUser(data[0].id)
        setNotifUser(data[0].id)
      }
    } catch (e) {
      console.error('Failed to fetch users', e)
    } finally {
      setLoadingUsers(false)
    }
  }

  const fetchBotStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/telegram/status`)
      const data = await res.json()
      setBotOnline(data.running)
      setBotUsername(data.bot_username)
    } catch {
      setBotOnline(false)
    }
  }

  const addLog = (type: string, userId: number, message: string, success: boolean) => {
    const user = users.find(u => u.id === userId)
    setLogs(prev => [{
      type,
      user: user?.name || `User ${userId}`,
      message: message.slice(0, 120) + (message.length > 120 ? '...' : ''),
      success,
      timestamp: new Date().toLocaleTimeString(),
    }, ...prev].slice(0, 20))
  }

  const handleSimulateTransaction = async () => {
    if (!txUser || !txMerchant || !txAmount) return
    setTxLoading(true)
    setTxResult(null)
    try {
      const res = await fetch(
        `${API_URL}/admin/simulate-transaction?user_id=${txUser}&merchant=${encodeURIComponent(txMerchant)}&amount=${txAmount}`,
        { method: 'POST' }
      )
      const data = await res.json()
      if (res.ok) {
        setTxResult(data.notification)
        addLog('Transaction', txUser as number, data.notification, data.success)
      } else {
        setTxResult(`Error: ${data.detail}`)
        addLog('Transaction', txUser as number, data.detail, false)
      }
    } catch (e: any) {
      setTxResult(`Error: ${e.message}`)
      addLog('Transaction', txUser as number, e.message, false)
    } finally {
      setTxLoading(false)
    }
  }

  const handleSendReport = async () => {
    if (!reportUser) return
    setReportLoading(true)
    setReportResult(null)
    try {
      const res = await fetch(
        `${API_URL}/admin/send-weekly-report?user_id=${reportUser}`,
        { method: 'POST' }
      )
      const data = await res.json()
      if (res.ok) {
        setReportResult(data.report)
        addLog('Weekly Report', reportUser as number, 'Weekly report sent', data.success)
      } else {
        setReportResult(`Error: ${data.detail}`)
        addLog('Weekly Report', reportUser as number, data.detail, false)
      }
    } catch (e: any) {
      setReportResult(`Error: ${e.message}`)
      addLog('Weekly Report', reportUser as number, e.message, false)
    } finally {
      setReportLoading(false)
    }
  }

  const handleSendNotification = async () => {
    if (!notifUser || !notifMessage) return
    setNotifLoading(true)
    setNotifResult(null)
    try {
      const res = await fetch(
        `${API_URL}/admin/send-notification?user_id=${notifUser}&message=${encodeURIComponent(notifMessage)}`,
        { method: 'POST' }
      )
      const data = await res.json()
      if (res.ok) {
        setNotifResult(data.success ? 'Sent!' : 'Failed to send')
        addLog('Custom', notifUser as number, notifMessage, data.success)
      } else {
        setNotifResult(`Error: ${data.detail}`)
        addLog('Custom', notifUser as number, data.detail, false)
      }
    } catch (e: any) {
      setNotifResult(`Error: ${e.message}`)
      addLog('Custom', notifUser as number, e.message, false)
    } finally {
      setNotifLoading(false)
    }
  }

  const UserSelect = ({ value, onChange }: { value: number | '', onChange: (v: number) => void }) => (
    <select
      value={value}
      onChange={e => onChange(Number(e.target.value))}
      className="w-full px-3 py-2.5 rounded-lg bg-[#232B22] border border-[#333D30] text-sm text-[#E8E4DA] focus:outline-none focus:ring-1 focus:ring-[#A3B570]/30"
    >
      {loadingUsers ? (
        <option>Loading users...</option>
      ) : users.length === 0 ? (
        <option>No Telegram users found</option>
      ) : (
        users.map(u => (
          <option key={u.id} value={u.id}>{u.name} (ID: {u.telegram_id})</option>
        ))
      )}
    </select>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-[#E8E4DA]">Admin Control Panel</h1>
          <p className="text-sm text-[#8A8878] mt-1">
            Trigger bot notifications for demo — simulate transactions, send reports
          </p>
        </div>
      </motion.div>

      {/* Bot Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#232B22] border border-[#333D30]">
          {botOnline ? (
            <>
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-[#E8E4DA]">
                Bot Online — @{botUsername}
              </span>
            </>
          ) : (
            <>
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span className="text-sm text-[#8A8878]">Bot Offline — start the backend server first</span>
            </>
          )}
          <span className="ml-auto text-xs text-[#8A8878]">{users.length} registered user(s)</span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Simulate Transaction */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <GlowingBorder>
            <div className="p-5 relative overflow-hidden">
              <Meteors count={5} />
              <div className="relative z-10 space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-[#C65D4A]/10 flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-[#C65D4A]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#E8E4DA]">Simulate Transaction</h3>
                    <p className="text-xs text-[#8A8878]">Send a spending alert to Telegram</p>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-[#8A8878] mb-1 block">User</label>
                  <UserSelect value={txUser} onChange={setTxUser} />
                </div>

                <div>
                  <label className="text-xs text-[#8A8878] mb-1 block">Merchant Name</label>
                  <input
                    type="text"
                    value={txMerchant}
                    onChange={e => setTxMerchant(e.target.value)}
                    placeholder="e.g. Gia Italian Restaurant"
                    className="w-full px-3 py-2.5 rounded-lg bg-[#232B22] border border-[#333D30] text-sm text-[#E8E4DA] placeholder:text-[#8A8878]/50 focus:outline-none focus:ring-1 focus:ring-[#A3B570]/30"
                  />
                </div>

                <div>
                  <label className="text-xs text-[#8A8878] mb-1 block">Amount ($)</label>
                  <input
                    type="number"
                    value={txAmount}
                    onChange={e => setTxAmount(e.target.value)}
                    placeholder="42.00"
                    className="w-full px-3 py-2.5 rounded-lg bg-[#232B22] border border-[#333D30] text-sm text-[#E8E4DA] placeholder:text-[#8A8878]/50 focus:outline-none focus:ring-1 focus:ring-[#A3B570]/30"
                  />
                </div>

                <button
                  onClick={handleSimulateTransaction}
                  disabled={txLoading || !txUser || !txMerchant || !txAmount}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#C65D4A] hover:bg-[#C65D4A]/90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-all"
                >
                  {txLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {txLoading ? 'Generating alert...' : 'Send Alert'}
                </button>

                {txResult && (
                  <div className="p-3 rounded-lg bg-[#1B211A] border border-[#333D30] text-xs text-[#D4C9A8] whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {txResult}
                  </div>
                )}
              </div>
            </div>
          </GlowingBorder>
        </motion.div>

        {/* Weekly Report */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <GlowingBorder>
            <div className="p-5 relative overflow-hidden">
              <Meteors count={5} />
              <div className="relative z-10 space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-[#A3B570]/10 flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-[#A3B570]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#E8E4DA]">Weekly Report</h3>
                    <p className="text-xs text-[#8A8878]">Send spending summary to Telegram</p>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-[#8A8878] mb-1 block">User</label>
                  <UserSelect value={reportUser} onChange={setReportUser} />
                </div>

                <button
                  onClick={handleSendReport}
                  disabled={reportLoading || !reportUser}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#A3B570] hover:bg-[#A3B570]/90 disabled:opacity-40 disabled:cursor-not-allowed text-[#1B211A] rounded-lg text-sm font-medium transition-all"
                >
                  {reportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
                  {reportLoading ? 'Generating report...' : 'Send Weekly Report'}
                </button>

                {reportResult && (
                  <div className="p-3 rounded-lg bg-[#1B211A] border border-[#333D30] text-xs text-[#D4C9A8] whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {reportResult}
                  </div>
                )}
              </div>
            </div>
          </GlowingBorder>
        </motion.div>

        {/* Custom Notification */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <GlowingBorder>
            <div className="p-5 relative overflow-hidden">
              <Meteors count={5} />
              <div className="relative z-10 space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-[#0088cc]/10 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-[#0088cc]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#E8E4DA]">Custom Notification</h3>
                    <p className="text-xs text-[#8A8878]">Send any message via Telegram</p>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-[#8A8878] mb-1 block">User</label>
                  <UserSelect value={notifUser} onChange={setNotifUser} />
                </div>

                <div>
                  <label className="text-xs text-[#8A8878] mb-1 block">Message</label>
                  <textarea
                    value={notifMessage}
                    onChange={e => setNotifMessage(e.target.value)}
                    placeholder="Type your notification message..."
                    rows={3}
                    className="w-full px-3 py-2.5 rounded-lg bg-[#232B22] border border-[#333D30] text-sm text-[#E8E4DA] placeholder:text-[#8A8878]/50 focus:outline-none focus:ring-1 focus:ring-[#A3B570]/30 resize-none"
                  />
                </div>

                <button
                  onClick={handleSendNotification}
                  disabled={notifLoading || !notifUser || !notifMessage}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#0088cc] hover:bg-[#0088cc]/90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-all"
                >
                  {notifLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {notifLoading ? 'Sending...' : 'Send Notification'}
                </button>

                {notifResult && (
                  <div className="p-3 rounded-lg bg-[#1B211A] border border-[#333D30] text-xs text-[#D4C9A8]">
                    {notifResult}
                  </div>
                )}
              </div>
            </div>
          </GlowingBorder>
        </motion.div>

        {/* Recent Notifications Log */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <SpotlightCard spotlightColor="rgba(163, 181, 112, 0.06)">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#A3B570]/10 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-[#A3B570]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#E8E4DA]">Recent Notifications</h3>
                  <p className="text-xs text-[#8A8878]">In-memory log of sent notifications</p>
                </div>
              </div>

              {logs.length === 0 ? (
                <div className="text-center py-6 text-[#8A8878] text-xs">
                  No notifications sent yet. Use the controls above to send one!
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {logs.map((log, i) => (
                    <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-[#232B22]/50 border border-[#333D30]/50">
                      {log.success ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-500 mt-0.5 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-red-500 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-[#A3B570] font-medium">{log.type}</span>
                          <span className="text-[#8A8878]">{log.user}</span>
                          <span className="ml-auto text-[#8A8878]">{log.timestamp}</span>
                        </div>
                        <p className="text-xs text-[#D4C9A8] truncate mt-0.5">{log.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </SpotlightCard>
        </motion.div>
      </div>
    </div>
  )
}
