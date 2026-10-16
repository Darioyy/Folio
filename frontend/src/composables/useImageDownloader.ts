import JSZip from 'jszip'

export const PROXIES: Array<(url: string) => string> = [
  url => `https://corsproxy.io/?${encodeURIComponent(url)}`,
  url => `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`,
]

export interface ImageResult {
  filename: string
  data: ArrayBuffer
  ok: true
}

export interface ImageFailure {
  ok: false
}

export type ImageDownloadResult = ImageResult | ImageFailure

export async function pooledAll<T>(
  factories: Array<() => Promise<T>>,
  limit = 4,
): Promise<T[]> {
  const results = new Array<T>(factories.length)
  let cursor = 0
  async function runNext(): Promise<void> {
    const i = cursor++
    if (i >= factories.length) return
    results[i] = await factories[i]()
    return runNext()
  }
  await Promise.all(Array.from({ length: Math.min(limit, factories.length) }, runNext))
  return results
}

export function buildFileMap(entries: { file: File; relPath: string }[]): Map<string, File> {
  const map = new Map<string, File>()
  for (const { file, relPath } of entries) {
    // 存相对路径（去掉开头的 ./，清除查询字符串），供精确匹配
    const cleanRel = relPath.replace(/^\.\//, '').split('?')[0].toLowerCase()
    map.set(cleanRel, file)
    // 仅以文件名作 fallback 键——先到先得，避免同名文件静默覆盖
    const filename = cleanRel.split('/').pop() || ''
    if (filename && !map.has(filename)) map.set(filename, file)
  }
  return map
}

export function lookupLocalFile(src: string, fileMap: Map<string, File>): File | null {
  if (!fileMap || fileMap.size === 0) return null
  for (const candidate of [src, decodeURIComponent(src)]) {
    // 1. 优先匹配相对路径（如 "page_files/image.png"），与 buildFileMap 的 cleanRel 键对应
    const relPath = candidate.replace(/^\.\//, '').split('?')[0].toLowerCase()
    const byRel = fileMap.get(relPath)
    if (byRel) return byRel
    // 2. 退回到仅文件名匹配
    const filename = relPath.split('/').pop() || ''
    const byName = fileMap.get(filename)
    if (byName) return byName
  }
  return null
}

function parseDataUri(dataUri: string): { ext: string; buf: ArrayBuffer } {
  const comma = dataUri.indexOf(',')
  const header = dataUri.slice(0, comma)
  const b64 = dataUri.slice(comma + 1)
  const mime = (header.match(/data:([^;,]+)/) || [])[1] || 'image/png'
  const ext = mime.split('/')[1]?.replace('jpeg', 'jpg').replace('svg+xml', 'svg') || 'png'
  const bin = atob(b64)
  const buf = new ArrayBuffer(bin.length)
  const view = new Uint8Array(buf)
  for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i)
  return { ext, buf }
}

function makeImgName(url: string, ts: number): string {
  try {
    const u = new URL(url, 'http://x/')
    const last = decodeURIComponent(u.pathname.split('/').filter(Boolean).pop() || 'image')
    const dot = last.lastIndexOf('.')
    const ext = (dot > 0 ? last.slice(dot + 1) : 'png').split('?')[0].toLowerCase().slice(0, 6) || 'png'
    const base = (dot > 0 ? last.slice(0, dot) : last).replace(/[^a-z0-9_-]/gi, '_').slice(0, 40)
    return `${ts}_${base}.${ext}`
  } catch {
    return `${ts}_image.png`
  }
}

export async function downloadImages(
  el: Element,
  baseUrl: string | null,
  sessionTs: number,
  fileMap: Map<string, File>,
): Promise<ImageDownloadResult[]> {
  const imgs = [...el.querySelectorAll('img')].filter(img => {
    const w = img.getAttribute('width')
    const h = img.getAttribute('height')
    return !(w && h && +w <= 2 && +h <= 2)
  })

  const tasks = imgs.map((img, i) => async (): Promise<ImageDownloadResult> => {
    const src = img.getAttribute('src') || ''

    if (src.startsWith('data:')) {
      try {
        const { ext, buf } = parseDataUri(src)
        const fname = `${sessionTs + i}_image.${ext}`
        img.setAttribute('src', `images/${fname}`)
        return { filename: fname, data: buf, ok: true }
      } catch { return { ok: false } }
    }

    const fname = makeImgName(src, sessionTs + i)

    const localFile = lookupLocalFile(src, fileMap)
    if (localFile) {
      try {
        const buf = await localFile.arrayBuffer()
        img.setAttribute('src', `images/${fname}`)
        return { filename: fname, data: buf, ok: true }
      } catch { /* fall through to network */ }
    }

    let absUrl: string
    try {
      absUrl = new URL(src, baseUrl || 'x://x/').href
      if (absUrl.startsWith('x://')) return { ok: false }
    } catch { return { ok: false } }

    // 1st: backend image proxy (our server, browser-like headers, no CORS limit)
    try {
      const ctrl = new AbortController()
      const tid = setTimeout(() => ctrl.abort(), 10000)
      const resp = await fetch(`/api/v1/tools/image?url=${encodeURIComponent(absUrl)}`, { signal: ctrl.signal })
      clearTimeout(tid)
      if (resp.ok) {
        const buf = await resp.arrayBuffer()
        img.setAttribute('src', `images/${fname}`)
        return { filename: fname, data: buf, ok: true }
      }
    } catch { /* fall through */ }

    // 2nd/3rd: public CORS proxies
    for (const makeProxy of PROXIES) {
      try {
        const ctrl = new AbortController()
        const tid = setTimeout(() => ctrl.abort(), 10000)
        const resp = await fetch(makeProxy(absUrl), { signal: ctrl.signal })
        clearTimeout(tid)
        if (!resp.ok) continue
        const buf = await resp.arrayBuffer()
        img.setAttribute('src', `images/${fname}`)
        return { filename: fname, data: buf, ok: true }
      } catch { /* try next proxy */ }
    }
    return { ok: false }
  })

  return pooledAll(tasks, 4)
}

export async function buildZip(name: string, md: string, images: ImageResult[]): Promise<Blob> {
  const zip = new JSZip()
  zip.file(`${name}.md`, md)
  if (images.length > 0) {
    const folder = zip.folder('images')!
    for (const { filename, data } of images) folder.file(filename, data)
  }
  return zip.generateAsync({ type: 'blob' })
}

export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // 延迟撤销：浏览器下载是异步触发的，立即撤销会导致大文件下载失败
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
