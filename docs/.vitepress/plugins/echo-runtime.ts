import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const echoSrc = path.resolve(pluginDir, '../../../src/echo')
const outDir = path.resolve(pluginDir, '../../public/echo-runtime')

function collectPythonFiles(dir: string, rel = ''): string[] {
  const files: string[] = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '__pycache__' || entry.name.startsWith('.')) {
      continue
    }
    const nextRel = rel ? `${rel}/${entry.name}` : entry.name
    const nextPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...collectPythonFiles(nextPath, nextRel))
      continue
    }
    if (entry.name.endsWith('.py')) {
      files.push(nextRel.replaceAll('\\', '/'))
    }
  }
  return files
}

export function copyEchoRuntime(): string[] {
  if (!fs.existsSync(echoSrc)) {
    throw new Error(`Echo sources not found at ${echoSrc}`)
  }
  fs.rmSync(outDir, { recursive: true, force: true })
  const files = collectPythonFiles(echoSrc)
  for (const rel of files) {
    const dest = path.join(outDir, rel)
    fs.mkdirSync(path.dirname(dest), { recursive: true })
    fs.copyFileSync(path.join(echoSrc, rel), dest)
  }
  fs.mkdirSync(outDir, { recursive: true })
  fs.writeFileSync(path.join(outDir, 'manifest.json'), `${JSON.stringify({ files }, null, 2)}\n`)
  return files
}

function sendRuntimeFile(url: string | undefined, res: import('node:http').ServerResponse, next: () => void) {
  const raw = (url || '').split('?')[0]
  const prefixes = ['/echo/echo-runtime/', '/echo-runtime/']
  const prefix = prefixes.find((item) => raw.startsWith(item))
  if (!prefix) {
    next()
    return
  }
  const rel = decodeURIComponent(raw.slice(prefix.length))
  if (rel.includes('..')) {
    res.statusCode = 400
    res.end('Invalid path')
    return
  }
  const file = path.join(outDir, rel)
  if (!file.startsWith(outDir) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    next()
    return
  }
  res.setHeader('Content-Type', rel.endsWith('.json') ? 'application/json' : 'text/plain; charset=utf-8')
  res.setHeader('Cache-Control', 'no-cache')
  fs.createReadStream(file).pipe(res)
}

export function echoRuntimePlugin(): Plugin {
  return {
    name: 'echo-runtime',
    buildStart() {
      const files = copyEchoRuntime()
      this.info(`copied ${files.length} Echo runtime files for the playground`)
    },
    configureServer(server) {
      copyEchoRuntime()
      server.middlewares.use((req, res, next) => {
        sendRuntimeFile(req.url, res, next)
      })
    },
  }
}
