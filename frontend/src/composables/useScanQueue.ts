import { ref, computed } from 'vue'
import { usePdfRenderer } from './usePdfRenderer'

export interface ScanPage {
  id: string
  name: string
  thumbnailDataUrl: string      // low-res, for the strip
  originalDataUrl: string       // full-res source image
  processedDataUrl: string | null
  // PDF source — pixels rendered on demand at export DPI
  pdfSource: { bytes: ArrayBuffer; pageNum: number } | null
  status: 'pending' | 'processing' | 'done' | 'error'
  errorMsg: string | null
}

let seq = 0

export function useScanQueue() {
  const pages = ref<ScanPage[]>([])
  const currentIndex = ref(0)
  const { renderToThumbs, renderPageToPixels } = usePdfRenderer()

  const currentPage = computed(() => pages.value[currentIndex.value] ?? null)
  const doneCount = computed(() => pages.value.filter(p => p.status === 'done').length)

  async function addImages(files: File[]): Promise<void> {
    for (const file of files) {
      const dataUrl = await fileToDataUrl(file)
      pages.value.push({
        id: `s${seq++}`, name: file.name,
        thumbnailDataUrl: dataUrl, originalDataUrl: dataUrl,
        processedDataUrl: null, pdfSource: null,
        status: 'pending', errorMsg: null,
      })
    }
    if (pages.value.length === files.length) currentIndex.value = 0
  }

  async function addPdf(file: File): Promise<void> {
    const buf = await file.arrayBuffer()
    // Keep an independent copy for later per-page rendering.
    // renderToThumbs (pdfjs) will transfer buf to its worker via postMessage,
    // detaching it — storedBuf is a separate allocation that survives unaffected.
    const storedBuf = buf.slice(0)
    const thumbs = await renderToThumbs(buf, 0.3)
    for (const thumb of thumbs) {
      pages.value.push({
        id: `s${seq++}`, name: `${file.name} — P${thumb.pageNum}`,
        thumbnailDataUrl: thumb.dataUrl, originalDataUrl: thumb.dataUrl,
        processedDataUrl: null,
        pdfSource: { bytes: storedBuf, pageNum: thumb.pageNum },
        status: 'pending', errorMsg: null,
      })
    }
    if (pages.value.length > 0 && currentIndex.value === 0) currentIndex.value = 0
  }

  async function renderPdfPageAtDpi(page: ScanPage, dpi: number): Promise<string> {
    if (!page.pdfSource) return page.originalDataUrl
    const scale = dpi / 72
    const { data, width, height } = await renderPageToPixels(page.pdfSource.bytes, page.pdfSource.pageNum, scale)
    const canvas = document.createElement('canvas')
    canvas.width = width; canvas.height = height
    canvas.getContext('2d')!.putImageData(new ImageData(data, width, height), 0, 0)
    return canvas.toDataURL('image/jpeg', 0.9)
  }

  function removePage(id: string): void {
    const idx = pages.value.findIndex(p => p.id === id)
    if (idx < 0) return
    pages.value.splice(idx, 1)
    if (currentIndex.value >= pages.value.length) {
      currentIndex.value = Math.max(0, pages.value.length - 1)
    }
  }

  function clear(): void { pages.value = []; currentIndex.value = 0 }

  function selectPage(idx: number): void { currentIndex.value = idx }

  return { pages, currentIndex, currentPage, doneCount, addImages, addPdf, renderPdfPageAtDpi, removePage, clear, selectPage }
}

function fileToDataUrl(file: File | Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
