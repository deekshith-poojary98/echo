const PYODIDE_INDEX = 'https://cdn.jsdelivr.net/pyodide/v0.28.3/full/'

const RUNNER = `
import io
import json
import sys
import time
import traceback
import builtins
from echo.errors import EchoError, format_diagnostic
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
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
_stdin_lines = []

def _playground_input(prompt=""):
    if prompt:
        sys.stdout.write(str(prompt))
        sys.stdout.flush()
    if not _stdin_lines:
        raise EOFError("ask() needs a line in the Input box")
    line = _stdin_lines.pop(0)
    sys.stdout.write(line + "\\n")
    return line

builtins.input = _playground_input

def run_echo(source, stdin_text):
    global _stdin_lines
    _stdin_lines = [line for line in str(stdin_text or "").splitlines()]
    stdout = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = stdout
    try:
        tokens = Lexer().tokenize(source, filename="<playground>")
        program = Parser(tokens).parse()
        SemanticAnalyzer().analyze(program)
        Interpreter().execute(program)
        return json.dumps({"ok": True, "output": stdout.getvalue()})
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
    if (data.type === 'init') {
      runtimeBase = data.baseUrl || runtimeBase
      await ensurePyodide()
      postMessage({ type: 'ready' })
      return
    }
    if (data.type === 'run') {
      const pyodide = await ensurePyodide()
      pyodide.globals.set('playground_source', data.source ?? '')
      pyodide.globals.set('playground_stdin', data.stdin ?? '')
      const raw = pyodide.runPython('run_echo(playground_source, playground_stdin)')
      postMessage({ type: 'result', id: data.id, ...JSON.parse(raw) })
    }
  } catch (error) {
    postMessage({
      type: 'failed',
      id: data.id,
      message: error instanceof Error ? error.message : String(error),
    })
  }
}
