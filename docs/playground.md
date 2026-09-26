---
layout: page
sidebar: false
aside: false
title: Playground
description: Write and run Echo in the browser
---

The browser playground uses a **restricted host**: no filesystem, no process launch, and no HTTP. Denied builtins abort with **E2801**. Environment variables are empty (`env` aborts; use `envOr`). The CLI defaults to allowing files, `run`, and HTTP — see [Host builtins](/standard-library/built-in-methods#host) and the [failure model](/failure-model).

URL helpers (`urlEncode`, …) and status checks (`httpOk`, `httpRedirect`) still work; live `httpGet` / `httpPost` do not.

<Playground />
