import { StreamLanguage } from '@codemirror/language'
import type { StreamParser } from '@codemirror/language'

// Keywords and type names: src/echo/frontend/tokens.py (KEYWORDS, TYPE_NAMES).
// `true` / `false` / `null` are literals, not keywords.
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
  'priv',
])

const TYPES = new Set(['int', 'float', 'str', 'bool', 'list', 'hash', 'dynamic', 'void'])
const LITERALS = new Set(['true', 'false', 'null'])

// Keep in sync with BUILTIN_NAMES in src/echo/runtime/builtins.py
// (and echo-syntax-highlighter/syntaxes/echo.tmLanguage.json). Names highlight as values and calls.
const BUILTINS = new Set([
  'abs',
  'args',
  'asBool',
  'asFloat',
  'asFloatOr',
  'asInt',
  'asIntOr',
  'ask',
  'assert',
  'asString',
  'ceil',
  'chunk',
  'clone',
  'contains',
  'copyFile',
  'countOf',
  'cwd',
  'default',
  'empty',
  'endsWith',
  'ensure',
  'env',
  'envOr',
  'eprint',
  'every',
  'exit',
  'expect',
  'expectEq',
  'expectNeq',
  'fail',
  'fileExists',
  'filter',
  'find',
  'findIndex',
  'flatMap',
  'flatten',
  'floor',
  'forEach',
  'format',
  'has',
  'indexOf',
  'insertAt',
  'isDir',
  'join',
  'keys',
  'lastIndexOf',
  'length',
  'listFiles',
  'lowerCase',
  'map',
  'mapValues',
  'max',
  'merge',
  'min',
  'mkdir',
  'mkdirAll',
  'now',
  'order',
  'padEnd',
  'padStart',
  'pairs',
  'parseJson',
  'parseJsonOr',
  'partition',
  'pathJoin',
  'pull',
  'push',
  'random',
  'randomInt',
  'rangeList',
  'rangeListInclusive',
  'readFile',
  'readFileOr',
  'readLine',
  'reduce',
  'removeFile',
  'removeTree',
  'removeValue',
  'repeat',
  'replace',
  'replaceFirst',
  'reverse',
  'run',
  'say',
  'slice',
  'some',
  'split',
  'startsWith',
  'take',
  'take_last',
  'trim',
  'type',
  'unique',
  'upperCase',
  'values',
  'wait',
  'wipe',
  'writeFile',
  'writeJson',
  'zip',
])

const NUMBER_RE = /^(?:\.[0-9]+|[0-9]+(?:\.[0-9]+)?)(?:[eE][+-]?[0-9]+)?/
const IDENT_RE = /^[A-Za-z_][A-Za-z0-9_]*/
const CONSTANT_RE = /^[A-Z_][A-Z0-9_]*$/
const CALL_AFTER_RE = /^\s*\(/

type StringFrame = { kind: 'string'; quote: '"' | "'"; triple: boolean }
type InterpFrame = { kind: 'interp'; depth: number }
type CommentFrame = { kind: 'comment' }
type Frame = StringFrame | InterpFrame | CommentFrame

type EchoState = {
  stack: Frame[]
  afterFn: boolean
  afterType: boolean
}

function topFrame(state: EchoState): Frame | undefined {
  return state.stack[state.stack.length - 1]
}

function clearDecl(state: EchoState) {
  state.afterFn = false
  state.afterType = false
}

type EchoStream = Parameters<StreamParser<EchoState>['token']>[0]

function tokenBlockComment(stream: EchoStream, state: EchoState): string {
  if (stream.match(/^.*?\*\//)) {
    state.stack.pop()
  } else {
    stream.skipToEnd()
  }
  return 'comment'
}

function tokenString(stream: EchoStream, state: EchoState, frame: StringFrame): string {
  if (stream.match('${')) {
    state.stack.push({ kind: 'interp', depth: 0 })
    return 'keyword'
  }
  if (stream.match('\\')) {
    if (!stream.eol()) {
      stream.next()
    }
    return 'string'
  }

  const closer = frame.triple ? frame.quote.repeat(3) : frame.quote
  if (stream.match(closer)) {
    state.stack.pop()
    return 'string'
  }

  while (!stream.eol()) {
    const next = stream.peek()
    if (next === '\\') {
      break
    }
    if (next === '$' && stream.string.startsWith('${', stream.pos)) {
      break
    }
    if (frame.triple) {
      if (next === frame.quote && stream.string.startsWith(closer, stream.pos)) {
        break
      }
    } else if (next === frame.quote) {
      break
    }
    stream.next()
  }
  return 'string'
}

function tokenCode(stream: EchoStream, state: EchoState): string | null {
  const interp = topFrame(state)
  const inInterp = interp?.kind === 'interp' ? interp : null

  if (inInterp) {
    if (stream.peek() === '{') {
      stream.next()
      inInterp.depth += 1
      clearDecl(state)
      return 'bracket'
    }
    if (stream.peek() === '}') {
      stream.next()
      if (inInterp.depth == 0) {
        state.stack.pop()
        clearDecl(state)
        return 'keyword'
      }
      inInterp.depth -= 1
      clearDecl(state)
      return 'bracket'
    }
  }

  if (stream.match(NUMBER_RE)) {
    clearDecl(state)
    return 'number'
  }

  if (stream.match(/^(?:&&|\|\||==|!=|<=|>=|\+=|-=|\*=|\/=|%=|->|=>|\.\.\.|\.\.)/)) {
    clearDecl(state)
    return 'operator'
  }
  if (stream.match(/^[+\-*/%=<>!]/)) {
    clearDecl(state)
    return 'operator'
  }
  // Brackets and colon cover index `xs[i]` and slices `xs[1:4]` / `xs[1:]` / `xs[:4]` / `xs[:]`.
  if (stream.match(/^[()[\]{},.:;]/)) {
    clearDecl(state)
    return 'punctuation'
  }

  if (stream.match(IDENT_RE)) {
    const word = stream.current()
    const isCall = CALL_AFTER_RE.test(stream.string.slice(stream.pos))

    if (state.afterFn) {
      clearDecl(state)
      return 'def'
    }
    if (state.afterType) {
      clearDecl(state)
      return 'type'
    }

    if (word === 'fn') {
      state.afterFn = true
      state.afterType = false
      return 'keyword'
    }
    if (word === 'type') {
      state.afterType = true
      state.afterFn = false
      return 'keyword'
    }
    if (word === 'this') {
      clearDecl(state)
      return 'keyword'
    }
    if (KEYWORDS.has(word)) {
      clearDecl(state)
      return 'keyword'
    }
    if (TYPES.has(word)) {
      clearDecl(state)
      return 'type'
    }
    if (LITERALS.has(word)) {
      clearDecl(state)
      return 'atom'
    }
    if (BUILTINS.has(word)) {
      clearDecl(state)
      return 'builtin'
    }
    if (isCall) {
      clearDecl(state)
      return 'def'
    }
    if (CONSTANT_RE.test(word) && /[A-Z]/.test(word)) {
      clearDecl(state)
      return 'atom'
    }
    clearDecl(state)
    return 'variable'
  }

  stream.next()
  clearDecl(state)
  return null
}

const echoParser: StreamParser<EchoState> = {
  name: 'echo',
  startState() {
    return { stack: [], afterFn: false, afterType: false }
  },
  copyState(state) {
    return {
      stack: state.stack.map((frame) => ({ ...frame })),
      afterFn: state.afterFn,
      afterType: state.afterType,
    }
  },
  token(stream, state) {
    const top = topFrame(state)
    if (top?.kind === 'comment') {
      return tokenBlockComment(stream, state)
    }
    if (top?.kind === 'string') {
      return tokenString(stream, state, top)
    }

    if (stream.eatSpace()) {
      return null
    }

    if (stream.match('//')) {
      stream.skipToEnd()
      return 'comment'
    }
    if (stream.match('/*')) {
      state.stack.push({ kind: 'comment' })
      return 'comment'
    }

    if (stream.match('"""') || stream.match("'''")) {
      clearDecl(state)
      const quote = stream.current()[0] as '"' | "'"
      state.stack.push({ kind: 'string', quote, triple: true })
      return 'string'
    }
    if (stream.match('"') || stream.match("'")) {
      clearDecl(state)
      const quote = stream.current() as '"' | "'"
      state.stack.push({ kind: 'string', quote, triple: false })
      return 'string'
    }

    return tokenCode(stream, state)
  },
  languageData: {
    commentTokens: { line: '//', block: { open: '/*', close: '*/' } },
    closeBrackets: { brackets: ['(', '[', '{', '"', "'"] },
  },
}

export const echoLanguage = StreamLanguage.define(echoParser)
