import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface AnimatedCounterProps {
  value: number
  duration?: number
  prefix?: string
  suffix?: string
  decimals?: number
  className?: string
  formatter?: (value: number) => string
}

export function AnimatedCounter({
  value,
  duration = 1500,
  prefix = '',
  suffix = '',
  decimals = 0,
  className,
  formatter,
}: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0)
  const prevValue = useRef(0)
  const frameRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    const startValue = prevValue.current
    const startTime = performance.now()

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = startValue + (value - startValue) * eased
      
      setDisplayValue(current)

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      } else {
        prevValue.current = value
      }
    }

    frameRef.current = requestAnimationFrame(animate)
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [value, duration])

  const formatted = formatter
    ? formatter(displayValue)
    : `${prefix}${displayValue.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}${suffix}`

  return <span className={cn('tabular-nums', className)}>{formatted}</span>
}
