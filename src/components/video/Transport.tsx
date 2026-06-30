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
  const pct = duration > 0 ? (t / duration) * 100 : 0

  return (
    <div
      className="flex flex-col gap-3 px-4 pt-3 pb-4 rounded-xl"
      style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}
    >
      {/* ── Scrubber row ── */}
      <div className="flex items-center gap-3">
        <span
          style={{
            fontFamily: 'var(--font-mono), monospace',
            fontSize: '0.78rem',
            fontWeight: 600,
            color: '#1A1A1A',
            minWidth: '2.8rem',
          }}
        >
          {fmt(t)}
        </span>

        <div className="relative flex-1">
          {/* filled track */}
          <div
            className="pointer-events-none absolute inset-y-0 left-0 rounded-full"
            style={{ width: `${pct}%`, background: '#1DB954', top: '50%', transform: 'translateY(-50%)', height: 4 }}
          />
          <input
            type="range"
            min={0}
            max={duration || 1}
            step={0.05}
            value={t}
            onChange={(e) => onSeek(parseFloat(e.target.value))}
            className="video-range relative h-1 w-full cursor-pointer appearance-none rounded-full"
            style={{ background: 'rgba(26,26,26,0.12)' }}
          />
        </div>

        <span
          style={{
            fontFamily: 'var(--font-mono), monospace',
            fontSize: '0.78rem',
            color: 'rgba(26,26,26,0.45)',
            minWidth: '2.8rem',
            textAlign: 'right',
          }}
        >
          {fmt(duration)}
        </span>
      </div>

      {/* ── Controls row ── */}
      <div className="flex items-center justify-between">
        {/* Left: step back */}
        <button
          onClick={() => onStep(-5)}
          title="Back 5s"
          className="flex items-center gap-1 rounded-md px-2 py-1 transition hover:bg-black/5"
          style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.72rem', color: 'rgba(26,26,26,0.5)' }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.63"/>
          </svg>
          5s
        </button>

        {/* Centre: play/pause */}
        <button
          onClick={onTogglePlay}
          className="flex h-12 w-12 items-center justify-center rounded-full shadow-md transition hover:scale-105 active:scale-95"
          style={{ background: '#1DB954', color: '#fff' }}
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? (
            <svg width="14" height="16" viewBox="0 0 12 14" fill="currentColor">
              <rect x="0" y="0" width="3.5" height="14" rx="1.5"/>
              <rect x="8.5" y="0" width="3.5" height="14" rx="1.5"/>
            </svg>
          ) : (
            <svg width="14" height="16" viewBox="0 0 12 14" fill="currentColor">
              <path d="M0 0 L12 7 L0 14 Z"/>
            </svg>
          )}
        </button>

        {/* Right: step forward */}
        <button
          onClick={() => onStep(5)}
          title="Forward 5s"
          className="flex items-center gap-1 rounded-md px-2 py-1 transition hover:bg-black/5"
          style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.72rem', color: 'rgba(26,26,26,0.5)' }}
        >
          5s
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-.49-3.63"/>
          </svg>
        </button>

        {/* Speed controls */}
        <div className="flex items-center gap-1 ml-2">
          {speeds.map((s) => (
            <button
              key={s}
              onClick={() => onSpeed(s)}
              className="rounded-md px-2 py-1 transition"
              style={{
                fontFamily: 'var(--font-mono), monospace',
                fontSize: '0.72rem',
                background: speed === s ? 'rgba(29,185,84,0.15)' : 'transparent',
                color: speed === s ? '#1DB954' : 'rgba(26,26,26,0.4)',
                fontWeight: speed === s ? 700 : 400,
              }}
            >
              {s}×
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
