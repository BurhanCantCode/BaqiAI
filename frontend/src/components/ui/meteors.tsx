import { cn } from '@/lib/utils'

interface MeteorsProps {
  count?: number
  className?: string
}

export function Meteors({ count = 12, className }: MeteorsProps) {
  const meteors = Array.from({ length: count }, (_, i) => {
    const delay = Math.random() * 4
    const duration = 1.5 + Math.random() * 2
    const left = `${Math.random() * 100}%`
    const size = 1 + Math.random() * 1.5

    return (
      <span
        key={i}
        className="absolute top-1/2 left-1/2 rotate-[215deg]"
        style={{
          left,
          top: '-5%',
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: '50%',
          background: '#A3B570',
          boxShadow: `0 0 0 1px rgba(163, 181, 112, 0.05), 0 0 3px 1px rgba(163, 181, 112, 0.15)`,
          animation: `meteor ${duration}s linear ${delay}s infinite`,
        }}
      >
        {/* Tail */}
        <div
          className="absolute top-1/2 -translate-y-1/2"
          style={{
            width: `${40 + Math.random() * 60}px`,
            height: '1px',
            background: 'linear-gradient(90deg, #A3B570, transparent)',
            right: '100%',
          }}
        />
      </span>
    )
  })

  return (
    <div className={cn('absolute inset-0 overflow-hidden pointer-events-none', className)}>
      {meteors}
    </div>
  )
}
