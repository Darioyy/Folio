// DOM preprocessing utilities for HTML → Markdown conversion.
// Handles MkDocs-Material, admonitions, code blocks, tabbed sets, etc.

function esc(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

// Step 1: Remove noise elements (nav, scripts, sidebars, comments section…)
export function cleanArticle(el: Element): void {
  const rm = (sel: string) => el.querySelectorAll(sel).forEach(e => e.remove())
  rm([
    '.md-content__button', '.md-source-file',
    '.md-nav', '.md-header', '.md-footer', '.md-sidebar', '.md-tabs', '.md-top', '.md-banner',
    '[style*="margin-top: -30px"]',
    'script', 'style', 'noscript', 'iframe', 'header', 'nav', 'footer',
    '[id*="giscus"]', '.giscus', '[class*="giscus"]',
    '[data-md-component="search"]',
    // 常见评论区容器（用 id/class 精确匹配，避免误删正文中提到"评论区"的段落）
    '#comments', '#comment-section', '#disqus_thread', '.disqus',
    '[class*="comment-section"]', '[id*="comment-list"]',
  ].join(','))
}

// Step 3: Convert widgets to simple HTML that Turndown understands
export function preprocessDOM(el: Element): void {
  const rm = (sel: string) => el.querySelectorAll(sel).forEach(e => e.remove())
  const unwrap = (sel: string) =>
    el.querySelectorAll(sel).forEach(e => e.replaceWith(...e.childNodes))

  // 1. Remove decorative / UI chrome
  rm([
    '.headerlink', '.md-clipboard', '.md-annotation', '.md-annotation__index',
    '.twemoji', '.footnote-backref',
    'input[type="radio"]', 'input[type="checkbox"][id^="tabbed"]',
    '[aria-label="Skip to content"]',
  ].join(','))

  // 2. Unwrap invisible typography wrappers (heti.js, GLightbox)
  unwrap('heti-adjacent, [class*="heti-"]')
  el.querySelectorAll('a.glightbox, a[data-type="image"]').forEach(a => {
    a.replaceWith(...a.childNodes)
  })

  // 3. Code blocks — strip line-number tables, normalize to clean <pre><code>
  el.querySelectorAll('table.highlighttable').forEach(table => {
    if (!el.contains(table)) return
    const codeCell = table.querySelector('td.code > div') || table.querySelector('td.code')
    if (codeCell) table.replaceWith(...codeCell.childNodes)
    else table.remove()
  })

  el.querySelectorAll('div.highlight, div[class*="language-"]').forEach(div => {
    if (!el.contains(div)) return
    const pre = div.querySelector('pre')
    if (!pre) return
    const codeEl = pre.querySelector('code') || pre
    const classStr = (div.getAttribute('class') || '') + ' ' + (codeEl.getAttribute('class') || '')
    const langMatch = classStr.match(/language-(\w+)/)
    const lang = langMatch ? langMatch[1] : ''
    const filenameEl = div.querySelector('.filename, [class*="filename"], .code-block-filename')
    if (filenameEl) {
      const p = document.createElement('p')
      p.innerHTML = `<em>📄 ${esc(filenameEl.textContent?.trim() || '')}</em>`
      div.before(p)
    }
    const newPre = document.createElement('pre')
    const newCode = document.createElement('code')
    newCode.className = lang ? `language-${lang}` : ''
    newCode.textContent = (codeEl.textContent || '').replace(/\n$/, '')
    newPre.appendChild(newCode)
    div.replaceWith(newPre)
  })

  // 4. Admonitions → <blockquote>
  el.querySelectorAll('.admonition, .alert, .callout').forEach(adm => {
    if (!el.contains(adm)) return
    const titleEl = adm.querySelector('.admonition-title, .alert-heading, .callout-title')
    const title = titleEl?.textContent?.trim() || 'Note'
    titleEl?.remove()
    const bq = document.createElement('blockquote')
    const header = document.createElement('p')
    header.innerHTML = `<strong>${esc(title)}</strong>`
    bq.appendChild(header)
    while (adm.firstChild) bq.appendChild(adm.firstChild)
    adm.replaceWith(bq)
  })

  // 5. <details>/<summary> → <blockquote>
  el.querySelectorAll('details').forEach(details => {
    if (!el.contains(details)) return
    const summary = details.querySelector(':scope > summary')
    const title = summary?.textContent?.trim() || 'Details'
    summary?.remove()
    const bq = document.createElement('blockquote')
    const header = document.createElement('p')
    header.innerHTML = `<strong>${esc(title)}</strong>`
    bq.appendChild(header)
    while (details.firstChild) bq.appendChild(details.firstChild)
    details.replaceWith(bq)
  })

  // 6. Tabbed sets → sections with <h4>
  el.querySelectorAll('.tabbed-set').forEach(tabSet => {
    if (!el.contains(tabSet)) return
    const labels = [...tabSet.querySelectorAll('.tabbed-labels > label')]
    const blocks = [...tabSet.querySelectorAll('.tabbed-content .tabbed-block')]
    const container = document.createElement('div')
    blocks.forEach((block, i) => {
      const h = document.createElement('h4')
      h.textContent = labels[i]?.textContent?.trim() || `Tab ${i + 1}`
      container.appendChild(h)
      while (block.firstChild) container.appendChild(block.firstChild)
    })
    tabSet.replaceWith(container)
  })

  // 7. Definition lists → bold term + paragraph
  el.querySelectorAll('dl').forEach(dl => {
    if (!el.contains(dl)) return
    const frag = document.createDocumentFragment()
    for (const child of [...dl.children]) {
      if (child.tagName === 'DT') {
        const p = document.createElement('p')
        const strong = document.createElement('strong')
        while (child.firstChild) strong.appendChild(child.firstChild)
        p.appendChild(strong)
        frag.appendChild(p)
      } else if (child.tagName === 'DD') {
        const p = document.createElement('p')
        while (child.firstChild) p.appendChild(child.firstChild)
        frag.appendChild(p)
      }
    }
    dl.replaceWith(frag)
  })

  // 8. <figure> → unwrap (caption → img alt)
  el.querySelectorAll('figure').forEach(fig => {
    if (!el.contains(fig)) return
    const img = fig.querySelector('img')
    const caption = fig.querySelector('figcaption')
    if (img && caption && !img.getAttribute('alt'))
      img.setAttribute('alt', caption.textContent?.trim() || '')
    caption?.remove()
    while (fig.firstChild) fig.before(fig.firstChild)
    fig.remove()
  })

  // 9. Inline element fixes
  el.querySelectorAll('kbd').forEach(kbd => {
    const code = document.createElement('code')
    code.textContent = kbd.textContent
    kbd.replaceWith(code)
  })
  el.querySelectorAll('mark').forEach(mark => {
    const frag = document.createDocumentFragment()
    frag.appendChild(document.createTextNode('=='))
    while (mark.firstChild) frag.appendChild(mark.firstChild)
    frag.appendChild(document.createTextNode('=='))
    mark.replaceWith(frag)
  })

  // 10. Remove empty block wrappers
  el.querySelectorAll('p, div').forEach(e => {
    if (el.contains(e) && !e.children.length && !e.textContent?.trim()) e.remove()
  })
}
