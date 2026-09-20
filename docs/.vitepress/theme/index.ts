import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import './custom.css'
import HomeLanding from './HomeLanding.vue'
import Playground from './Playground.vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('HomeLanding', HomeLanding)
    app.component('Playground', Playground)
  }
} satisfies Theme
