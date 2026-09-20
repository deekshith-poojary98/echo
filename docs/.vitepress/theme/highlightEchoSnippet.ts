const KEYWORDS = new Set([
  'if',
  'else',
  'while',
  'for',
  'foreach',
  'switch',
  'return',
  'break',
  'continue',
  'in',
  'by',
  'as',
  'fn',
  'watch',
  'type',
  'use',
  'mut',
  'import',
  'export',
  'from',
  'const',
  'exact',
  'class',
  'interface',
  'new',
  'implements',
  'this',
])

const TYPES = new Set(['int', 'float', 'str', 'bool', 'list', 'hash', 'dynamic', 'void'])
const LITERALS = new Set(['true', 'false', 'null'])
const BUILTINS = new Set(['say', 'ask', 'assert', 'type', 'len', 'push', 'map', 'filter'])

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function span(kind: string, text: string): string {
  return `<span class="echo-tok echo-tok--${kind}">${escapeHtml(text)}</span>`
}

/** Lightweight Echo highlighter for static homepage snippets. */
export function highlightEchoSnippet(source: string): string {
  let out = ''
  let i = 0

  while (i < source.length) {
    const ch = source[i]

    if (ch === '/' && source[i + 1] === '/') {
      const end = source.indexOf('\n', i)
      const slice = end === -1 ? source.slice(i) : source.slice(i, end)
      out += span('comment', slice)
      i += slice.length
      continue
    }

    if (ch === '"' || ch === "'") {
      const quote = ch
      let j = i + 1
      let text = quote
      while (j < source.length) {
        const c = source[j]
        text += c
        if (c === '\\' && j + 1 < source.length) {
          text += source[j + 1]
          j += 2
          continue
        }
        if (c === quote) {
          j += 1
          break
        }
        j += 1
      }
      // Split ${...} interpolations inside strings.
      let rendered = ''
      let k = 0
      while (k < text.length) {
        if (text.startsWith('${', k)) {
          const close = text.indexOf('}', k + 2)
          if (close === -1) {
            rendered += span('string', text.slice(k))
            break
          }
          rendered += span('interp', text.slice(k, close + 1))
          k = close + 1
          continue
        }
        let next = text.indexOf('${', k)
        if (next === -1) {
          next = text.length
        }
        if (next > k) {
          rendered += span('string', text.slice(k, next))
        }
        k = next
      }
      out += rendered
      i = j
      continue
    }

    if (/[0-9]/.test(ch) || (ch === '.' && /[0-9]/.test(source[i + 1] || ''))) {
      const match = source.slice(i).match(/^(?:\.[0-9]+|[0-9]+(?:\.[0-9]+)?)(?:[eE][+-]?[0-9]+)?/)
      if (match) {
        out += span('number', match[0])
        i += match[0].length
        continue
      }
    }

    if (/[A-Za-z_]/.test(ch)) {
      const match = source.slice(i).match(/^[A-Za-z_][A-Za-z0-9_]*/)
      if (match) {
        const word = match[0]
        const after = source.slice(i + word.length)
        const isCall = /^\s*\(/.test(after)
        if (KEYWORDS.has(word)) {
          out += span('keyword', word)
        } else if (TYPES.has(word)) {
          out += span('type', word)
        } else if (LITERALS.has(word)) {
          out += span('literal', word)
        } else if (BUILTINS.has(word) || isCall) {
          out += span(BUILTINS.has(word) || isCall ? 'fn' : 'name', word)
        } else {
          out += span('name', word)
        }
        i += word.length
        continue
      }
    }

    if ('{}[]();,.:+-*/%=<>!|&?'.includes(ch)) {
      let j = i + 1
      // Capture multi-char ops lightly
      if ((ch === '=' || ch === '!' || ch === '<' || ch === '>') && source[j] === '=') {
        j += 1
      } else if (ch === '-' && source[j] === '>') {
        j += 1
      }
      out += span('punct', source.slice(i, j))
      i = j
      continue
    }

    out += escapeHtml(ch)
    i += 1
  }

  return out
}
