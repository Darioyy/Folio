import { ref, computed } from 'vue'
import TurndownService from 'turndown'
import { gfm } from 'turndown-plugin-gfm'
import { cleanArticle, preprocessDOM } from './useHtmlDomPreprocess'
import { preprocessMath, restoreMath } from './useMathPreprocess'
import {
  downloadImages, buildZip, triggerDownload,
  PROXIES, buildFileMap,
  type ImageResult,
} from './useImageDownloader'
import JSZip from 'jszip'

export interface ConversionEntry {
  id: string
  name: string
  status: 'processing' | 'done' | 'error'
  statusText: string
  md: string | null
  images: ImageResult[]
  lines: number
  imgCount: number
  imgFailed: number
  error: string | null
}

// Module-level TurndownService (shared, stateless between conversions)
const td = new TurndownService({
  headingStyle: 'atx',
  hr: '---',
  bulletListMarker: '-',
  codeBlockStyle: 'fenced',
  fence: '```',
})
td.use(gfm)
td.remove(['script', 'style', 'noscript', 'iframe', 'header', 'nav', 'footer'])

let idSeq = 0

export function useHtmlConverter() {
  const entries = ref<Map<string, ConversionEntry>>(new Map())
  const downloadImagesEnabled = ref(true)

  const entriesList = computed(() => [...entries.value.values()].reverse())
  const doneCount = computed(() =>
    [...entries.value.values()].filter(e => e.status === 'done').length,
  )

  function tick(): Promise<void> {
    return new Promise(r => setTimeout(r, 0))
  }

  function setEntry(id: string, update: Partial<ConversionEntry>): void {
    const current = entries.value.get(id)
    if (!current) return
    entries.value = new Map(entries.value).set(id, { ...current, ...update })
  }

  async function convert(
    html: string,
    name: string,
    baseUrl: string | null,
    fileMap: Map<string, File>,
  ): Promise<void> {
    const id = `f${idSeq++}`
    entries.value = new Map(entries.value).set(id, {
      id, name, status: 'processing', statusText: '解析页面…',
      md: null, images: [], lines: 0, imgCount: 0, imgFailed: 0, error: null,
    })
    await tick()

    try {
      const doc = new DOMParser().parseFromString(html, 'text/html')
      // base[href] 是浏览器解析相对 URL 的标准依据，优先级最高；
      // 用户手动输入的 baseUrl 是 base[href] 的 fallback；
      // canonical 是 SEO 规范 URL，不影响相对路径解析，优先级较低。
      const resolvedBase =
        doc.querySelector('base[href]')?.getAttribute('href') ||
        baseUrl ||
        doc.querySelector('link[rel="canonical"]')?.getAttribute('href') ||
        doc.querySelector('meta[property="og:url"]')?.getAttribute('content') ||
        null

      const article = (
        doc.querySelector('article.md-content__inner') ||
        doc.querySelector('[class*="md-content__inner"]') ||
        doc.querySelector('.md-content') ||
        doc.querySelector('main article') ||
        doc.querySelector('main') ||
        doc.querySelector('article') ||
        doc.body
      ) as Element

      const clone = article.cloneNode(true) as Element
      cleanArticle(clone)
      // preprocessDOM 先于图片下载执行：清理装饰性元素、规范化代码块后，
      // 只下载最终会出现在 Markdown 中的图片，避免无效下载和 imgCount 虚高。
      preprocessDOM(clone)

      if (downloadImagesEnabled.value) {
        setEntry(id, { statusText: '下载图片中…' })
        await tick()
        const results = await downloadImages(clone, resolvedBase, Date.now(), fileMap)
        const ok = results.filter((r): r is ImageResult => r.ok)
        setEntry(id, { images: ok, imgCount: ok.length, imgFailed: results.filter(r => !r.ok).length })
      } else {
        clone.querySelectorAll('img').forEach(img => img.remove())
      }

      setEntry(id, { statusText: '生成 Markdown…' })
      await tick()

      const placeholders = preprocessMath(clone)
      let md = td.turndown(clone.innerHTML)
      md = restoreMath(md, placeholders)
      md = md.replace(/\n{4,}/g, '\n\n\n').trim()

      setEntry(id, { md, lines: md.split('\n').length, status: 'done' })
    } catch (err) {
      setEntry(id, { status: 'error', error: (err as Error).message || '转换失败' })
    }
  }

  async function convertFromUrl(rawUrl: string): Promise<void> {
    let url: URL
    try { url = new URL(rawUrl.startsWith('http') ? rawUrl : 'https://' + rawUrl) }
    catch { throw new Error('请输入有效的网址') }

    let html: string
    let finalUrl = url.href

    // 1st try: backend proxy (no CORS, sends real browser UA)
    let backendResp: Response | null = null
    try {
      backendResp = await fetch(`/api/v1/tools/proxy?url=${encodeURIComponent(url.href)}`)
    } catch {
      // backend unreachable — fall through to CORS proxy
    }

    if (backendResp?.ok) {
      const data = await backendResp.json()
      if (data.success) {
        html = data.data.content
        finalUrl = data.data.url || url.href
      } else {
        throw new Error(data.error?.message || '代理请求失败')
      }
    } else {
      // Backend failed or target returned error.
      // For 403/429: our server IP may be blocked — a different proxy IP might succeed.
      // For 404/401/400: content is definitively inaccessible — skip fallback.
      const errData = backendResp ? await backendResp.json().catch(() => null) : null
      const backendStatus = backendResp?.status ?? 0
      const errCode = errData?.error?.code ?? ''
      // Only skip fallback when the TARGET page is definitively inaccessible (HTTP_ERROR from proxy).
      // NOT_FOUND means our own route doesn't exist yet — still try CORS proxy.
      const skipFallback = errCode === 'HTTP_ERROR' && (backendStatus === 404 || backendStatus === 401)
      if (skipFallback) {
        throw new Error(errData?.error?.message || `目标网站返回 HTTP ${backendStatus}`)
      }
      // 2nd try: public CORS proxy (different IP, may bypass IP-based blocks like Cloudflare)
      const fallbackResp = await fetch(PROXIES[0](url.href)).catch(() => null)
      if (!fallbackResp?.ok) {
        throw new Error(errData?.error?.message || `无法抓取该页面（HTTP ${fallbackResp?.status ?? '网络错误'}）`)
      }
      html = await fallbackResp.text()
    }

    const finalUrlObj = new URL(finalUrl)
    const parts = finalUrlObj.pathname.replace(/\/$/, '').split('/').filter(Boolean)
    await convert(html, parts.length ? parts[parts.length - 1] : finalUrlObj.hostname, finalUrl, new Map())
  }

  async function downloadOne(id: string): Promise<void> {
    const e = entries.value.get(id)
    if (!e || e.status !== 'done' || !e.md) return
    if (downloadImagesEnabled.value && e.images.length > 0) {
      triggerDownload(await buildZip(e.name, e.md, e.images), `${e.name}.zip`)
    } else {
      triggerDownload(new Blob([e.md], { type: 'text/markdown;charset=utf-8' }), `${e.name}.md`)
    }
  }

  async function downloadAll(): Promise<void> {
    const done = [...entries.value.entries()].filter(([, e]) => e.status === 'done')
    if (!done.length) return
    if (done.length === 1) { await downloadOne(done[0][0]); return }

    const zip = new JSZip()
    for (const [, e] of done) {
      if (!e.md) continue
      if (downloadImagesEnabled.value && e.images.length > 0) {
        // 每个文件独立子目录，避免不同文件间的 images/ 文件名碰撞
        const folder = zip.folder(e.name)!
        folder.file(`${e.name}.md`, e.md)
        const imgFolder = folder.folder('images')!
        for (const { filename, data } of e.images) imgFolder.file(filename, data)
      } else {
        zip.file(`${e.name}.md`, e.md)
      }
    }
    triggerDownload(await zip.generateAsync({ type: 'blob' }), 'folio-export.zip')
  }

  function clearAll(): void {
    entries.value = new Map()
  }

  return {
    entries,
    entriesList,
    doneCount,
    downloadImagesEnabled,
    convert,
    convertFromUrl,
    downloadOne,
    downloadAll,
    clearAll,
    buildFileMap,
  }
}
