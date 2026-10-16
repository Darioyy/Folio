import { ref, computed } from 'vue'
import { PDFDocument, degrees, rgb, StandardFonts } from 'pdf-lib'
import { usePdfRenderer } from './usePdfRenderer'

export interface PageEntry {
  id: string
  docIndex: number
  originalIndex: number
  rotation: number        // 0, 90, 180, 270
  thumbnail: string | null
  aspectRatio: number
  selected: boolean
}

export interface WatermarkOptions {
  type: 'text' | 'image'
  text?: string
  fontSizePt?: number
  color?: string          // hex e.g. '#d1d5db'
  opacity?: number
  angleDeg?: number
  imageBytes?: Uint8Array
}

let seq = 0

export function usePdfEditor() {
  const sourceBytesList = ref<Uint8Array[]>([])
  const pages = ref<PageEntry[]>([])
  const fileName = ref('')
  const isLoading = ref(false)
  const isExporting = ref(false)
  const { rendering, renderToThumbs } = usePdfRenderer()

  const hasPages = computed(() => pages.value.length > 0)
  const selectedCount = computed(() => pages.value.filter(p => p.selected).length)

  async function loadFile(file: File): Promise<void> {
    isLoading.value = true
    try {
      const buf = await file.arrayBuffer()
      // Store an independent copy — pdfjs will transfer/detach buf via postMessage,
      // so we must slice before passing to renderToThumbs to keep our stored bytes intact.
      sourceBytesList.value = [new Uint8Array(buf.slice(0))]
      fileName.value = file.name.replace(/\.pdf$/i, '')
      const thumbs = await renderToThumbs(buf)
      pages.value = thumbs.map(t => ({
        id: `p${seq++}`, docIndex: 0, originalIndex: t.pageNum - 1,
        rotation: 0, thumbnail: t.dataUrl, aspectRatio: t.aspectRatio, selected: false,
      }))
    } finally {
      isLoading.value = false
    }
  }

  async function mergeFile(file: File): Promise<void> {
    const buf = await file.arrayBuffer()
    const docIndex = sourceBytesList.value.length
    // Same pattern: store independent copy, pass original to renderer
    sourceBytesList.value = [...sourceBytesList.value, new Uint8Array(buf.slice(0))]
    const thumbs = await renderToThumbs(buf)
    pages.value = [
      ...pages.value,
      ...thumbs.map(t => ({
        id: `p${seq++}`, docIndex, originalIndex: t.pageNum - 1,
        rotation: 0, thumbnail: t.dataUrl, aspectRatio: t.aspectRatio, selected: false,
      })),
    ]
  }

  function toggleSelect(id: string): void {
    const p = pages.value.find(x => x.id === id)
    if (p) p.selected = !p.selected
  }

  function selectAll(): void { pages.value.forEach(p => { p.selected = true }) }
  function deselectAll(): void { pages.value.forEach(p => { p.selected = false }) }

  function deleteSelected(): void {
    pages.value = pages.value.filter(p => !p.selected)
  }

  function rotatePage(id: string, delta: 90 | -90): void {
    const p = pages.value.find(x => x.id === id)
    if (p) p.rotation = ((p.rotation + delta) % 360 + 360) % 360
  }

  function reorderPage(fromId: string, toId: string): void {
    const arr = [...pages.value]
    const fi = arr.findIndex(p => p.id === fromId)
    const ti = arr.findIndex(p => p.id === toId)
    if (fi < 0 || ti < 0 || fi === ti) return
    const [item] = arr.splice(fi, 1)
    arr.splice(ti, 0, item)
    pages.value = arr
  }

  async function splitSelected(): Promise<void> {
    const selected = pages.value.filter(p => p.selected)
    if (!selected.length) return
    isExporting.value = true
    try {
      const srcDocs = await Promise.all(sourceBytesList.value.map(b => PDFDocument.load(b)))
      const newDoc = await PDFDocument.create()
      for (const p of selected) {
        const [copied] = await newDoc.copyPages(srcDocs[p.docIndex], [p.originalIndex])
        const added = newDoc.addPage(copied)
        if (p.rotation) added.setRotation(degrees((added.getRotation().angle + p.rotation) % 360))
      }
      triggerDownload(await newDoc.save(), `${fileName.value}-split.pdf`)
    } finally {
      isExporting.value = false
    }
  }

  async function exportPdf(watermark?: WatermarkOptions): Promise<void> {
    isExporting.value = true
    try {
      const srcDocs = await Promise.all(sourceBytesList.value.map(b => PDFDocument.load(b)))
      const newDoc = await PDFDocument.create()
      for (const p of pages.value) {
        const [copied] = await newDoc.copyPages(srcDocs[p.docIndex], [p.originalIndex])
        const added = newDoc.addPage(copied)
        if (p.rotation) added.setRotation(degrees((added.getRotation().angle + p.rotation) % 360))
      }
      if (watermark) await applyWatermark(newDoc, watermark)
      triggerDownload(await newDoc.save(), `${fileName.value || 'document'}.pdf`)
    } finally {
      isExporting.value = false
    }
  }

  function reset(): void {
    sourceBytesList.value = []
    pages.value = []
    fileName.value = ''
  }

  return {
    pages, fileName, isLoading, isExporting, rendering, hasPages, selectedCount,
    loadFile, mergeFile, toggleSelect, selectAll, deselectAll,
    deleteSelected, rotatePage, reorderPage, splitSelected, exportPdf, reset,
  }
}

async function applyWatermark(doc: PDFDocument, opt: WatermarkOptions): Promise<void> {
  const docPages = doc.getPages()
  if (opt.type === 'text' && opt.text) {
    const font = await doc.embedFont(StandardFonts.HelveticaBold)
    const hex = opt.color || '#d1d5db'
    const r = parseInt(hex.slice(1, 3), 16) / 255
    const g = parseInt(hex.slice(3, 5), 16) / 255
    const b = parseInt(hex.slice(5, 7), 16) / 255
    for (const page of docPages) {
      const { width, height } = page.getSize()
      const size = opt.fontSizePt || 60
      const tw = font.widthOfTextAtSize(opt.text, size)
      page.drawText(opt.text, {
        x: (width - tw) / 2, y: height / 2, size, font,
        color: rgb(r, g, b), opacity: opt.opacity ?? 0.2,
        rotate: degrees(opt.angleDeg ?? -45),
      })
    }
  } else if (opt.type === 'image' && opt.imageBytes) {
    const img = await doc.embedJpg(opt.imageBytes).catch(() => doc.embedPng(opt.imageBytes!))
    for (const page of docPages) {
      const { width, height } = page.getSize()
      const dim = img.scaleToFit(width * 0.4, height * 0.4)
      page.drawImage(img, {
        x: (width - dim.width) / 2, y: (height - dim.height) / 2,
        width: dim.width, height: dim.height, opacity: opt.opacity ?? 0.2,
      })
    }
  }
}

function triggerDownload(bytes: Uint8Array, name: string): void {
  const blob = new Blob([bytes], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
