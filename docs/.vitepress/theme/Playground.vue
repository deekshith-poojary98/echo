<script setup lang="ts">
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language'
import { highlightSelectionMatches, searchKeymap } from '@codemirror/search'
import { EditorState } from '@codemirror/state'
import { EditorView, highlightActiveLine, highlightActiveLineGutter, keymap, lineNumbers } from '@codemirror/view'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { echoLanguage } from './echoLanguage'
import { echoHighlight } from './echoHighlight'
import classesSource from '../../../examples/classes_and_interfaces.echo?raw'
import bankSource from '../../../examples/bank_account.echo?raw'

type Example = {
  id: string
  label: string
  source: string
}

const EXAMPLES: Example[] = [
  {
    id: 'hello',
    label: 'Hello',
    source: `name: str = "Echo";

fn greet(user: str) {
    say("Hello, \${user}!");
}

greet(name);
`,
  },
  {
    id: 'types',
    label: 'Types',
    source: `count: int = 3;
pi: float = 3.14;
ready: bool = true;
items: list = [1, 2, 3];

say("count:", count);
say("pi:", pi);
say("ready:", ready);
say("items:", items);
say("as string:", count.asString());
`,
  },
  {
    id: 'lists',
    label: 'Lists & hashes',
    source: `nums: list = [1, 2, 3];

foreach n: int in nums {
    say(n * 2);
}

words: list = ["a", "b", "a"];
counts: hash = {};

i: int = 0;
while i < words.length() {
    word: str = words[i];
    counts[word] = counts.ensure(word, 0) + 1;
    i = i + 1;
}

say(counts);
`,
  },
  {
    id: 'classes',
    label: 'Classes',
    source: `class Point {
    new {
        x: int;
        y: int;
    }

    fn describe(this) {
        say("(", this.x, ",", this.y, ")");
    }
}

p: Point = Point { x: 3, y: 4 };
p.describe();
`,
  },
  {
    id: 'functions',
    label: 'Functions',
    source: `fn describe(name: str, age: int) {
    say(name, "is", age);
}

describe(age: 21, name: "Alice");
`,
  },
  {
    id: 'lambdas',
    label: 'Lambdas & lists',
    source: `nums: list = [1, 2, 3, 4];
double: fn(int) -> int = fn(x: int) -> int { return x * 2; };

say("slice:", nums[1:3]);
say("tail:", nums[1:]);
say("map:", nums.map(double));
say("filter:", nums.filter(fn(x: int) -> bool { return x % 2 == 0; }));
say("reduce:", nums.reduce(0, fn(acc: int, x: int) -> int { return acc + x; }));
nums.forEach(fn(x: int) { say("each", x); });
say("flatMap:", nums.flatMap(fn(x: int) -> list { return [x, x]; }));
say("some:", nums.some(fn(x: int) -> bool { return x == 3; }));
say("every:", nums.every(fn(x: int) -> bool { return x > 0; }));
say("findIndex:", nums.findIndex(fn(x: int) -> bool { return x == 4; }));
say("zip:", zip(nums, [10, 20, 30]));
say("unique:", [1, 2, 1, true, 1].unique());
say("flatten:", [[1, 2], [3]].flatten());
say("partition:", nums.partition(fn(x: int) -> bool { return x % 2 == 0; }));

fn join(punct: str = ",", parts: str...) {
    say(parts.join(punct));
}
join(" | ", "a", "b", "c");
`,
  },
  {
    id: 'fizzbuzz',
    label: 'FizzBuzz',
    source: `for n: int in 1..20 {
    if n % 15 == 0 {
        say("FizzBuzz");
    } else if n % 3 == 0 {
        say("Fizz");
    } else if n % 5 == 0 {
        say("Buzz");
    } else {
        say(n);
    }
}
`,
  },
  {
    id: 'ask',
    label: 'ask()',
    source: `name: str = ask("Name: ");
say("Hello, \${name}!");
`,
  },
  {
    id: 'urls',
    label: 'URL helpers',
    source: `q: str = urlQuery({ q: "echo lang", page: "1" });
say(urlEncode("a b/c"));
say(urlJoin("https://example.com/api/", "users"));
say(q);
say(httpOk(200));
say(httpRedirect(302));
`,
  },
  {
    id: 'bank',
    label: 'Bank account',
    source: bankSource,
  },
  {
    id: 'classes-full',
    label: 'Classes & interfaces',
    source: classesSource,
  },
]

const RUN_TIMEOUT_MS = 8000
const PLACEHOLDER = 'Output appears here after you run a program.\nClick here and type when ask() prompts you.'

function exampleFromQuery(): string {
  if (typeof window === 'undefined') {
    return EXAMPLES[0].id
  }
  const id = new URLSearchParams(window.location.search).get('example')
  return EXAMPLES.some((item) => item.id === id) ? (id as string) : EXAMPLES[0].id
}

const editorHost = ref<HTMLElement | null>(null)
const consoleEl = ref<HTMLElement | null>(null)
const workspaceEl = ref<HTMLElement | null>(null)
const exampleId = ref(exampleFromQuery())
const initialExample = EXAMPLES.find((item) => item.id === exampleId.value) ?? EXAMPLES[0]
const source = ref(initialExample.source)
const output = ref('')
const draftInput = ref('')
const awaitingInput = ref(false)
const failed = ref(false)
const status = ref('Starting playground…')
const ready = ref(false)
const running = ref(false)
const splitPct = ref(57)
const stacked = ref(false)
const dragging = ref(false)

const canRun = computed(() => ready.value && !running.value && source.value.trim().length > 0)
const statusKind = computed(() =>
  failed.value ? 'error' : awaitingInput.value ? 'running' : running.value ? 'running' : ready.value ? 'ready' : 'boot',
)
const showPlaceholder = computed(() => !output.value && !awaitingInput.value && !running.value)
const workspaceStyle = computed(() => {
  const primary = `minmax(0, ${splitPct.value}fr)`
  const secondary = `minmax(0, ${100 - splitPct.value}fr)`
  if (stacked.value) {
    return {
      gridTemplateColumns: 'minmax(0, 1fr)',
      gridTemplateRows: `${primary} auto ${secondary}`,
    }
  }
  return {
    gridTemplateColumns: `${primary} auto ${secondary}`,
    gridTemplateRows: 'minmax(0, 1fr)',
  }
})

let worker: Worker | null = null
let editor: EditorView | null = null
let runId = 0
let timeoutHandle = 0
let applyingExample = false
let stackQuery: MediaQueryList | null = null
let editorResizeObserver: ResizeObserver | null = null

const SPLIT_MIN = 22
const SPLIT_MAX = 78
const STACK_MQ = '(max-width: 860px)'

function clampSplit(value: number): number {
  return Math.min(SPLIT_MAX, Math.max(SPLIT_MIN, value))
}

function syncStacked() {
  stacked.value = stackQuery?.matches ?? false
}

function onSplitterPointerDown(event: PointerEvent) {
  if (event.button !== 0 || !workspaceEl.value) {
    return
  }
  event.preventDefault()
  const target = event.currentTarget as HTMLElement
  const rect = workspaceEl.value.getBoundingClientRect()
  const startPos = stacked.value ? event.clientY : event.clientX
  const startPct = splitPct.value
  const size = stacked.value ? rect.height : rect.width
  if (size <= 0) {
    return
  }

  dragging.value = true
  target.setPointerCapture(event.pointerId)

  const onMove = (moveEvent: PointerEvent) => {
    const delta = (stacked.value ? moveEvent.clientY : moveEvent.clientX) - startPos
    splitPct.value = clampSplit(startPct + (delta / size) * 100)
  }

  const onUp = (upEvent: PointerEvent) => {
    dragging.value = false
    target.releasePointerCapture(upEvent.pointerId)
    target.removeEventListener('pointermove', onMove)
    target.removeEventListener('pointerup', onUp)
    target.removeEventListener('pointercancel', onUp)
    editor?.requestMeasure()
  }

  target.addEventListener('pointermove', onMove)
  target.addEventListener('pointerup', onUp)
  target.addEventListener('pointercancel', onUp)
}

function onSplitterKeydown(event: KeyboardEvent) {
  const step = event.shiftKey ? 8 : 3
  const grow =
    (!stacked.value && event.key === 'ArrowRight') ||
    (stacked.value && event.key === 'ArrowDown')
  const shrink =
    (!stacked.value && event.key === 'ArrowLeft') ||
    (stacked.value && event.key === 'ArrowUp')
  if (!grow && !shrink) {
    return
  }
  event.preventDefault()
  splitPct.value = clampSplit(splitPct.value + (grow ? step : -step))
  nextTick(() => editor?.requestMeasure())
}

function workerUrl(): string {
  return `${import.meta.env.BASE_URL}echo-playground-worker.js`
}

function clearTimeoutHandle() {
  if (timeoutHandle) {
    window.clearTimeout(timeoutHandle)
    timeoutHandle = 0
  }
}

function armRunTimeout(id: number) {
  clearTimeoutHandle()
  timeoutHandle = window.setTimeout(() => {
    if (id !== runId || awaitingInput.value) {
      return
    }
    worker?.terminate()
    worker = null
    running.value = false
    awaitingInput.value = false
    draftInput.value = ''
    failed.value = true
    output.value = `Program stopped after ${RUN_TIMEOUT_MS / 1000}s. Infinite loops and long wait() calls are limited in the playground.`
    status.value = 'Timed out'
    startWorker()
  }, RUN_TIMEOUT_MS)
}

function focusConsole() {
  nextTick(() => {
    consoleEl.value?.focus()
    if (consoleEl.value) {
      consoleEl.value.scrollTop = consoleEl.value.scrollHeight
    }
  })
}

function handleWorkerMessage(event: MessageEvent) {
  const data = event.data || {}
  if (data.type === 'status') {
    status.value = data.message
    return
  }
  if (data.type === 'ready') {
    ready.value = true
    status.value = 'Ready'
    return
  }
  if (data.type === 'ask' && data.id === runId) {
    clearTimeoutHandle()
    awaitingInput.value = true
    draftInput.value = ''
    failed.value = false
    output.value = typeof data.output === 'string' ? data.output : ''
    status.value = 'Waiting for input…'
    focusConsole()
    return
  }
  if (data.type === 'result' && data.id === runId) {
    finishRun(Boolean(data.ok), formatResult(data.output, data.error))
    return
  }
  if (data.type === 'failed') {
    if (data.id && data.id !== runId) {
      return
    }
    finishRun(false, data.message || 'Playground failed.')
  }
}

function formatResult(stdout?: string, error?: string): string {
  const chunks = []
  if (stdout) {
    chunks.push(stdout.replace(/\s+$/, ''))
  }
  if (error) {
    chunks.push(error)
  }
  return chunks.join('\n\n') || '(no output)'
}

function finishRun(ok: boolean, text: string) {
  clearTimeoutHandle()
  running.value = false
  awaitingInput.value = false
  draftInput.value = ''
  failed.value = !ok
  output.value = text
  status.value = ok ? 'Finished' : 'Failed'
}

function startWorker() {
  worker?.terminate()
  ready.value = false
  status.value = 'Starting playground…'
  worker = new Worker(workerUrl(), { type: 'module' })
  worker.addEventListener('message', handleWorkerMessage)
  worker.addEventListener('error', (event) => {
    ready.value = false
    running.value = false
    awaitingInput.value = false
    failed.value = true
    status.value = 'Failed'
    output.value = event.message || 'Playground worker failed to start.'
  })
  worker.postMessage({ type: 'init', baseUrl: new URL(import.meta.env.BASE_URL, window.location.origin).href })
}

function setEditorText(text: string) {
  if (!editor) {
    source.value = text
    return
  }
  applyingExample = true
  editor.dispatch({
    changes: { from: 0, to: editor.state.doc.length, insert: text },
  })
  applyingExample = false
  source.value = text
}

function loadExample() {
  const example = EXAMPLES.find((item) => item.id === exampleId.value) ?? EXAMPLES[0]
  setEditorText(example.source)
}

watch(exampleId, loadExample)

function run() {
  if (!worker || !canRun.value) {
    return
  }
  running.value = true
  awaitingInput.value = false
  draftInput.value = ''
  failed.value = false
  status.value = 'Running…'
  output.value = ''
  runId += 1
  const id = runId
  worker.postMessage({ type: 'run', id, source: source.value })
  armRunTimeout(id)
}

function stop() {
  if (!running.value && !awaitingInput.value) {
    return
  }
  clearTimeoutHandle()
  runId += 1
  worker?.terminate()
  worker = null
  running.value = false
  awaitingInput.value = false
  draftInput.value = ''
  failed.value = true
  status.value = 'Stopped'
  output.value = output.value || 'Program stopped.'
  startWorker()
}

function submitInput() {
  if (!worker || !awaitingInput.value) {
    return
  }
  const line = draftInput.value
  output.value = `${output.value}${line}\n`
  draftInput.value = ''
  awaitingInput.value = false
  status.value = 'Running…'
  worker.postMessage({ type: 'stdin', id: runId, line })
  armRunTimeout(runId)
  focusConsole()
}

function onConsoleKeydown(event: KeyboardEvent) {
  if (!awaitingInput.value) {
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    submitInput()
    return
  }
  if (event.key === 'Backspace') {
    event.preventDefault()
    draftInput.value = draftInput.value.slice(0, -1)
    return
  }
  if (event.key === 'Tab') {
    event.preventDefault()
    draftInput.value += '\t'
    return
  }
  if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault()
    draftInput.value += event.key
  }
}

function onConsolePaste(event: ClipboardEvent) {
  if (!awaitingInput.value) {
    return
  }
  event.preventDefault()
  const text = event.clipboardData?.getData('text') ?? ''
  const line = text.split(/\r?\n/, 1)[0] ?? ''
  draftInput.value += line
}

function createEditor() {
  if (!editorHost.value) {
    return
  }
  editor = new EditorView({
    parent: editorHost.value,
    state: EditorState.create({
      doc: source.value,
      extensions: [
        lineNumbers(),
        highlightActiveLine(),
        highlightActiveLineGutter(),
        highlightSelectionMatches(),
        history(),
        echoLanguage,
        syntaxHighlighting(echoHighlight),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        keymap.of([
          {
            key: 'Mod-Enter',
            run: () => {
              run()
              return true
            },
          },
          indentWithTab,
          ...defaultKeymap,
          ...historyKeymap,
          ...searchKeymap,
        ]),
        EditorView.updateListener.of((update) => {
          if (update.docChanged && !applyingExample) {
            source.value = update.state.doc.toString()
          }
        }),
        EditorView.theme({
          '&': {
            height: '100%',
            fontSize: '15px',
          },
          '.cm-scroller': {
            fontFamily: 'var(--vp-font-family-mono)',
            lineHeight: '1.6',
          },
          '.cm-gutters': {
            backgroundColor: 'transparent',
            borderRight: '1px solid var(--vp-c-divider)',
            color: 'var(--vp-c-text-3)',
          },
          '.cm-activeLine': {
            backgroundColor: 'var(--echo-editor-active-line)',
          },
          '.cm-activeLineGutter': {
            backgroundColor: 'transparent',
          },
          '&.cm-focused': {
            outline: 'none',
          },
          '.cm-content': {
            padding: '12px 0',
          },
          '.cm-line': {
            padding: '0 16px 0 8px',
          },
        }),
      ],
    }),
  })
}

onMounted(() => {
  createEditor()
  startWorker()
  stackQuery = window.matchMedia(STACK_MQ)
  syncStacked()
  stackQuery.addEventListener('change', syncStacked)
  if (editorHost.value) {
    editorResizeObserver = new ResizeObserver(() => editor?.requestMeasure())
    editorResizeObserver.observe(editorHost.value)
  }
})

onUnmounted(() => {
  clearTimeoutHandle()
  stackQuery?.removeEventListener('change', syncStacked)
  stackQuery = null
  editorResizeObserver?.disconnect()
  editorResizeObserver = null
  worker?.terminate()
  worker = null
  editor?.destroy()
  editor = null
})
</script>

<template>
  <div class="echo-playground vp-raw">
    <header class="echo-playground__toolbar">
      <div class="echo-playground__identity">
        <strong>Playground</strong>
        <span :data-state="statusKind">{{ status }}</span>
      </div>
      <div class="echo-playground__actions">
        <label class="echo-playground__field">
          <span>Example</span>
          <select v-model="exampleId">
            <option v-for="example in EXAMPLES" :key="example.id" :value="example.id">
              {{ example.label }}
            </option>
          </select>
        </label>
        <button class="echo-playground__run" type="button" :disabled="!canRun" @click="run">
          Run
        </button>
        <button class="echo-playground__stop" type="button" :disabled="!running && !awaitingInput" @click="stop">
          Stop
        </button>
      </div>
    </header>
    <p class="echo-playground__policy">
      No files, processes, or HTTP here — denied builtins abort with E2801. CLI allows them by default.
    </p>

    <div
      ref="workspaceEl"
      class="echo-playground__workspace"
      :class="{ 'is-stacked': stacked, 'is-dragging': dragging }"
      :style="workspaceStyle"
    >
      <section class="echo-playground__panel">
        <div class="echo-playground__panel-bar">
          <span>main.echo</span>
          <span>Ctrl/⌘ Enter</span>
        </div>
        <div ref="editorHost" class="echo-playground__editor" />
      </section>
      <div
        class="echo-playground__splitter"
        role="separator"
        :aria-orientation="stacked ? 'horizontal' : 'vertical'"
        :aria-valuenow="Math.round(splitPct)"
        aria-valuemin="22"
        aria-valuemax="78"
        aria-label="Resize editor and output"
        tabindex="0"
        @pointerdown="onSplitterPointerDown"
        @keydown="onSplitterKeydown"
      />
      <section class="echo-playground__panel">
        <div class="echo-playground__panel-bar">
          <span>Output</span>
          <span v-if="awaitingInput">input</span>
          <span v-else-if="failed">error</span>
        </div>
        <pre
          ref="consoleEl"
          class="echo-playground__output"
          :class="{
            'is-error': failed,
            'is-waiting': awaitingInput,
            'is-placeholder': showPlaceholder,
          }"
          tabindex="0"
          role="textbox"
          :aria-readonly="!awaitingInput"
          aria-label="Program output and input"
          @keydown="onConsoleKeydown"
          @paste="onConsolePaste"
          @click="focusConsole"
        ><template v-if="showPlaceholder">{{ PLACEHOLDER }}</template><template v-else>{{ output }}<span
            v-if="awaitingInput"
            class="echo-playground__draft"
          >{{ draftInput }}</span><span
            v-if="awaitingInput"
            class="echo-playground__caret"
            aria-hidden="true"
          /></template></pre>
      </section>
    </div>
  </div>
</template>
