'use client'

import { useEffect, useRef, useCallback } from 'react'

// ── Draw command types — must match scenes_preview.json exactly ──────────
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
  /** bump this whenever you want the scene to redraw from scratch (e.g. on seek) */
  replayKey: number
  /** only draw while actively playing — stays blank when paused/seeking */
  playing: boolean
  speed?: number
  className?: string
}

// Logical drawing coordinate space — all cmd x/y/size values in scenes_preview.json
// are authored against this. We scale up to device pixels for crispness, the CSS
// box stretches to fill its container so it reads correctly on phones too.
const CANVAS_W = 640
const CANVAS_H = 360

export function DoodleCanvas({ scene, replayKey, playing, speed = 1, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null)
  const tokenRef = useRef(0) // increments to cancel in-flight async draws
  const dprRef = useRef(1)

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

  const wait = (ms: number, mySpeed: number) =>
    new Promise<void>((resolve) => setTimeout(resolve, Math.max(0, ms) / mySpeed))

  const drawStroke = useCallback(
    async (ctx: CanvasRenderingContext2D, cmd: Extract<DrawCmd, { type: 'stroke' }>, mySpeed: number, myToken: number) => {
      const { points, color = '#222', width = 2.5, duration = 600 } = cmd
      if (!points.length) return
      const delay = duration / mySpeed / Math.max(points.length, 1)
      ctx.strokeStyle = color
      ctx.lineWidth = width
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      for (let i = 1; i < points.length; i++) {
        if (tokenRef.current !== myToken) return
        ctx.beginPath()
        ctx.moveTo(points[i - 1].x, points[i - 1].y)
        ctx.lineTo(points[i].x, points[i].y)
        ctx.stroke()
        await wait(delay, mySpeed)
      }
    },
    []
  )

  // Text draws instantly for reliability. The sequential drawing of
  // strokes and arrows still provides the hand-drawn doodle feel.
  const drawText = useCallback(
    async (ctx: CanvasRenderingContext2D, cmd: Extract<DrawCmd, { type: 'text' }>, mySpeed: number, myToken: number) => {
      const { text, x, y, size = 28, color = '#222', duration = 400 } = cmd
      if (tokenRef.current !== myToken) return
      ctx.fillStyle = color
      ctx.font = `700 ${size}px 'Caveat', cursive`
      ctx.textBaseline = 'alphabetic'
      ctx.fillText(text, x, y)
      // Brief pause so elements appear sequentially, not all at once
      await wait(Math.min(duration * 0.25, 120), mySpeed)
    },
    []
  )

  const drawCircle = useCallback(
    async (ctx: CanvasRenderingContext2D, cmd: Extract<DrawCmd, { type: 'circle' }>, mySpeed: number, myToken: number) => {
      const { cx, cy, r, color = '#222', fill = false, duration = 500 } = cmd
      const steps = 60
      const delay = duration / mySpeed / steps
      for (let i = 1; i <= steps; i++) {
        if (tokenRef.current !== myToken) return
        const ang = (i / steps) * Math.PI * 2 - Math.PI / 2
        const pang = ((i - 1) / steps) * Math.PI * 2 - Math.PI / 2
        ctx.beginPath()
        ctx.moveTo(cx + Math.cos(pang) * r, cy + Math.sin(pang) * r)
        ctx.lineTo(cx + Math.cos(ang) * r, cy + Math.sin(ang) * r)
        ctx.strokeStyle = color
        ctx.lineWidth = 3
        ctx.stroke()
        await wait(delay, mySpeed)
      }
      if (fill) {
        ctx.beginPath()
        ctx.arc(cx, cy, r - 2, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
      }
    },
    []
  )

  const execute = useCallback(
    async (ctx: CanvasRenderingContext2D, cmd: DrawCmd, mySpeed: number, myToken: number) => {
      switch (cmd.type) {
        case 'stroke':
          return drawStroke(ctx, cmd, mySpeed, myToken)
        case 'text':
          return drawText(ctx, cmd, mySpeed, myToken)
        case 'circle':
          return drawCircle(ctx, cmd, mySpeed, myToken)
        case 'wait':
          return wait(cmd.ms, mySpeed)
        case 'clear':
          paperBg(ctx)
          return
      }
    },
    [drawStroke, drawText, drawCircle, paperBg]
  )

  const runScene = useCallback(
    async (cmds: DrawCmd[], mySpeed: number) => {
      const ctx = ctxRef.current
      if (!ctx) return
      tokenRef.current += 1
      const myToken = tokenRef.current
      paperBg(ctx)
      for (const cmd of cmds) {
        if (tokenRef.current !== myToken) return
        await execute(ctx, cmd, mySpeed, myToken)
      }
    },
    [execute, paperBg]
  )

  // init canvas — scale for devicePixelRatio so text/strokes stay crisp when the
  // CSS box is stretched larger on bigger screens
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

  // Only draw while actively playing. When paused or while scrubbing the
  // timeline, cancel any in-flight draw and show a blank sheet — the
  // animation should never appear "already finished" before you hit play.
  useEffect(() => {
    const ctx = ctxRef.current
    if (!scene) return

    if (!playing) {
      tokenRef.current += 1 // cancel any in-flight draw
      if (ctx) paperBg(ctx)
      return
    }

    runScene(scene.cmds, speed)
    // intentionally not awaiting — fire and forget, cancellation via tokenRef
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scene?.window_index, replayKey, playing])

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width: '100%', height: '100%', display: 'block', background: '#fffef8', borderRadius: 12 }}
    />
  )
}
