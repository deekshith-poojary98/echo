import { defineConfig } from 'vitepress'
import echoGrammar from '../../echo-syntax-highlighter/syntaxes/echo.tmLanguage.json'

export default defineConfig({
  title: 'Echo',
  description: 'Official documentation for the Echo scripting language',
  base: '/echo/',
  head: [
    ['link', { rel: 'icon', type: 'image/jpeg', href: '/echo/echo_logo.jpg' }],
    ['link', { rel: 'shortcut icon', type: 'image/jpeg', href: '/echo/echo_logo.jpg' }],
    ['link', { rel: 'apple-touch-icon', href: '/echo/echo_logo.jpg' }]
  ],
  cleanUrls: true,
  lastUpdated: true,
  markdown: {
    languages: [
      {
        ...echoGrammar,
        name: 'echo',
        displayName: 'Echo'
      }
    ]
  },
  themeConfig: {
    logo: '/echo_logo.jpg',
    nav: [
      { text: 'Docs', link: '/getting-started/quick-start' },
      { text: 'Examples', link: '/examples/hello-world' },
      { text: 'Reference', link: '/reference/language-reference' },
      { text: 'Limits', link: '/errors-diagnostics/known-limitations' }
    ],
    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Installation', link: '/getting-started/installation' },
          { text: 'Quick Start', link: '/getting-started/quick-start' },
          { text: 'Getting Started', link: '/getting-started/getting-started' },
          { text: 'Syntax Basics', link: '/getting-started/syntax-basics' },
          { text: 'Variables and Types', link: '/getting-started/variables-and-types' },
          { text: 'Strings and Interpolation', link: '/getting-started/strings-and-interpolation' },
          { text: 'Control Flow', link: '/getting-started/control-flow' },
          { text: 'Functions', link: '/getting-started/functions' }
        ]
      },
      {
        text: 'Core Concepts',
        items: [
          { text: 'Lists', link: '/core-concepts/lists' },
          { text: 'Hashes', link: '/core-concepts/hashes' },
          { text: 'Type Aliases', link: '/core-concepts/type-aliases' },
          { text: 'Scope, use, and watch', link: '/core-concepts/scope-use-watch' }
        ]
      },
      {
        text: 'Standard Library',
        items: [
          { text: 'Built-in Methods', link: '/standard-library/built-in-methods' }
        ]
      },
      {
        text: 'Examples',
        items: [
          { text: 'Hello World', link: '/examples/hello-world' },
          { text: 'Lists in Practice', link: '/examples/lists-in-practice' },
          { text: 'Hash Usage', link: '/examples/hash-usage' },
          { text: 'Functions in Practice', link: '/examples/functions-in-practice' },
          { text: 'Mini Programs', link: '/examples/mini-programs' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'Operators', link: '/reference/operators' },
          { text: 'Loops Reference', link: '/reference/loops-reference' },
          { text: 'CLI and Execution Model', link: '/reference/cli-and-execution-model' },
          { text: 'Language Reference', link: '/reference/language-reference' }
        ]
      },
      {
        text: 'Errors & Diagnostics',
        items: [
          { text: 'Errors and Troubleshooting', link: '/errors-diagnostics/errors-and-troubleshooting' },
          { text: 'Known Limitations', link: '/errors-diagnostics/known-limitations' }
        ]
      },
      {
        text: 'Project',
        items: [
          { text: 'Roadmap / Planned Improvements', link: '/project/roadmap' }
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/deekshith-poojary98/echo' }
    ],
    search: {
      provider: 'local'
    },
    outline: [2, 3],
    footer: {
      message: 'Echo is in active development. The docs reflect the current implementation.',
      copyright: 'Echo Documentation'
    },
    docFooter: {
      prev: 'Previous page',
      next: 'Next page'
    }
  }
})
