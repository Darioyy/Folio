import { ref } from 'vue'
import ImageWorker from '@/workers/imageProcess.worker?worker'

export interface EnhancementSettings {
  brightness: number  // -100..100
  contrast: number    // -100..100
  sharpen: number     // 0..100
  denoise: number     // 0..100
  binarize: boolean
}

export const DEFAULT_SETTINGS: EnhancementSettings = {
  brightness: 0, contrast: 0, sharpen: 0, denoise: 0, binarize: false,
}

export const PRESETS: Record<'document' | 'photo' | 'bw', EnhancementSettings> = {
  document: { brightness: 10, contrast: 20, sharpen: 40, denoise: 20, binarize: false },
  photo:    { brightness: 5,  contrast: 10, sharpen: 20, denoise: 10, binarize: false },
  bw:       { brightness: 10, contrast: 60, sharpen: 50, denoise: 10, binarize: true  },
}

type PendingItem = {
  resolve: (v: { pixels: Uint8ClampedArray; width: number; height: number }) => void
  reject: (e: Error) => void
}

let sharedWorker: Worker | null = null
const pending = new Map<string, PendingItem>()
let reqSeq = 0

function getWorker(): Worker {
  if (!sharedWorker) {
    sharedWorker = new ImageWorker()
    sharedWorker.onmessage = (e: MessageEvent) => {
      const { id, pixels, width, height, error } = e.data
      const item = pending.get(id)
      if (!item) return
      pending.delete(id)
      if (error) item.reject(new Error(error))
      else item.resolve({ pixels, width, height })
    }
  }
  return sharedWorker
}

export function useImageEnhancer() {
  const processing = ref(false)

  async function processPixels(
    pixels: Uint8ClampedArray,
    width: number,
    height: number,
    settings: EnhancementSettings,
  ): Promise<{ pixels: Uint8ClampedArray; width: number; height: number }> {
    const id = `r${reqSeq++}`
    const copy = new Uint8ClampedArray(pixels)
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject })
      getWorker().postMessage({ id, pixels: copy, width, height, settings }, [copy.buffer])
    })
  }

  async function processDataUrl(
    dataUrl: string,
    settings: EnhancementSettings,
  ): Promise<string> {
    processing.value = true
    try {
      const { pixels, width, height } = await dataUrlToPixels(dataUrl)
      const result = await processPixels(pixels, width, height, settings)
      const canvas = document.createElement('canvas')
      canvas.width = result.width
      canvas.height = result.height
      canvas.getContext('2d')!.putImageData(new ImageData(result.pixels, result.width, result.height), 0, 0)
      return canvas.toDataURL('image/jpeg', 0.92)
    } finally {
      processing.value = false
    }
  }

  return { processing, processPixels, processDataUrl }
}

function dataUrlToPixels(dataUrl: string): Promise<{ pixels: Uint8ClampedArray; width: number; height: number }> {
  return new Promise(resolve => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      const ctx = canvas.getContext('2d')!
      ctx.drawImage(img, 0, 0)
      const d = ctx.getImageData(0, 0, canvas.width, canvas.height)
      resolve({ pixels: d.data, width: canvas.width, height: canvas.height })
    }
    img.src = dataUrl
  })
}
