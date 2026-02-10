import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface TextGenerateProps {
  words: string
  className?: string
  delay?: number
}

export function TextGenerate({ words, className, delay = 0 }: TextGenerateProps) {
  const [started, setStarted] = useState(false)
  const wordArray = words.split(' ')

  useEffect(() => {
    const timer = setTimeout(() => setStarted(true), delay)
    return () => clearTimeout(timer)
  }, [delay])

  return (
    <div className={cn('inline', className)}>
      <AnimatePresence>
        {started && wordArray.map((word, i) => (
          <motion.span
            key={`${word}-${i}`}
            initial={{ opacity: 0, y: 10, filter: 'blur(8px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{
              duration: 0.4,
              delay: i * 0.08,
              ease: [0.2, 0.65, 0.3, 0.9],
            }}
            className="inline-block mr-[0.25em]"
          >
            {word}
          </motion.span>
        ))}
      </AnimatePresence>
    </div>
  )
}
