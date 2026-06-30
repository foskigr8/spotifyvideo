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
  replayKey: number
  playing: boolean
  speed?: number
  className?: string
}

const CANVAS_W = 640
const CANVAS_H = 360

export function DoodleCanvas({ scene, replayKey, playing, speed = 1, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null)
  const tokenRef = useRef(0)
  const dprRef = useRef(1)

  const wait = (ms: number, spd: number) =>
    new Promise<void>((res) => setTimeout(res, Math.max(0, ms) / spd))

  const paperBg = useCallback((ctx: CanvasRenderingContext2D) => {
    ctx.save()
    ctx.setTransform(dprRef.current, 0, 0, dprRef.current, 0, 0)
    ctx.fillStyle = '#fffef8'
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)
    ctx.strokeStyle = 'rgba(0,0,0,0.04)'
    ctx.lineWidth = 1
    for (let y = 28; y < CANVAS_H; y += 28) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CANVAS_W, y); ctx.stroke()
    }
    ctx.restore()
  }, [])

  const drawStroke = useCallback(async (
    ctx: CanvasRenderingContext2D,
    cmd: Extract<DrawCmd, { type: 'stroke' }>,
    spd: number, tok: number, instant: boolean
  ) => {
    const { points, color = '#1A1A1A', width = 2.5, duration = 500 } = cmd
    if (!points.length) return
    ctx.strokeStyle = color
    ctx.lineWidth = width
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    if (instant) {
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)
      for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y)
      ctx.stroke()
      return
    }
    const delay = duration / spd / Math.max(points.length - 1, 1)
    for (let i = 1; i < points.length; i++) {
      if (tokenRef.current !== tok) return
      ctx.beginPath()
      ctx.moveTo(points[i - 1].x, points[i - 1].y)
      ctx.lineTo(points[i].x, points[i].y)
      ctx.stroke()
      await wait(delay, spd)
    }
  }, [])

  // Character-by-character typewriter draw — this is what makes it feel hand-written
  const drawText = useCallback(async (
    ctx: CanvasRenderingContext2D,
    cmd: Extract<DrawCmd, { type: 'text' }>,
    spd: number, tok: number, instant: boolean
  ) => {
    const { text, x, y, size = 32, color = '#1A1A1A', duration = 400 } = cmd
    ctx.fillStyle = color
    ctx.font = `700 ${size}px 'Caveat', cursive`
    ctx.textBaseline = 'alphabetic'
    if (instant) { ctx.fillText(text, x, y); return }
    const delay = duration / spd / Math.max(text.length, 1)
    let drawn = ''
    for (const ch of text) {
      if (tokenRef.current !== tok) return
      drawn += ch
      // Erase the growing text area so we cleanly redraw each frame
      const metrics = ctx.measureText(drawn)
      ctx.fillStyle = '#fffef8'
      ctx.fillRect(x - 2, y - size - 2, metrics.width + size + 4, size + 12)
      // Re-draw the ruled line behind the text (so erasing doesn't leave a white gap)
      const lineY = Math.round(y / 28) * 28
      ctx.strokeStyle = 'rgba(0,0,0,0.04)'
      ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(x - 2, lineY); ctx.lineTo(x + metrics.width + size + 2, lineY); ctx.stroke()
      // Draw the text
      ctx.fillStyle = color
      ctx.font = `700 ${size}px 'Caveat', cursive`
      ctx.textBaseline = 'alphabetic'
      ctx.fillText(drawn, x, y)
      await wait(delay, spd)
    }
  }, [])

  const drawCircle = useCallback(async (
    ctx: CanvasRenderingContext2D,
    cmd: Extract<DrawCmd, { type: 'circle' }>,
    spd: number, tok: number, instant: boolean
  ) => {
    const { cx, cy, r, color = '#1A1A1A', fill = false, duration = 400 } = cmd
    if (instant) {
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2)
      if (fill) { ctx.fillStyle = color; ctx.fill() }
      else { ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.stroke() }
      return
    }
    const steps = 48
    const delay = duration / spd / steps
    if (fill) {
      // Progressive pie-wedge fill — grows from top, feels like it's being drawn in
      for (let i = 1; i <= steps; i++) {
        if (tokenRef.current !== tok) return
        const ang = (i / steps) * Math.PI * 2 - Math.PI / 2
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, r, -Math.PI / 2, ang)
        ctx.closePath()
        ctx.fillStyle = color
        ctx.fill()
        await wait(delay, spd)
      }
    } else {
      // Outline arc-by-arc
      ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.lineCap = 'round'
      for (let i = 1; i <= steps; i++) {
        if (tokenRef.current !== tok) return
        const ang = (i / steps) * Math.PI * 2 - Math.PI / 2
        const pang = ((i - 1) / steps) * Math.PI * 2 - Math.PI / 2
        ctx.beginPath()
        ctx.arc(cx, cy, r, pang, ang)
        ctx.stroke()
        await wait(delay, spd)
      }
    }
  }, [])

  const execute = useCallback(async (
    ctx: CanvasRenderingContext2D, cmd: DrawCmd,
    spd: number, tok: number, instant: boolean
  ) => {
    switch (cmd.type) {
      case 'stroke': return drawStroke(ctx, cmd, spd, tok, instant)
      case 'text': return drawText(ctx, cmd, spd, tok, instant)
      case 'circle': return drawCircle(ctx, cmd, spd, tok, instant)
      case 'wait': return instant ? undefined : wait(cmd.ms, spd)
      case 'clear': paperBg(ctx); return
    }
  }, [drawStroke, drawText, drawCircle, paperBg])

  const runScene = useCallback(async (
    cmds: DrawCmd[], spd: number, instant = false
  ) => {
    const ctx = ctxRef.current
    if (!ctx) return
    tokenRef.current += 1
    const tok = tokenRef.current
    paperBg(ctx)
    for (const cmd of cmds) {
      if (tokenRef.current !== tok) return
      await execute(ctx, cmd, spd, tok, instant)
    }
  }, [execute, paperBg])

  // Init canvas with devicePixelRatio scaling for crisp rendering on retina
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

  // Scene changes: animate when playing, instant render when paused/scrubbing
  useEffect(() => {
    if (!scene) return
    runScene(scene.cmds, speed, !playing)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scene?.window_index, replayKey])

  // When playback starts, re-run the current scene animated from scratch
  useEffect(() => {
    if (!scene || !playing) return
    runScene(scene.cmds, speed, false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing])

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width: '100%', height: '100%', display: 'block', borderRadius: 12 }}
    />
  )
}
