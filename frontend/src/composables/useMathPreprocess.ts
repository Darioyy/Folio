// Protect math expressions from Turndown processing by replacing them with
// placeholder tokens, then restoring after conversion.

interface MathEntry {
  display: boolean
  latex: string
}

// Unescape chars Turndown adds backslashes before, to restore original LaTeX.
function unescapeMarkdown(s: string): string {
  return s.replace(/\\([\\*_{}[\]()#!.+\-~|`])/g, '$1')
}

/** Try multiple strategies to extract LaTeX source from an .arithmatex element. */
function extractLatex(node: Element): { latex: string; display: boolean } | null {
  let m: RegExpMatchArray | null

  // ── Strategy 0: KaTeX annotation element (always authoritative) ─────────
  // KaTeX stores the original LaTeX in <annotation encoding="application/x-tex">.
  const annotation = node.querySelector('annotation[encoding="application/x-tex"]')
  if (annotation) {
    const latex = annotation.textContent?.trim() ?? ''
    if (latex) {
      const isDisplay =
        node.tagName === 'DIV' ||
        !!node.querySelector('.katex-display, math[display="block"]')
      return { latex, display: isDisplay }
    }
  }

  // ── Strategy 1: textContent contains \[...\] or \(...\) ─────────────────
  const text = node.textContent ?? ''
  m = text.match(/\\\[(.+?)\\\]/s)
  if (m) return { latex: m[1].trim(), display: true }
  m = text.match(/\\\((.+?)\\\)/s)
  if (m) return { latex: m[1].trim(), display: false }

  // ── Strategy 2: scan individual text nodes, score by LaTeX syntax ────────
  // Score: \cmd sequences (3 pts), _ or ^ (2 pts), {} (1 pt).
  const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT)
  let best: { text: string; score: number } = { text: '', score: 0 }
  let cur: Node | null
  while ((cur = walker.nextNode())) {
    const t = (cur as Text).data.trim()
    if (!t) continue
    m = t.match(/\\\[(.+?)\\\]/s)
    if (m) return { latex: m[1].trim(), display: true }
    m = t.match(/\\\((.+?)\\\)/s)
    if (m) return { latex: m[1].trim(), display: false }
    const score =
      ((t.match(/\\[a-zA-Z]+/g) ?? []).length * 3) +
      ((t.match(/[_^]/g) ?? []).length * 2) +
      ((t.match(/[{}]/g) ?? []).length)
    if (score > best.score) best = { text: t, score }
  }
  if (best.score >= 2) return { latex: best.text, display: node.tagName === 'DIV' }

  // ── Strategy 3: strip rendered math containers, recheck remaining text ───
  const clone = node.cloneNode(true) as Element
  clone
    .querySelectorAll('mjx-container, mjx-assistive-mml, svg, [class*="MathJax"], [class*="mathjax"]')
    .forEach(e => e.remove())
  const rest = (clone.textContent ?? '').trim()
  if (rest) {
    m = rest.match(/\\\[(.+?)\\\]/s)
    if (m) return { latex: m[1].trim(), display: true }
    m = rest.match(/\\\((.+?)\\\)/s)
    if (m) return { latex: m[1].trim(), display: false }
  }

  return null
}

export function preprocessMath(el: Element): Map<string, MathEntry> {
  const map = new Map<string, MathEntry>()
  let n = 0

  // Placeholder must use only alphanumeric chars: Turndown escapes underscores
  // (_→\_) in text, breaking the split(key) lookup in restoreMath.
  const makeKey = () => `ARITHMATEXPH${n++}END`

  // ── Pass 1: .arithmatex elements (pymdownx / MkDocs-Material) ────────────
  el.querySelectorAll('.arithmatex').forEach(node => {
    if (!el.contains(node)) return   // already replaced (nested edge case)
    const extracted = extractLatex(node)
    if (!extracted) { node.remove(); return }   // prevent garbage Markdown output

    const key = makeKey()
    // Treat as display if: DIV, explicit \[...\], multiline content, or alignment (&)
    const isDisplay = extracted.display || node.tagName === 'DIV' ||
      extracted.latex.includes('\n') || extracted.latex.includes('&') ||
      /\\begin\s*\{/.test(extracted.latex)
    map.set(key, { display: isDisplay, latex: extracted.latex })

    if (isDisplay) {
      const p = document.createElement('p')
      p.textContent = key
      node.replaceWith(p)
    } else {
      node.replaceWith(document.createTextNode(key))
    }
  })

  // ── Pass 2: bare <mjx-container> (MathJax 3 pages without .arithmatex) ───
  el.querySelectorAll('mjx-container').forEach(node => {
    if (!el.contains(node)) return
    const ann = node.querySelector('annotation[encoding="application/x-tex"]')
    const latex = ann?.textContent?.trim() || node.getAttribute('data-latex') || ''
    if (!latex) { node.remove(); return }
    const isDisplay =
      !!node.querySelector('math[display="block"]') ||
      node.getAttribute('display') === 'block'
    const key = makeKey()
    map.set(key, { display: isDisplay, latex })
    if (isDisplay) {
      const p = document.createElement('p')
      p.textContent = key
      node.replaceWith(p)
    } else {
      node.replaceWith(document.createTextNode(key))
    }
  })

  return map
}

export function restoreMath(md: string, map: Map<string, MathEntry>): string {
  for (const [key, { display, latex }] of map) {
    if (display) md = md.split(key).join(`\n\n$$\n${latex}\n$$\n\n`)
    else md = md.split(key).join(`$${latex}$`)
  }
  // Catch \(...\) without .arithmatex; unescape Turndown-mangled content.
  // \[...\] skipped: Turndown also escapes [text]→\[text\] causing false positives.
  md = md.replace(/\\{1,2}\((.+?)\\{1,2}\)/gs, (_, l) => `$${unescapeMarkdown(l).trim()}$`)
  // Promote multiline $\n...\n$ (display math with wrong delimiters) to $$...$$.
  // Also unescapes \\cmd→\cmd and \_→_ that Turndown added to pass-through math.
  md = md.replace(/(?<!\$)\$\n([\s\S]+?)\n\$(?!\$)/g, (_, c) =>
    `\n\n$$\n${unescapeMarkdown(c.trim())}\n$$\n\n`)
  // Unescape Turndown escapes inside remaining single-line $...$ blocks.
  md = md.replace(/(?<!\$)\$((?:[^$\n]|\\.)+?)\$(?!\$)/g, (_, c) => `$${unescapeMarkdown(c)}$`)
  return md
}
