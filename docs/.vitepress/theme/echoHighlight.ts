import { HighlightStyle } from '@codemirror/language'
import { tags as t } from '@lezer/highlight'

export const echoHighlight = HighlightStyle.define([
  { tag: t.keyword, color: 'var(--echo-syn-keyword)', fontWeight: '700' },
  { tag: t.typeName, color: 'var(--echo-syn-type)' },
  { tag: t.string, color: 'var(--echo-syn-string)' },
  { tag: t.special(t.string), color: 'var(--echo-syn-interp)', fontWeight: '650' },
  { tag: t.comment, color: 'var(--echo-syn-comment)', fontStyle: 'italic' },
  { tag: t.number, color: 'var(--echo-syn-number)' },
  { tag: t.bool, color: 'var(--echo-syn-literal)' },
  { tag: t.atom, color: 'var(--echo-syn-literal)' },
  { tag: t.null, color: 'var(--echo-syn-literal)' },
  { tag: t.operator, color: 'var(--echo-syn-operator)' },
  { tag: t.punctuation, color: 'var(--echo-syn-punct)' },
  { tag: t.bracket, color: 'var(--echo-syn-punct)' },
  { tag: t.standard(t.variableName), color: 'var(--echo-syn-builtin)' },
  { tag: t.function(t.variableName), color: 'var(--echo-syn-fn)' },
  { tag: t.definition(t.variableName), color: 'var(--echo-syn-fn)' },
  { tag: t.special(t.variableName), color: 'var(--echo-syn-fn)' },
  { tag: t.variableName, color: 'var(--echo-syn-name)' },
])
