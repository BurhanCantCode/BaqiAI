import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

interface MovingBorderButtonProps {
  children: React.ReactNode
  className?: string
  containerClassName?: string
  borderColor?: string
  duration?: number
  onClick?: () => void
  disabled?: boolean
}

export function MovingBorderButton({
  children,
  className,
  containerClassName,
  borderColor = '#A3B570',
  duration = 3,
  onClick,
  disabled,
}: MovingBorderButtonProps) {
  return (
    <div className={cn('relative inline-block group', containerClassName)}>
      {/* Animated border */}
      <div className="absolute -inset-[2px] rounded-xl overflow-hidden">
        <motion.div
          className="absolute inset-0"
          style={{
            background: `conic-gradient(from 0deg, transparent 0%, ${borderColor} 10%, transparent 20%)`,
          }}
          animate={{ rotate: 360 }}
          transition={{ duration, repeat: Infinity, ease: 'linear' }}
        />
      </div>
      {/* Button */}
      <button
        onClick={onClick}
        disabled={disabled}
        className={cn(
          'relative z-10 rounded-xl bg-card px-6 py-3 font-medium transition-all',
          'hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed',
          className
        )}
      >
        {children}
      </button>
    </div>
  )
}
