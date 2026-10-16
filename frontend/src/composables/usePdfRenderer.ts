import { ref } from 'vue'
import { getDocument, GlobalWorkerOptions, version as pdfjsVersion } from 'pdfjs-dist'

// 使用 CDN 避免因服务器未配置 .mjs MIME 类型而导致 worker 加载失败。
// nginx 已同步修复（location ~* \.mjs$），CDN 作为双保险。
GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsVersion}/build/pdf.worker.min.mjs`

export interface RenderedPage {
  pageNum: number
  dataUrl: string
  aspectRatio: number
}

export function usePdfRenderer() {
  const rendering = ref(false)

  async function renderToThumbs(bytes: ArrayBuffer, scale = 0.3): Promise<RenderedPage[]> {
    rendering.value = true
    const pages: RenderedPage[] = []
    try {
      // slice(0) creates an independent copy so pdfjs can transfer it to its worker
      // without detaching the caller's buffer reference
      const pdf = await getDocument({ data: new Uint8Array(bytes.slice(0)) }).promise
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i)
        const viewport = page.getViewport({ scale })
        const canvas = document.createElement('canvas')
        canvas.width = viewport.width
        canvas.height = viewport.height
        const ctx = canvas.getContext('2d')!
        await page.render({ canvasContext: ctx as unknown as CanvasRenderingContext2D, viewport }).promise
        pages.push({
          pageNum: i,
          dataUrl: canvas.toDataURL('image/jpeg', 0.8),
          aspectRatio: viewport.height / viewport.width,
        })
        page.cleanup()
      }
      pdf.destroy()
    } finally {
      rendering.value = false
    }
    return pages
  }

  async function renderPageToPixels(
    bytes: ArrayBuffer,
    pageNum: number,
    scale: number,
  ): Promise<{ data: Uint8ClampedArray; width: number; height: number }> {
    const pdf = await getDocument({ data: new Uint8Array(bytes.slice(0)) }).promise
    const page = await pdf.getPage(pageNum)
    const viewport = page.getViewport({ scale })
    const canvas = document.createElement('canvas')
    canvas.width = viewport.width
    canvas.height = viewport.height
    const ctx = canvas.getContext('2d')!
    await page.render({ canvasContext: ctx as unknown as CanvasRenderingContext2D, viewport }).promise
    const imgData = ctx.getImageData(0, 0, viewport.width, viewport.height)
    page.cleanup()
    pdf.destroy()
    return { data: imgData.data, width: viewport.width, height: viewport.height }
  }

  async function getPdfPageCount(bytes: ArrayBuffer): Promise<number> {
    const pdf = await getDocument({ data: new Uint8Array(bytes.slice(0)) }).promise
    const count = pdf.numPages
    pdf.destroy()
    return count
  }

  return { rendering, renderToThumbs, renderPageToPixels, getPdfPageCount }
}
