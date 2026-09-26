const PYODIDE_INDEX = 'https://cdn.jsdelivr.net/pyodide/v0.28.3/full/'

const RUNNER = `
import io
import json
import sys
import time
import traceback
import builtins
from js import playgroundAsk
from pyodide.ffi import run_sync
from echo.errors import EchoError, EchoExit, format_diagnostic
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.runtime.host import Host
from echo.runtime.interpreter import Interpreter
from echo.semantics.analyzer import SemanticAnalyzer

_orig_sleep = time.sleep

def _capped_sleep(seconds):
    try:
        delay = float(seconds)
    except (TypeError, ValueError):
        delay = 0
    _orig_sleep(min(max(delay, 0.0), 0.25))

time.sleep = _capped_sleep

def _playground_input(prompt=""):
    if prompt:
        sys.stdout.write(str(prompt))
        sys.stdout.flush()
    out = sys.stdout.getvalue() if hasattr(sys.stdout, "getvalue") else ""
    line = run_sync(playgroundAsk(out))
    line = "" if line is None else str(line)
    if line.endswith("\\r\\n"):
        line = line[:-2]
    elif line.endswith("\\n") or line.endswith("\\r"):
        line = line[:-1]
    sys.stdout.write(line + "\\n")
    return line

builtins.input = _playground_input

def run_echo(source):
    stdout = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = stdout
    try:
        tokens = Lexer().tokenize(source, filename="<playground>")
        program = Parser(tokens).parse()
        SemanticAnalyzer().analyze(program)
        Interpreter(Host(allow_files=False, allow_run=False, allow_http=False, environ={})).execute(program)
        return json.dumps({"ok": True, "output": stdout.getvalue()})
    except EchoExit as exc:
        payload = {"ok": exc.code == 0, "output": stdout.getvalue()}
        if exc.code != 0:
            payload["error"] = f"exit({exc.code})"
        return json.dumps(payload)
    except EchoError as exc:
        return json.dumps({"ok": False, "output": stdout.getvalue(), "error": format_diagnostic(exc, source)})
    except EOFError as exc:
        return json.dumps({"ok": False, "output": stdout.getvalue(), "error": str(exc)})
    except Exception:
        return json.dumps({"ok": False, "output": stdout.getvalue(), "error": traceback.format_exc()})
    finally:
        sys.stdout, sys.stderr = old_out, old_err
`

let pyodidePromise = null
let runtimeBase = ''
let currentRunId = 0
let pendingAsk = null

function rejectPendingAsk(reason) {
  if (!pendingAsk) {
    return
  }
  const { reject } = pendingAsk
  pendingAsk = null
  reject(reason instanceof Error ? reason : new Error(String(reason || 'cancelled')))
}

function playgroundAsk(outputSoFar) {
  return new Promise((resolve, reject) => {
    rejectPendingAsk(new Error('Overlapping ask()'))
    pendingAsk = { resolve, reject, id: currentRunId }
    postMessage({
      type: 'ask',
      id: currentRunId,
      output: outputSoFar == null ? '' : String(outputSoFar),
    })
  })
}

self.playgroundAsk = playgroundAsk

function runtimeUrl(file) {
  return new URL(`echo-runtime/${file}`, runtimeBase || self.location.href).href
}

async function loadEcho(pyodide) {
  const manifestRes = await fetch(runtimeUrl('manifest.json'))
  if (!manifestRes.ok) {
    throw new Error(`Failed to load Echo runtime manifest (${manifestRes.status})`)
  }
  const manifest = await manifestRes.json()
  pyodide.FS.mkdirTree('/home/pyodide/echo')
  for (const file of manifest.files) {
    const response = await fetch(runtimeUrl(file))
    if (!response.ok) {
      throw new Error(`Failed to load Echo file ${file}`)
    }
    const dest = `/home/pyodide/echo/${file}`
    pyodide.FS.mkdirTree(dest.slice(0, dest.lastIndexOf('/')))
    pyodide.FS.writeFile(dest, await response.text())
  }
  pyodide.runPython(`
import sys
sys.path.insert(0, "/home/pyodide")
${RUNNER}
`)
}

async function ensurePyodide() {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      postMessage({ type: 'status', message: 'Downloading Python runtime…' })
      const { loadPyodide } = await import(`${PYODIDE_INDEX}pyodide.mjs`)
      const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX })
      postMessage({ type: 'status', message: 'Loading Echo…' })
      await loadEcho(pyodide)
      return pyodide
    })()
  }
  return pyodidePromise
}

self.onmessage = async (event) => {
  const data = event.data || {}
  try {
    if (data.type === 'stdin') {
      if (pendingAsk && pendingAsk.id === data.id) {
        const { resolve } = pendingAsk
        pendingAsk = null
        resolve(data.line ?? '')
      }
      return
    }
    if (data.type === 'init') {
      runtimeBase = data.baseUrl || runtimeBase
      await ensurePyodide()
      postMessage({ type: 'ready' })
      return
    }
    if (data.type === 'run') {
      currentRunId = data.id
      rejectPendingAsk(new Error('cancelled'))
      const pyodide = await ensurePyodide()
      pyodide.globals.set('playground_source', data.source ?? '')
      const raw = await pyodide.runPythonAsync('run_echo(playground_source)')
      postMessage({ type: 'result', id: data.id, ...JSON.parse(raw) })
      return
    }
  } catch (error) {
    rejectPendingAsk(error)
    postMessage({
      type: 'failed',
      id: data.id,
      message: error instanceof Error ? error.message : String(error),
    })
  }
}
