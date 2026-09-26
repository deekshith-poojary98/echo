import { defineConfig } from 'vitepress'
import echoGrammar from '../../echo-syntax-highlighter/syntaxes/echo.tmLanguage.json'
import { echoRuntimePlugin } from './plugins/echo-runtime'

export default defineConfig({
  title: 'Echo',
  description: 'Official documentation for the Echo scripting language',
  base: '/echo/',
  head: [
    ['link', { rel: 'icon', type: 'image/jpeg', href: '/echo/echo_logo.jpg' }],
    ['link', { rel: 'shortcut icon', type: 'image/jpeg', href: '/echo/echo_logo.jpg' }],
    ['link', { rel: 'apple-touch-icon', href: '/echo/echo_logo.jpg' }],
    [
      'link',
      {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,550;9..144,650&family=IBM+Plex+Mono:wght@400;500&display=swap'
      }
    ]
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
    siteTitle: false,
    nav: [
      { text: 'Install', link: '/getting-started/installation' },
      { text: 'Learn', link: '/getting-started/quick-start' },
      { text: 'Playground', link: '/playground' },
      { text: 'Examples', link: '/examples/hello-world' },
      { text: 'Reference', link: '/reference/language-reference' },
      { text: 'Limits', link: '/errors-diagnostics/known-limitations' }
    ],
    sidebar: [
      {
        text: 'Start',
        items: [
          { text: 'Installation', link: '/getting-started/installation' },
          { text: 'Quick Start', link: '/getting-started/quick-start' },
          { text: 'Playground', link: '/playground' }
        ]
      },
      {
        text: 'Language',
        items: [
          { text: 'Language Tour', link: '/getting-started/tour' },
          { text: 'Syntax Basics', link: '/getting-started/syntax-basics' },
          { text: 'Variables and Types', link: '/getting-started/variables-and-types' },
          { text: 'Strings and Interpolation', link: '/getting-started/strings-and-interpolation' },
          { text: 'Control Flow', link: '/getting-started/control-flow' },
          { text: 'Functions', link: '/getting-started/functions' },
          { text: 'Scope, use, and watch', link: '/core-concepts/scope-use-watch' }
        ]
      },
      {
        text: 'Data',
        items: [
          { text: 'Lists', link: '/core-concepts/lists' },
          { text: 'Hashes', link: '/core-concepts/hashes' },
          { text: 'Type Aliases', link: '/core-concepts/type-aliases' }
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
          { text: 'Classes and Interfaces', link: '/examples/classes-and-interfaces' },
          { text: 'Lists in Practice', link: '/examples/lists-in-practice' },
          { text: 'Hash Usage', link: '/examples/hash-usage' },
          { text: 'Functions in Practice', link: '/examples/functions-in-practice' },
          { text: 'Mini Programs', link: '/examples/mini-programs' },
          { text: 'Algorithm Examples', link: '/examples/algorithms' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'Language Reference', link: '/reference/language-reference' },
          { text: 'Operators', link: '/reference/operators' },
          { text: 'Loops Reference', link: '/reference/loops-reference' },
          { text: 'CLI and Execution Model', link: '/reference/cli-and-execution-model' },
          { text: 'Builtin Inventory', link: '/reference/builtin-inventory' },
          { text: 'Failure Model', link: '/failure-model' }
        ]
      },
      {
        text: 'Errors',
        items: [
          { text: 'Errors and Troubleshooting', link: '/errors-diagnostics/errors-and-troubleshooting' },
          { text: 'Known Limitations', link: '/errors-diagnostics/known-limitations' }
        ]
      },
      {
        text: 'Project',
        items: [
          { text: 'Roadmap', link: '/project/roadmap' }
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
  },
  vite: {
    plugins: [echoRuntimePlugin()],
    worker: {
      format: 'es'
    },
    server: {
      fs: {
        allow: ['..']
      }
    }
  }
})
