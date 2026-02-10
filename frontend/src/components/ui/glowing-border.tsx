import { cn } from '@/lib/utils'

interface GlowingBorderProps {
  children: React.ReactNode
  className?: string
  glowColor?: string
  borderRadius?: string
}

export function GlowingBorder({
  children,
  className,
  glowColor = '#A3B570',
  borderRadius = '1rem',
}: GlowingBorderProps) {
  return (
    <div className={cn('relative group', className)}>
      {/* Animated glow */}
      <div
        className="absolute -inset-[1px] rounded-[inherit] opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm"
        style={{
          background: `linear-gradient(135deg, ${glowColor}, transparent, ${glowColor})`,
          borderRadius,
        }}
      />
      {/* Border */}
      <div
        className="absolute -inset-[1px] rounded-[inherit] opacity-30 group-hover:opacity-60 transition-opacity duration-500"
        style={{
          background: `linear-gradient(135deg, ${glowColor}40, transparent, ${glowColor}40)`,
          borderRadius,
        }}
      />
      {/* Content */}
      <div className="relative bg-card rounded-[inherit] overflow-hidden">
        {children}
      </div>
    </div>
  )
}
