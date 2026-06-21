import { useEffect, useRef, useState } from 'react'
import LogoIcon from './LogoIcon'
import './Intro.css'

const WORD = 'DietMate'.split('')

/**
 * Cinematic launch overlay (pacome-style). Animates the brand in, runs a
 * loading counter, then lifts the curtain to reveal the app beneath.
 * Click anywhere to skip; auto-skips entirely under prefers-reduced-motion.
 */
export default function Intro({ onDone }: { onDone: () => void }) {
  const [progress, setProgress] = useState(0)
  const [exiting, setExiting] = useState(false)
  const doneRef = useRef(false)
  const rafRef = useRef(0)

  const finish = () => {
    if (doneRef.current) return
    doneRef.current = true
    cancelAnimationFrame(rafRef.current)
    setProgress(100)
    setExiting(true)
    window.setTimeout(onDone, 850)
  }

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) {
      onDone()
      return
    }
    const DUR = 1800
    const start = performance.now()
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / DUR)
      setProgress(Math.round(p * 100))
      if (p < 1) rafRef.current = requestAnimationFrame(tick)
      else finish()
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div
      className={`intro ${exiting ? 'intro--exit' : ''}`}
      onClick={finish}
      role="button"
      tabIndex={0}
      aria-label="Enter DietMate67"
    >
      <div className="intro-corner intro-corner--tl">
        <span className="eyebrow">Vol.01 / &rsquo;26</span>
      </div>
      <div className="intro-corner intro-corner--tr">
        <span className="eyebrow">Est. 2026</span>
      </div>

      <div className="intro-center">
        <span className="intro-logo"><LogoIcon /></span>
        <span className="eyebrow intro-kicker">Dietary Restaurant Matching</span>
        <h1 className="intro-word">
          {WORD.map((c, i) => (
            <span key={i} style={{ animationDelay: `${0.2 + i * 0.05}s` }}>{c}</span>
          ))}
          <span
            className="intro-word-accent"
            style={{ animationDelay: `${0.2 + WORD.length * 0.05}s` }}
          >
            67
          </span>
        </h1>
      </div>

      <div className="intro-foot">
        <div className="intro-progress">
          <span className="intro-count">{String(progress).padStart(3, '0')}</span>
          <span className="intro-bar">
            <span className="intro-bar-fill" style={{ width: `${progress}%` }} />
          </span>
          <span className="intro-count intro-count--dim">100</span>
        </div>
        <span className="eyebrow intro-skip">
          {progress < 100 ? 'Loading' : 'Click to enter'}
        </span>
      </div>
    </div>
  )
}
