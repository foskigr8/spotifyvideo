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
  speed?: number
  className?: string
}

const CANVAS_W = 640
const CANVAS_H = 360

export function DoodleCanvas({ scene, replayKey, speed = 1, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null)
  const tokenRef = useRef(0) // increments to cancel in-flight async draws

  const paperBg = useCallback((ctx: CanvasRenderingContext2D) => {
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
  }, [])

  const wait = (ms: number, mySpeed: number) =>
    new Promise<void>((resolve) => setTimeout(resolve, ms / mySpeed))

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

  const drawText = useCallback(
    async (ctx: CanvasRenderingContext2D, cmd: Extract<DrawCmd, { type: 'text' }>, mySpeed: number, myToken: number) => {
      const { text, x, y, size = 28, color = '#222', duration = 500 } = cmd
      const delay = duration / mySpeed / Math.max(text.length, 1)
      let drawn = ''
      for (const ch of text) {
        if (tokenRef.current !== myToken) return
        drawn += ch
        const w = ctx.measureText(drawn).font ? ctx.measureText(drawn).width : 0
        // clear just the text region behind what's being (re)drawn each frame
        ctx.fillStyle = '#fffef8'
        ctx.fillRect(x - 2, y - size, w + 40, size + 10)
        ctx.fillStyle = color
        ctx.font = `700 ${size}px 'Caveat', cursive`
        ctx.fillText(drawn, x, y)
        await wait(delay, mySpeed)
      }
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

  // init canvas context once
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctxRef.current = ctx
    paperBg(ctx)
  }, [paperBg])

  // run the scene whenever it changes (or replayKey forces a redraw)
  useEffect(() => {
    if (!scene) return
    runScene(scene.cmds, speed)
    // intentionally not awaiting — fire and forget, cancellation via tokenRef
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scene?.window_index, replayKey])

  return (
    <canvas
      ref={canvasRef}
      width={CANVAS_W}
      height={CANVAS_H}
      className={className}
      style={{ width: '100%', height: '100%', display: 'block', background: '#fffef8', borderRadius: 12 }}
    />
  )
}
