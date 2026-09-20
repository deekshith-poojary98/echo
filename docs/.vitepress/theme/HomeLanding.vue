<script setup lang="ts">
import { onMounted, onUnmounted, ref, useTemplateRef } from 'vue'
import { highlightEchoSnippet } from './highlightEchoSnippet'

const withBase = (path: string) => {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

const snippets = [
  {
    id: 'hello',
    title: 'Greet',
    code: `name: str = "Echo";

fn greet(user: str) {
    say("Hello, \${user}!");
}

greet(name);`,
  },
  {
    id: 'lists',
    title: 'Lists',
    code: `nums: list = [1, 2, 3];

foreach n: int in nums {
    say(n * 2);
}`,
  },
  {
    id: 'classes',
    title: 'Classes',
    code: `class Point {
    new {
        x: int;
        y: int;
    }

    fn describe(this) {
        say("(", this.x, ",", this.y, ")");
    }
}

p: Point = Point { x: 3, y: 4 };
p.describe();`,
  },
]

const pillars = [
  {
    title: 'Typed',
    body: 'Declarations and parameters carry types. Echo checks them when values are bound — no separate static checker.',
  },
  {
    title: 'Observable',
    body: 'watch, clear failures, and a CLI built for scripts you can see: run, check, test, fmt, lint.',
  },
  {
    title: 'Honest limits',
    body: 'What ships and what is held are written down. Do not assume a pattern works until the docs say so.',
  },
]

const startPaths = [
  { text: 'Install', link: '/getting-started/installation', hint: 'CLI on your machine' },
  { text: 'Quick Start', link: '/getting-started/quick-start', hint: 'File → run in minutes' },
  { text: 'Language Tour', link: '/getting-started/tour', hint: 'Surface and early pitfalls' },
  { text: 'Playground', link: '/playground', hint: 'Try Echo in the browser' },
]

const heroRef = useTemplateRef<HTMLElement>('hero')
const canvasRef = useTemplateRef<HTMLCanvasElement>('water')
const showScrollCue = ref(true)

const SCALE = 2.75
const DAMPING = 0.972
const DISTURB_RADIUS = 4
const DISTURB_STRENGTH = 28

let width = 0
let height = 0
let curr: Float32Array | null = null
let prev: Float32Array | null = null
let pixels: ImageData | null = null
let ctx: CanvasRenderingContext2D | null = null
let raf = 0
let active = false
let reduceMotion = false
let dark = false
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null

function index(x: number, y: number) {
  return y * width + x
}

function resize() {
  if (!heroRef.value || !canvasRef.value) {
    return
  }

  const rect = heroRef.value.getBoundingClientRect()
  width = Math.max(48, Math.floor(rect.width / SCALE))
  height = Math.max(48, Math.floor(rect.height / SCALE))

  canvasRef.value.width = width
  canvasRef.value.height = height
  canvasRef.value.style.width = `${rect.width}px`
  canvasRef.value.style.height = `${rect.height}px`

  ctx = canvasRef.value.getContext('2d', { alpha: true })
  if (!ctx) {
    return
  }

  curr = new Float32Array(width * height)
  prev = new Float32Array(width * height)
  pixels = ctx.createImageData(width, height)
}

function disturb(px: number, py: number) {
  if (!curr || !prev || !heroRef.value) {
    return
  }

  const rect = heroRef.value.getBoundingClientRect()
  const x = Math.floor(((px - rect.left) / rect.width) * width)
  const y = Math.floor(((py - rect.top) / rect.height) * height)

  for (let oy = -DISTURB_RADIUS; oy <= DISTURB_RADIUS; oy += 1) {
    for (let ox = -DISTURB_RADIUS; ox <= DISTURB_RADIUS; ox += 1) {
      const nx = x + ox
      const ny = y + oy
      if (nx <= 0 || ny <= 0 || nx >= width - 1 || ny >= height - 1) {
        continue
      }
      const dist = Math.hypot(ox, oy)
      if (dist > DISTURB_RADIUS) {
        continue
      }
      const falloff = 1 - dist / DISTURB_RADIUS
      curr[index(nx, ny)] += DISTURB_STRENGTH * falloff * falloff
    }
  }

  if (!active) {
    active = true
    raf = window.requestAnimationFrame(frame)
  }
}

function step() {
  if (!curr || !prev) {
    return 0
  }

  let energy = 0
  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const i = index(x, y)
      const next =
        (curr[i - 1] + curr[i + 1] + curr[i - width] + curr[i + width]) / 2 - prev[i]
      prev[i] = next * DAMPING
      energy += Math.abs(prev[i])
    }
  }

  const swap = curr
  curr = prev
  prev = swap
  return energy
}

function paint() {
  if (!ctx || !curr || !pixels) {
    return
  }

  const data = pixels.data
  const baseR = dark ? 45 : 15
  const baseG = dark ? 212 : 118
  const baseB = dark ? 191 : 110

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const i = index(x, y)
      const h = curr[i]
      const dx = curr[i - 1] - curr[i + 1]
      const dy = curr[i - width] - curr[i + width]
      // Fake lighting: highlight facing top-left, troughs darker.
      const shade = dx * 0.35 + dy * 0.5
      const tone = h * 0.55 + shade
      const p = i * 4

      data[p] = Math.max(0, Math.min(255, baseR + tone * 1.6))
      data[p + 1] = Math.max(0, Math.min(255, baseG + tone * 1.2))
      data[p + 2] = Math.max(0, Math.min(255, baseB + tone * 0.9))
      data[p + 3] = Math.max(0, Math.min(38, Math.abs(h) * 1.35 + Math.abs(shade) * 0.7))
    }
  }

  ctx.putImageData(pixels, 0, 0)
}

function frame() {
  const energy = step()
  paint()

  if (energy > 0.35) {
    raf = window.requestAnimationFrame(frame)
  } else {
    active = false
    if (ctx && pixels) {
      pixels.data.fill(0)
      ctx.putImageData(pixels, 0, 0)
    }
  }
}

function onHeroClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (target?.closest('a, button') || reduceMotion) {
    return
  }
  disturb(event.clientX, event.clientY)
}

function scrollToContent() {
  document.getElementById('echo-home-try')?.scrollIntoView({
    behavior: reduceMotion ? 'auto' : 'smooth',
    block: 'start',
  })
}

function onWindowScroll() {
  showScrollCue.value = window.scrollY < 48
}

function syncTheme() {
  dark = document.documentElement.classList.contains('dark')
}

onMounted(() => {
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduceMotion || !heroRef.value || !canvasRef.value) {
    return
  }

  syncTheme()
  resize()
  onWindowScroll()
  window.addEventListener('scroll', onWindowScroll, { passive: true })

  resizeObserver = new ResizeObserver(() => resize())
  resizeObserver.observe(heroRef.value)

  themeObserver = new MutationObserver(syncTheme)
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
})

onUnmounted(() => {
  window.cancelAnimationFrame(raf)
  window.removeEventListener('scroll', onWindowScroll)
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
})
</script>

<template>
  <div class="echo-home vp-raw">
    <section
      ref="hero"
      class="echo-home__hero"
      aria-labelledby="echo-home-brand"
      @click="onHeroClick"
    >
      <div class="echo-home__hero-glow" aria-hidden="true" />
      <canvas ref="water" class="echo-home__water" aria-hidden="true"></canvas>

      <p class="echo-home__version">Latest · 0.8.4</p>
      <div class="echo-home__mark" role="img" aria-label="Echo">
        <span class="echo-home__bar" style="--h: 0.36; --d: 0s"></span>
        <span class="echo-home__bar" style="--h: 0.78; --d: -0.28s"></span>
        <span class="echo-home__bar" style="--h: 1; --d: -0.56s"></span>
        <span class="echo-home__bar" style="--h: 0.58; --d: -0.84s"></span>
        <span class="echo-home__bar" style="--h: 0.78; --d: -1.12s"></span>
      </div>
      <h1 id="echo-home-brand" class="echo-home__brand">Echo</h1>
      <p class="echo-home__tagline">
        A typed scripting language for automation, testing, and workflows you can watch.
      </p>
      <div class="echo-home__ctas">
        <a class="echo-home__cta echo-home__cta--primary" :href="withBase('/getting-started/installation')">
          Install
        </a>
        <a class="echo-home__cta echo-home__cta--ghost" :href="withBase('/playground')">
          Playground
        </a>
      </div>

      <button
        type="button"
        class="echo-home__scroll"
        :class="{ 'is-hidden': !showScrollCue }"
        aria-label="Scroll to see more"
        @click.stop="scrollToContent"
      >
        <span>See more</span>
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path
            d="M6 9l6 6 6-6"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </section>

    <section class="echo-home__try" aria-labelledby="echo-home-try">
      <h2 id="echo-home-try" class="echo-home__section-title">See it</h2>
      <p class="echo-home__section-lead">Short programs. Open any one in the playground.</p>
      <div class="echo-home__panels">
        <article
          v-for="(snippet, index) in snippets"
          :key="snippet.id"
          class="echo-home__panel"
          :style="{ '--delay': `${0.08 * index}s` }"
        >
          <header class="echo-home__panel-bar">
            <span>{{ snippet.title }}</span>
            <a class="echo-home__try-link" :href="withBase(`/playground?example=${snippet.id}`)">
              Try
            </a>
          </header>
          <pre class="echo-home__code"><code v-html="highlightEchoSnippet(snippet.code)"></code></pre>
        </article>
      </div>
    </section>

    <section class="echo-home__why" aria-labelledby="echo-home-why">
      <h2 id="echo-home-why" class="echo-home__section-title">Why Echo?</h2>
      <p class="echo-home__section-lead">
        Built for scripts that need structure — not another systems language.
      </p>
      <div class="echo-home__pillars">
        <div v-for="pillar in pillars" :key="pillar.title" class="echo-home__pillar">
          <h3>{{ pillar.title }}</h3>
          <p>{{ pillar.body }}</p>
        </div>
      </div>
    </section>

    <section class="echo-home__start" aria-labelledby="echo-home-start">
      <h2 id="echo-home-start" class="echo-home__section-title">Start here</h2>
      <ul class="echo-home__paths">
        <li v-for="path in startPaths" :key="path.link">
          <a :href="withBase(path.link)">
            <strong>{{ path.text }}</strong>
            <span>{{ path.hint }}</span>
          </a>
        </li>
      </ul>
      <p class="echo-home__footnote">
        Ships today: types, modules, classes and interfaces (no inheritance), CLI tooling.
        Held: generics, <code>try</code>/<code>catch</code>, packages.
        See
        <a :href="withBase('/errors-diagnostics/known-limitations')">Known Limitations</a>.
      </p>
    </section>
  </div>
</template>
