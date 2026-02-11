import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { Meteors } from '@/components/ui/meteors'
import { useApp } from '@/context/AppContext'
import { baqiApi } from '@/api/client'
import {
  MessageSquare, Send, Trash2, Loader2, Bot, User,
  Wifi, WifiOff, Sparkles
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function Chat() {
  const { userId, dataSource } = useApp()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ollamaOnline, setOllamaOnline] = useState<boolean | null>(null)
  const [modelName, setModelName] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Check Ollama status on mount
  useEffect(() => {
    baqiApi.getChatStatus()
      .then(res => {
        setOllamaOnline(res.data.online)
        setModelName(res.data.model || '')
      })
      .catch(() => setOllamaOnline(false))
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // Load history on mount
  useEffect(() => {
    const id = userId || 1
    baqiApi.getChatHistory(id)
      .then(res => {
        if (res.data.messages?.length) {
          setMessages(res.data.messages)
        }
      })
      .catch(() => {})
  }, [userId])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    const id = userId || 1
    const source = dataSource || 'csv'

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    // Add placeholder assistant message for streaming
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const resp = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: id, message: text, data_source: source }),
      })

      if (!resp.ok || !resp.body) {
        // Fallback to non-streaming
        const fallback = await baqiApi.sendChatMessage({ user_id: id, message: text, data_source: source })
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = { role: 'assistant', content: fallback.data.reply }
          return updated
        })
        setLoading(false)
        return
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') break
            try {
              const parsed = JSON.parse(data)
              if (parsed.token) {
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + parsed.token,
                  }
                  return updated
                })
              }
            } catch {}
          }
        }
      }
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Failed to connect. Make sure Ollama is running (`ollama serve`).',
        }
        return updated
      })
    }

    setLoading(false)
    inputRef.current?.focus()
  }, [input, loading, userId, dataSource])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = async () => {
    const id = userId || 1
    try {
      await baqiApi.clearChatHistory(id)
    } catch {}
    setMessages([])
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-7rem)]">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              <span className="text-gradient">AI Chat</span>
            </h1>
            <p className="text-[#8A8878] text-sm mt-1">
              Chat with your local AI financial assistant
            </p>
          </div>
          <div className="flex items-center gap-2">
            {ollamaOnline === null ? (
              <Badge variant="secondary" className="bg-[#333D30] text-[#8A8878]">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" /> Checking...
              </Badge>
            ) : ollamaOnline ? (
              <Badge variant="secondary" className="bg-[#A3B570]/10 text-[#A3B570] border-[#A3B570]/20">
                <Wifi className="w-3 h-3 mr-1" /> Ollama Online
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-[#C65D4A]/10 text-[#C65D4A] border-[#C65D4A]/20">
                <WifiOff className="w-3 h-3 mr-1" /> Ollama Offline
              </Badge>
            )}
            {modelName && ollamaOnline && (
              <Badge variant="secondary" className="bg-[#D4C9A8]/10 text-[#D4C9A8] border-[#D4C9A8]/20">
                {modelName}
              </Badge>
            )}
          </div>
        </div>
      </motion.div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 rounded-xl border border-[#333D30]/50 bg-[#1B211A]/50 overflow-hidden flex flex-col">
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center h-full text-center relative"
            >
              <Meteors count={6} />
              <div className="w-16 h-16 rounded-2xl bg-[#A3B570]/10 flex items-center justify-center glow-sage mb-4 relative z-10">
                <Sparkles className="w-8 h-8 text-[#A3B570]" />
              </div>
              <h3 className="text-lg font-semibold text-[#E8E4DA] mb-2 relative z-10">
                Ask me anything about your finances
              </h3>
              <p className="text-sm text-[#8A8878] max-w-md relative z-10">
                I have your complete spending history. Ask about budgets, savings opportunities,
                merchant spending, or investment advice — all powered by your local AI.
              </p>
              <div className="flex flex-wrap gap-2 mt-4 relative z-10">
                {[
                  'How much do I spend on food?',
                  'Help me save $300/month',
                  'What are my subscriptions?',
                  'Am I on track with savings?',
                ].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => { setInput(suggestion); inputRef.current?.focus() }}
                    className="px-3 py-1.5 rounded-lg bg-[#2C362A] border border-[#333D30] text-xs text-[#D4C9A8] hover:border-[#A3B570]/30 hover:text-[#E8E4DA] transition-all"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </motion.div>
          ) : (
            <AnimatePresence initial={false}>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-[#A3B570]/15 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-4 h-4 text-[#A3B570]" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-[#A3B570]/15 text-[#E8E4DA] border border-[#A3B570]/20'
                        : 'bg-[#232B22] text-[#E8E4DA] border border-[#333D30]/50'
                    }`}
                  >
                    {msg.content || (
                      <span className="flex items-center gap-2 text-[#8A8878]">
                        <Loader2 className="w-3 h-3 animate-spin" /> Thinking...
                      </span>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-[#2C362A] border border-[#333D30] flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4 text-[#8A8878]" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-[#333D30]/50 p-3 bg-[#1B211A]">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={ollamaOnline === false ? 'Ollama is offline — start it first' : 'Ask about your spending, savings, investments...'}
              disabled={loading || ollamaOnline === false}
              rows={1}
              className="flex-1 bg-[#232B22] border border-[#333D30] rounded-lg px-4 py-3 text-sm text-[#E8E4DA] placeholder:text-[#8A8878] focus:outline-none focus:ring-1 focus:ring-[#A3B570]/30 resize-none disabled:opacity-50"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || loading || ollamaOnline === false}
              className="bg-[#A3B570] hover:bg-[#8A9E5C] text-[#1B211A] px-4 rounded-lg shrink-0"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between mt-2">
            <span className="text-[10px] text-[#8A8878]">
              Powered by Ollama (local) &middot; Your data stays on your machine
            </span>
            {messages.length > 0 && (
              <button
                onClick={handleClear}
                className="flex items-center gap-1 text-[10px] text-[#8A8878] hover:text-[#C65D4A] transition-colors"
              >
                <Trash2 className="w-3 h-3" /> Clear chat
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
