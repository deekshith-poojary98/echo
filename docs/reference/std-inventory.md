---
title: Std Inventory
description: Auto-generated list of Echo install-tree std/… modules
---

# Std Inventory

Auto-generated from the install-tree `std/` modules by `tools/sync_builtins.py`.
Do not edit by hand — run `python tools/sync_builtins.py` after adding a std module.

CLI: `elang std` / `elang std --exports`. Module semantics: [Modules](/module-semantics).
Prelude builtins: [Builtin Inventory](/reference/builtin-inventory).


**Modules:** 12

| Module | Exports |
| --- | --- |
| `std/base64` | `base64Decode`, `base64Encode` |
| `std/fs` | `copyFile`, `cwd`, `fileExists`, `isDir`, `listFiles`, `mkdir`, `mkdirAll`, `pathJoin`, `readFile`, `readFileOr`, `removeFile`, `removeTree`, `writeFile` |
| `std/http` | `httpGet`, `httpGetOr`, `httpOk`, `httpPost`, `httpPostOr`, `httpRedirect` |
| `std/json` | `parseJson`, `parseJsonOr`, `writeJson` |
| `std/math` | `abs`, `ceil`, `floor`, `max`, `min` |
| `std/meta` | `stdName`, `stdOk` |
| `std/os` | `args`, `env`, `envOr`, `run` |
| `std/random` | `random`, `randomInt` |
| `std/re` | `regexFind`, `regexMatch`, `regexReplace`, `regexSplit` |
| `std/time` | `days`, `formatTime`, `hours`, `minutes`, `now`, `parseTime`, `wait` |
| `std/url` | `urlDecode`, `urlEncode`, `urlJoin`, `urlQuery` |
| `std/yaml` | `yamlParse`, `yamlParseOr`, `yamlWrite` |
