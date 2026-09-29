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
      { text: 'Start', link: '/start/choose-your-path' },
      { text: 'Learn', link: '/learn/first-program' },
      { text: 'Practice', link: '/practice/change-predict-fix' },
      { text: 'Playground', link: '/playground' },
      { text: 'Reference', link: '/reference/language-reference' },
      { text: 'Advanced', link: '/getting-started/tour' }
    ],
    sidebar: [
      {
        text: 'Start here',
        items: [
          { text: 'Choose your path', link: '/start/choose-your-path' },
          { text: 'Install Echo', link: '/getting-started/installation' },
          { text: 'Playground', link: '/playground' },
          { text: 'Quick Start (short)', link: '/getting-started/quick-start' }
        ]
      },
      {
        text: 'Learn Echo',
        items: [
          { text: '1. Your first program', link: '/learn/first-program' },
          { text: '2. Values and variables', link: '/learn/values-and-variables' },
          { text: '3. Making decisions', link: '/learn/making-decisions' },
          { text: '4. Repeating things', link: '/learn/repeating-things' },
          { text: '5. Functions', link: '/learn/functions' },
          { text: '6. Lists and hashes', link: '/learn/lists-and-hashes' },
          { text: '7. Strings', link: '/learn/strings' },
          { text: '8. Organizing programs', link: '/learn/modules' },
          { text: '9. Classes', link: '/learn/classes' }
        ]
      },
      {
        text: 'Practice',
        items: [
          { text: 'Change, predict, fix', link: '/practice/change-predict-fix' },
          { text: 'Small exercises', link: '/practice/small-exercises' },
          { text: 'Mini projects', link: '/practice/mini-projects' }
        ]
      },
      {
        text: 'When something goes wrong',
        items: [
          { text: 'Common mistakes', link: '/errors-diagnostics/common-mistakes' },
          { text: 'Error codes (reference)', link: '/errors-diagnostics/errors-and-troubleshooting' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'Language Reference', link: '/reference/language-reference' },
          { text: 'Language Semantics', link: '/language-semantics' },
          { text: 'Module Semantics', link: '/module-semantics' },
          { text: 'Operators', link: '/reference/operators' },
          { text: 'Loops Reference', link: '/reference/loops-reference' },
          { text: 'CLI and Execution Model', link: '/reference/cli-and-execution-model' },
          { text: 'Built-in Methods', link: '/standard-library/built-in-methods' },
          { text: 'Builtin Inventory', link: '/reference/builtin-inventory' },
          { text: 'Std Inventory', link: '/reference/std-inventory' },
          { text: 'Failure Model', link: '/failure-model' },
          { text: 'Known Limitations', link: '/errors-diagnostics/known-limitations' }
        ]
      },
      {
        text: 'Advanced',
        items: [
          { text: 'Language Tour (for programmers)', link: '/getting-started/tour' },
          { text: 'Syntax Basics', link: '/getting-started/syntax-basics' },
          { text: 'Variables and Types (full)', link: '/getting-started/variables-and-types' },
          { text: 'Strings and Interpolation (full)', link: '/getting-started/strings-and-interpolation' },
          { text: 'Control Flow (full)', link: '/getting-started/control-flow' },
          { text: 'Functions (full)', link: '/getting-started/functions' },
          { text: 'Scope, use, and watch', link: '/core-concepts/scope-use-watch' },
          { text: 'Lists (methods)', link: '/core-concepts/lists' },
          { text: 'Hashes (methods)', link: '/core-concepts/hashes' },
          { text: 'Type Aliases', link: '/core-concepts/type-aliases' },
          { text: 'Classes and Interfaces (full)', link: '/examples/classes-and-interfaces' },
          { text: 'Modules (full)', link: '/getting-started/modules' }
        ]
      },
      {
        text: 'Examples',
        items: [
          { text: 'Hello World', link: '/examples/hello-world' },
          { text: 'Lists in Practice', link: '/examples/lists-in-practice' },
          { text: 'Hash Usage', link: '/examples/hash-usage' },
          { text: 'Functions in Practice', link: '/examples/functions-in-practice' },
          { text: 'Mini Programs', link: '/examples/mini-programs' },
          { text: 'Algorithm Examples', link: '/examples/algorithms' }
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
