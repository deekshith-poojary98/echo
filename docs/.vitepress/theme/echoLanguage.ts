import { StreamLanguage } from '@codemirror/language'
import type { StreamParser } from '@codemirror/language'

const KEYWORDS = new Set([
  'if',
  'else',
  'while',
  'for',
  'foreach',
  'return',
  'break',
  'continue',
  'in',
  'by',
  'fn',
  'watch',
  'type',
  'use',
  'mut',
  'import',
  'export',
  'from',
  'as',
])

const TYPES = new Set(['int', 'float', 'str', 'bool', 'list', 'hash', 'dynamic', 'void'])
const LITERALS = new Set(['true', 'false', 'null'])
const BUILTINS = new Set([
  'wait',
  'ask',
  'say',
  'asInt',
  'asFloat',
  'asBool',
  'asString',
  'type',
  'trim',
  'upperCase',
  'lowerCase',
  'length',
  'keys',
  'values',
  'reverse',
  'push',
  'empty',
  'clone',
  'countOf',
  'merge',
  'find',
  'insertAt',
  'pull',
  'removeValue',
  'order',
  'wipe',
  'take',
  'take_last',
  'ensure',
  'pairs',
  'default',
  'format',
])

type EchoState = {
  comment: boolean
  quote: '"' | "'" | null
  interp: number
}

const echoParser: StreamParser<EchoState> = {
  name: 'echo',
  startState() {
    return { comment: false, quote: null, interp: 0 }
  },
  copyState(state) {
    return { ...state }
  },
  token(stream, state) {
    if (state.comment) {
      if (stream.match(/.*?\*\//)) {
        state.comment = false
      } else {
        stream.skipToEnd()
      }
      return 'comment'
    }

    if (state.quote && state.interp === 0) {
      if (stream.match('${')) {
        state.interp = 1
        return 'string-2'
      }
      if (stream.match('\\')) {
        stream.next()
        return 'string'
      }
      if (stream.next() === state.quote) {
        state.quote = null
      }
      return 'string'
    }

    if (stream.eatSpace()) {
      return null
    }

    if (stream.match('//')) {
      stream.skipToEnd()
      return 'comment'
    }
    if (stream.match('/*')) {
      state.comment = true
      return 'comment'
    }

    if (state.interp > 0 && stream.peek() === '{') {
      stream.next()
      state.interp += 1
      return 'bracket'
    }
    if (state.interp > 0 && stream.peek() === '}') {
      stream.next()
      state.interp -= 1
      return state.interp === 0 ? 'string-2' : 'bracket'
    }

    if (stream.match('"') || stream.match("'")) {
      state.quote = stream.current() as '"' | "'"
      return 'string'
    }

    if (stream.match(/0x[0-9a-fA-F]+/) || stream.match(/0b[01]+/) || stream.match(/\d+(?:\.\d+)?/)) {
      return 'number'
    }

    if (stream.match(/&&|\|\||==|!=|<=|>=|\+=|-=|\*=|\/=|%=|->|=>|\.\.\.|\.\./)) {
      return 'operator'
    }
    if (stream.match(/[+\-*/%=<>!]/)) {
      return 'operator'
    }
    if (stream.match(/[()[\]{},.:;]/)) {
      return 'punctuation'
    }

    if (stream.match(/[A-Za-z_][A-Za-z0-9_]*/)) {
      const word = stream.current()
      if (KEYWORDS.has(word)) {
        return 'keyword'
      }
      if (TYPES.has(word)) {
        return 'type'
      }
      if (LITERALS.has(word)) {
        return 'atom'
      }
      if (BUILTINS.has(word)) {
        return 'builtin'
      }
      const after = stream.string.slice(stream.pos).match(/^\s*\(/)
      if (after) {
        return 'def'
      }
      return 'variable'
    }

    stream.next()
    return null
  },
  languageData: {
    commentTokens: { line: '//', block: { open: '/*', close: '*/' } },
    closeBrackets: { brackets: ['(', '[', '{', '"', "'"] },
  },
}

export const echoLanguage = StreamLanguage.define(echoParser)
