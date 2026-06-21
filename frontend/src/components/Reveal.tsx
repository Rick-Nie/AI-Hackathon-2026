import { useEffect, useRef, useState, ReactNode, CSSProperties } from 'react'

interface RevealProps {
  children: ReactNode
  /** Stagger delay in ms before the element animates in. */
  delay?: number
  className?: string
  style?: CSSProperties
  as?: keyof JSX.IntrinsicElements
}

/**
 * Fades + lifts its children into view once they enter the viewport.
 * Pairs with the `.reveal` / `.reveal.is-visible` rules in index.css.
 * Respects prefers-reduced-motion (CSS short-circuits the transition).
 */
export default function Reveal({
  children,
  delay = 0,
  className = '',
  style,
  as: Tag = 'div',
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          obs.disconnect()
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  const Component = Tag as any
  return (
    <Component
      ref={ref}
      className={`reveal${visible ? ' is-visible' : ''}${className ? ` ${className}` : ''}`}
      style={{ ...style, transitionDelay: visible ? `${delay}ms` : '0ms' }}
    >
      {children}
    </Component>
  )
}
