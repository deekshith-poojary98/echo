Here’s the useful split: **nice-to-have missing** vs **big / by-design holds**.

**0.9.x ergonomics series is open through 0.9.9.**

### 0.9.x
- **0.9.0** — Compound assign on members (`this.x += 1`) — **done**
- **0.9.1** — `priv` / visibility — **done**
- **0.9.2** — Positional construction `Point(3, 4)` — **done**
- **0.9.3** — Deep `clone()` — **done**
- **0.9.4** — Named `format()` placeholders — **done**
- **0.9.5** — Class properties `get` / `set` — **done**
- **0.9.6** — `mkdirAll` / `removeTree` — **done**
- **0.9.7** — Regex builtins — **done**
- **0.9.8** — Union narrowing in `if type(...)` — **drafted**
- **0.9.9** — Thin dates builtins — **drafted**

### Still nice later (not in 0.9.6–0.9.9)
- **HTTP** builtins (host/playground policy — held)
- **Packages** (share modules beyond single-repo `import`)
- **`Point.new` factory spelling** (held; positional call form shipped instead)
- **Deeper tooling**: real **LSP**, better debugger than `watch`
- **Doc generator**, tighter error messages / codes polish (ongoing, not a version slice)

### Missing but not “nice soon” (big or intentional)
- Generics, async, VM/JIT, compiler  
- `try`/`catch`, `Result`/`Option` (failure model is frozen around abort + `*Or`)  
- Inheritance, abstract classes, overloading, nested classes  

### Bottom line
**0.9.7** ships regex builtins. Next: union narrowing (**0.9.8**).
