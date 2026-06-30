'use client'

import { useEffect, useRef, useCallback } from 'react'

export type DrawCmd =
  | { type: 'text'; text: string; x: number; y: number; size?: number; color?: string; duration?: number }
  | { type: 'stroke'; points: { x: number; y: number }[]; color?: string; width?: number; duration?: number }
  | { type: 'circle'; cx: number; cy: number; r: number; color?: string; fill?: boolean; duration?: number }
  | { type: 'wait'; ms: number }
  | { type: 'clear' }

export interface SceneWindow {
  window_index: number
  time_start: number
  time_end: number
  phrase: string
  cmds: DrawCmd[]
}

interface Props {
  scene: SceneWindow | null
  /** Global playhead time in seconds (always passed, even when paused / seeking) */
  currentTime: number
  playing: boolean
  speed?: number
  className?: string
}

const CANVAS_W = 640
const CANVAS_H = 360

interface Scheduled {
  cmd: DrawCmd
  startMs: number
  endMs: number
}

function schedule(cmds: DrawCmd[]): { items: Scheduled[]; totalMs: number } {
  let t = 0
  const items: Scheduled[] = []
  for (const cmd of cmds) {
    if (cmd.type === 'wait') {
      t += cmd.ms
      continue
    }
    if (cmd.type === 'clear') {
      items.push({ cmd, startMs: t, endMs: t })
      continue
    }
    const dur = cmd.duration ?? 400
    items.push({ cmd, startMs: t, endMs: t + dur })
    t += dur
  }
  return { items, totalMs: t }
}

export function DoodleCanvas({ scene, currentTime, playing, speed = 1, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null)
  const dprRef = useRef(1)
  const rafRef = useRef<number | null>(null)
  const startedAtRef = useRef<number | null>(null)

  const paperBg = useCallback((ctx: CanvasRenderingContext2D) => {
    ctx.save()
    ctx.setTransform(dprRef.current, 0, 0, dprRef.current, 0, 0)
    ctx.fillStyle = '#fffef8'
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)
    ctx.strokeStyle = 'rgba(0,0,0,0.035)'
    ctx.lineWidth = 1
    for (let y = 0; y < CANVAS_H; y += 24) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(CANVAS_W, y)
      ctx.stroke()
    }
    ctx.restore()
  }, [])

  const drawFrame = useCallback(
    (ctx: CanvasRenderingContext2D, items: Scheduled[], elapsed: number) => {
      paperBg(ctx)
      for (const { cmd, startMs, endMs } of items) {
        if (elapsed <= startMs) continue
        const span = Math.max(1, endMs - startMs)
        const progress = Math.min(1, (elapsed - startMs) / span)

        if (cmd.type === 'stroke') {
          const { points, color = '#222', width = 2.5 } = cmd
          if (points.length < 2) continue
          const n = Math.max(2, Math.round(points.length * progress))
          ctx.strokeStyle = color
          ctx.lineWidth = width
          ctx.lineCap = 'round'
          ctx.lineJoin = 'round'
          ctx.beginPath()
          ctx.moveTo(points[0].x, points[0].y)
          for (let i = 1; i < n; i++) ctx.lineTo(points[i].x, points[i].y)
          ctx.stroke()
        } else if (cmd.type === 'circle') {
          const { cx, cy, r, color = '#222', fill = false } = cmd
          const endAngle = -Math.PI / 2 + progress * Math.PI * 2
          ctx.beginPath()
          ctx.arc(cx, cy, r, -Math.PI / 2, endAngle)
          ctx.strokeStyle = color
          ctx.lineWidth = 3
          ctx.stroke()
          if (fill && progress >= 1) {
            ctx.beginPath()
            ctx.arc(cx, cy, r - 2, 0, Math.PI * 2)
            ctx.fillStyle = color
            ctx.fill()
          }
        } else if (cmd.type === 'text') {
          if (progress <= 0) continue
          const { text, x, y, size = 28, color = '#222' } = cmd
          ctx.fillStyle = color
          ctx.font = `700 ${size}px 'Caveat', cursive`
          ctx.textBaseline = 'alphabetic'
          ctx.fillText(text, x, y)
        }
      }
    },
    [paperBg]
  )

  // Canvas setup on mount
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dpr = Math.max(1, Math.min(3, window.devicePixelRatio || 1))
    dprRef.current = dpr
    canvas.width = CANVAS_W * dpr
    canvas.height = CANVAS_H * dpr
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctxRef.current = ctx
    paperBg(ctx)
  }, [paperBg])

  // Main render effect — re-runs on scene change, seek, play/pause, speed change
  useEffect(() => {
    const ctx = ctxRef.current
    if (!scene || !ctx) return

    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    startedAtRef.current = null

    const { items, totalMs } = schedule(scene.cmds)
    const sceneDurationSec = Math.max(0.001, scene.time_end - scene.time_start)

    // How far into this scene's animation are we? (in ms)
    const elapsedAtSeek = Math.max(
      0,
      Math.min(totalMs, ((currentTime - scene.time_start) / sceneDurationSec) * totalMs)
    )

    if (!playing) {
      // PAUSED or SEEKING: draw the exact static frame for this position
      drawFrame(ctx, items, elapsedAtSeek)
      return
    }

    // PLAYING: start rAF from elapsedAtSeek and animate forward
    const tick = (now: number) => {
      if (startedAtRef.current === null) startedAtRef.current = now
      const runtimeElapsed = (now - startedAtRef.current) * speed
      const elapsed = Math.min(totalMs, elapsedAtSeek + runtimeElapsed)
      drawFrame(ctx, items, elapsed)
      if (elapsed < totalMs) {
        rafRef.current = requestAnimationFrame(tick)
      }
    }
    rafRef.current = requestAnimationFrame(tick)

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scene?.window_index, scene?.time_start, currentTime, playing, speed, drawFrame])

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width: '100%', height: '100%', display: 'block', background: '#fffef8', borderRadius: 12 }}
    />
  )
}
