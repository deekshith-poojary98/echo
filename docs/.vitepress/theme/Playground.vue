<script setup lang="ts">
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language'
import { highlightSelectionMatches, searchKeymap } from '@codemirror/search'
import { EditorState } from '@codemirror/state'
import { EditorView, highlightActiveLine, highlightActiveLineGutter, keymap, lineNumbers } from '@codemirror/view'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { echoLanguage } from './echoLanguage'
import { echoHighlight } from './echoHighlight'
import gradebookSource from '../../../complex_example.echo?raw'

type Example = {
  id: string
  label: string
  stdin: string
  source: string
}

const EXAMPLES: Example[] = [
  {
    id: 'hello',
    label: 'Hello',
    stdin: '',
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
    stdin: '',
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
    stdin: '',
    source: `words: list = ["a", "b", "a"];
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
    id: 'functions',
    label: 'Functions',
    stdin: '',
    source: `fn describe(name: str, age: int) {
    say(name, "is", age);
}

describe(age: 21, name: "Alice");
`,
  },
  {
    id: 'fizzbuzz',
    label: 'FizzBuzz',
    stdin: '',
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
    stdin: 'Ada\n',
    source: `name: str = ask("Name: ");
say("Hello, \${name}!");
`,
  },
  {
    id: 'gradebook',
    label: 'Gradebook (complex)',
    stdin: '',
    source: gradebookSource,
  },
]

const RUN_TIMEOUT_MS = 8000

const editorHost = ref<HTMLElement | null>(null)
const exampleId = ref(EXAMPLES[0].id)
const source = ref(EXAMPLES[0].source)
const stdin = ref(EXAMPLES[0].stdin)
const output = ref('')
const failed = ref(false)
const status = ref('Starting playground…')
const ready = ref(false)
const running = ref(false)

const canRun = computed(() => ready.value && !running.value && source.value.trim().length > 0)
const statusKind = computed(() => (failed.value ? 'error' : running.value ? 'running' : ready.value ? 'ready' : 'boot'))

let worker: Worker | null = null
let editor: EditorView | null = null
let runId = 0
let timeoutHandle = 0
let applyingExample = false

function workerUrl(): string {
  return `${import.meta.env.BASE_URL}echo-playground-worker.js`
}

function clearTimeoutHandle() {
  if (timeoutHandle) {
    window.clearTimeout(timeoutHandle)
    timeoutHandle = 0
  }
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
  stdin.value = example.stdin
}

watch(exampleId, loadExample)

function run() {
  if (!worker || !canRun.value) {
    return
  }
  running.value = true
  failed.value = false
  status.value = 'Running…'
  output.value = ''
  runId += 1
  const id = runId
  worker.postMessage({ type: 'run', id, source: source.value, stdin: stdin.value })
  timeoutHandle = window.setTimeout(() => {
    if (id !== runId) {
      return
    }
    worker?.terminate()
    worker = null
    running.value = false
    failed.value = true
    output.value = `Program stopped after ${RUN_TIMEOUT_MS / 1000}s. Infinite loops and long wait() calls are limited in the playground.`
    status.value = 'Timed out'
    startWorker()
  }, RUN_TIMEOUT_MS)
}

function stop() {
  if (!running.value) {
    return
  }
  clearTimeoutHandle()
  runId += 1
  worker?.terminate()
  worker = null
  running.value = false
  failed.value = true
  status.value = 'Stopped'
  output.value = output.value || 'Program stopped.'
  startWorker()
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
})

onUnmounted(() => {
  clearTimeoutHandle()
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
        <button class="echo-playground__stop" type="button" :disabled="!running" @click="stop">
          Stop
        </button>
      </div>
    </header>

    <div class="echo-playground__workspace">
      <section class="echo-playground__panel">
        <div class="echo-playground__panel-bar">
          <span>main.echo</span>
          <span>Ctrl/⌘ Enter</span>
        </div>
        <div ref="editorHost" class="echo-playground__editor" />
      </section>
      <section class="echo-playground__panel">
        <div class="echo-playground__panel-bar">
          <span>Output</span>
          <span v-if="failed">error</span>
        </div>
        <pre class="echo-playground__output" :class="{ 'is-error': failed }">{{ output || 'Output appears here after you run a program.' }}</pre>
      </section>
      <label class="echo-playground__stdin">
        <span>ask() input</span>
        <textarea
          v-model="stdin"
          spellcheck="false"
          placeholder="One line per ask() call"
        />
      </label>
    </div>
  </div>
</template>
