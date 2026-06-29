'use client'

interface Props {
  t: number
  duration: number
  playing: boolean
  speed: number
  onSeek: (t: number) => void
  onTogglePlay: () => void
  onSpeed: (s: number) => void
  onStep: (delta: number) => void
}

function fmt(s: number): string {
  if (!isFinite(s) || s < 0) s = 0
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

export function Transport({ t, duration, playing, speed, onSeek, onTogglePlay, onSpeed, onStep }: Props) {
  const speeds = [0.5, 1, 1.5, 2]
  return (
    <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
      <button
        onClick={() => onStep(-3)}
        className="rounded-md px-2 py-1 font-mono text-xs text-white/60 transition hover:bg-white/10 hover:text-white"
        title="Back 3s"
      >
        -3s
      </button>
      <button
        onClick={onTogglePlay}
        className="flex h-10 w-10 items-center justify-center rounded-full bg-[#1DB954] text-black transition hover:scale-105 hover:bg-[#1ed760] active:scale-95"
        title={playing ? 'Pause' : 'Play'}
      >
        {playing ? (
          <svg width="14" height="16" viewBox="0 0 14 16" fill="currentColor"><rect x="0" y="0" width="4" height="16" rx="1"/><rect x="10" y="0" width="4" height="16" rx="1"/></svg>
        ) : (
          <svg width="14" height="16" viewBox="0 0 14 16" fill="currentColor"><path d="M0 0 L14 8 L0 16 Z"/></svg>
        )}
      </button>
      <button
        onClick={() => onStep(3)}
        className="rounded-md px-2 py-1 font-mono text-xs text-white/60 transition hover:bg-white/10 hover:text-white"
        title="Forward 3s"
      >
        +3s
      </button>

      <div className="ml-2 font-mono text-sm tabular-nums text-white/70">
        <span className="text-white">{fmt(t)}</span>
        <span className="mx-1 text-white/30">/</span>
        <span>{fmt(duration)}</span>
      </div>

      <div className="relative mx-2 flex-1">
        <input
          type="range"
          min={0}
          max={duration}
          step={0.05}
          value={t}
          onChange={(e) => onSeek(parseFloat(e.target.value))}
          className="video-range h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/15"
        />
      </div>

      <div className="flex items-center gap-1">
        {speeds.map((s) => (
          <button
            key={s}
            onClick={() => onSpeed(s)}
            className={`rounded-md px-2 py-1 font-mono text-xs transition ${
              speed === s ? 'bg-white/15 text-white' : 'text-white/45 hover:bg-white/10 hover:text-white/80'
            }`}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  )
}
