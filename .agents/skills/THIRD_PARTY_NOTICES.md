# Third-party skills — provenance and licences

This directory contains both first-party skills and vendored third-party skills.
Vendored content is listed here together with its upstream source and licence.
Do not edit vendored files in place; re-import from upstream and re-apply any
local adaptation instead, so the diff against upstream stays reviewable.

## First-party (maintained in this repository)

| Skill | Purpose |
|---|---|
| `character-design-sheet` | Character sheet / turnaround generation |
| `google-flow` | Google Flow + Veo 3.1 browser automation |
| `playwright-cli` | Playwright CLI driving for UI verification |
| `script-writer` | Scenario Director / screenplay writing |
| `storyboard-manager` | Storyboard breakdown and shot ordering |

## Vendored — `drama-skills`

- **Upstream:** https://github.com/zenstory-ai/drama-skills
- **Version:** 0.10.0 (`VERSION` at import time)
- **Imported:** 2026-10-30
- **Scope:** all eleven `skills/*` directories, imported unmodified
- **Licence:** MIT

Imported skill directories: `short-drama`, `short-drama-assets`,
`short-drama-develop`, `short-drama-edit`, `short-drama-image-prompts`,
`short-drama-novel-analyze`, `short-drama-produce`, `short-drama-review`,
`short-drama-storyboard`, `short-drama-video-prompts`, `short-drama-write`.

The vendored skills are authoring guidance for the coding agent: they shape how
scenario, character-asset, storyboard and review documents are written. They are
**not** wired into the FastAPI pipelines at runtime. The parts that run inside the
web application are reimplemented first-party; see the `Prompt-Port` work on
`core/screenwriter/scenario_director.py`.

`short-drama-produce/scripts/provider_adapters.py` talks to external media
providers and is unused here — this project generates through its own
`core/api/*` clients and `core/api/google_flow_engine.py`.

### Licence text

```
MIT License

Copyright (c) 2026 drama-skills contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
