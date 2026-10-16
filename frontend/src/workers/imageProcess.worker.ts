export type {}

interface Settings {
  brightness: number  // -100..100
  contrast: number    // -100..100
  sharpen: number     // 0..100
  denoise: number     // 0..100
  binarize: boolean
}

self.addEventListener('message', (e: MessageEvent) => {
  const { id, pixels, width, height, settings } = e.data as {
    id: string; pixels: Uint8ClampedArray; width: number; height: number; settings: Settings
  }
  try {
    const buf = new Uint8ClampedArray(pixels)
    if (settings.denoise > 5) boxBlur(buf, width, height)
    applyBrightnessContrast(buf, settings.brightness, settings.contrast)
    if (settings.sharpen > 5) unsharpMask(buf, width, height, settings.sharpen / 80)
    if (settings.binarize) {
      normalizeBackground(buf, width, height)
      sauvolaBinarize(buf, width, height)
      despeckle(buf, width, height)
    }
    self.postMessage({ id, pixels: buf, width, height }, [buf.buffer] as unknown as Transferable[])
  } catch (err) {
    self.postMessage({ id, error: (err as Error).message })
  }
})

function applyBrightnessContrast(d: Uint8ClampedArray, brightness: number, contrast: number): void {
  const b = brightness * 2.55
  const f = contrast >= 0 ? 1 + contrast / 50 : 1 + contrast / 100
  for (let i = 0; i < d.length; i += 4) {
    for (let c = 0; c < 3; c++) d[i + c] = clamp((d[i + c] - 128) * f + 128 + b)
  }
}

function boxBlur(d: Uint8ClampedArray, w: number, h: number): void {
  const s = new Uint8ClampedArray(d)
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const o = (y * w + x) * 4
      for (let c = 0; c < 3; c++) {
        d[o + c] = (
          s[((y-1)*w+(x-1))*4+c] + s[((y-1)*w+x)*4+c] + s[((y-1)*w+(x+1))*4+c] +
          s[(y*w+(x-1))*4+c]     + s[o+c]              + s[(y*w+(x+1))*4+c] +
          s[((y+1)*w+(x-1))*4+c] + s[((y+1)*w+x)*4+c] + s[((y+1)*w+(x+1))*4+c]
        ) / 9
      }
    }
  }
}

function gaussianBlur(d: Uint8ClampedArray, w: number, h: number): Uint8ClampedArray {
  const o = new Uint8ClampedArray(d.length)
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = (y * w + x) * 4
      for (let c = 0; c < 3; c++) {
        o[i + c] = (
          d[((y-1)*w+(x-1))*4+c]   + d[((y-1)*w+x)*4+c]*2 + d[((y-1)*w+(x+1))*4+c] +
          d[(y*w+(x-1))*4+c]*2     + d[i+c]*4              + d[(y*w+(x+1))*4+c]*2 +
          d[((y+1)*w+(x-1))*4+c]   + d[((y+1)*w+x)*4+c]*2 + d[((y+1)*w+(x+1))*4+c]
        ) / 16
      }
      o[i + 3] = d[i + 3]
    }
  }
  for (let y = 0; y < h; y++) {
    const a = y * w * 4, b = (y * w + w - 1) * 4
    for (let c = 0; c < 4; c++) { o[a + c] = d[a + c]; o[b + c] = d[b + c] }
  }
  for (let x = 0; x < w; x++) {
    const a = x * 4, b = ((h - 1) * w + x) * 4
    for (let c = 0; c < 4; c++) { o[a + c] = d[a + c]; o[b + c] = d[b + c] }
  }
  return o
}

function unsharpMask(d: Uint8ClampedArray, w: number, h: number, amount: number): void {
  const blurred = gaussianBlur(d, w, h)
  for (let i = 0; i < d.length; i += 4) {
    for (let c = 0; c < 3; c++) d[i + c] = clamp(d[i + c] + amount * (d[i + c] - blurred[i + c]) * 2.5)
  }
}

// ── Background normalization ───────────────────────────────────────────────────
// Uses integral image for fast large-radius box blur (radius=40).
// Equalizes uneven lighting/shadows common in photographed documents.
function normalizeBackground(d: Uint8ClampedArray, w: number, h: number): void {
  const n = w * h
  const gray = new Float32Array(n)
  for (let i = 0; i < n; i++) {
    gray[i] = 0.299 * d[i * 4] + 0.587 * d[i * 4 + 1] + 0.114 * d[i * 4 + 2]
  }

  // Build 2D prefix sum
  const W1 = w + 1
  const S = new Float64Array(W1 * (h + 1))
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const v = gray[y * w + x], idx = (y + 1) * W1 + (x + 1)
      S[idx] = v + S[y * W1 + (x + 1)] + S[(y + 1) * W1 + x] - S[y * W1 + x]
    }
  }

  const R = 40
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const x1 = Math.max(0, x - R), y1 = Math.max(0, y - R)
      const x2 = Math.min(w - 1, x + R), y2 = Math.min(h - 1, y + R)
      const cnt = (x2 - x1 + 1) * (y2 - y1 + 1)
      const bg = (S[(y2+1)*W1+(x2+1)] - S[y1*W1+(x2+1)] - S[(y2+1)*W1+x1] + S[y1*W1+x1]) / cnt
      const v = clamp(bg > 1 ? gray[y * w + x] * 200 / bg : gray[y * w + x])
      const px = (y * w + x) * 4
      d[px] = d[px + 1] = d[px + 2] = v
    }
  }
}

// ── Sauvola adaptive binarization ─────────────────────────────────────────────
// k=0.2 (was 0.5): lower value preserves thin strokes in document text.
// halfWindow=10 (was 7): larger window handles more lighting variation.
function sauvolaBinarize(d: Uint8ClampedArray, w: number, h: number): void {
  const wh = w * h
  const gray = new Float32Array(wh)
  for (let i = 0; i < wh; i++) gray[i] = 0.299 * d[i * 4] + 0.587 * d[i * 4 + 1] + 0.114 * d[i * 4 + 2]
  const W1 = w + 1
  const S = new Float64Array(W1 * (h + 1))
  const S2 = new Float64Array(W1 * (h + 1))
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const v = gray[y * w + x], idx = (y + 1) * W1 + (x + 1)
      S[idx]  = v     + S[y * W1 + (x + 1)] + S[(y + 1) * W1 + x] - S[y * W1 + x]
      S2[idx] = v * v + S2[y * W1 + (x + 1)] + S2[(y + 1) * W1 + x] - S2[y * W1 + x]
    }
  }
  const half = 10, k = 0.2, R = 128
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const x1 = Math.max(0, x - half), y1 = Math.max(0, y - half)
      const x2 = Math.min(w - 1, x + half), y2 = Math.min(h - 1, y + half)
      const cnt = (x2 - x1 + 1) * (y2 - y1 + 1)
      const s  = S[(y2+1)*W1+(x2+1)] - S[y1*W1+(x2+1)] - S[(y2+1)*W1+x1] + S[y1*W1+x1]
      const s2 = S2[(y2+1)*W1+(x2+1)] - S2[y1*W1+(x2+1)] - S2[(y2+1)*W1+x1] + S2[y1*W1+x1]
      const mean = s / cnt
      const thr = mean * (1 + k * (Math.sqrt(Math.max(0, s2 / cnt - mean * mean)) / R - 1))
      const v = gray[y * w + x] < thr ? 0 : 255
      const px = (y * w + x) * 4; d[px] = d[px + 1] = d[px + 2] = v
    }
  }
}

// ── Despeckle (morphological noise removal) ───────────────────────────────────
// Pass 1: remove isolated black pixels (< 2 black neighbors → flip white).
// Pass 2: fill isolated white holes (< 2 white neighbors → flip black).
function despeckle(d: Uint8ClampedArray, w: number, h: number): void {
  const n = w * h
  const bin = new Uint8Array(n)
  for (let i = 0; i < n; i++) bin[i] = d[i * 4]

  const out = new Uint8Array(bin)
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const idx = y * w + x
      if (bin[idx] === 0) {
        const cnt =
          (bin[(y-1)*w+(x-1)] === 0 ? 1 : 0) + (bin[(y-1)*w+x] === 0 ? 1 : 0) +
          (bin[(y-1)*w+(x+1)] === 0 ? 1 : 0) + (bin[y*w+(x-1)] === 0 ? 1 : 0) +
          (bin[y*w+(x+1)] === 0 ? 1 : 0) + (bin[(y+1)*w+(x-1)] === 0 ? 1 : 0) +
          (bin[(y+1)*w+x] === 0 ? 1 : 0) + (bin[(y+1)*w+(x+1)] === 0 ? 1 : 0)
        if (cnt < 2) out[idx] = 255
      }
    }
  }

  const out2 = new Uint8Array(out)
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const idx = y * w + x
      if (out[idx] === 255) {
        const cnt =
          (out[(y-1)*w+(x-1)] === 255 ? 1 : 0) + (out[(y-1)*w+x] === 255 ? 1 : 0) +
          (out[(y-1)*w+(x+1)] === 255 ? 1 : 0) + (out[y*w+(x-1)] === 255 ? 1 : 0) +
          (out[y*w+(x+1)] === 255 ? 1 : 0) + (out[(y+1)*w+(x-1)] === 255 ? 1 : 0) +
          (out[(y+1)*w+x] === 255 ? 1 : 0) + (out[(y+1)*w+(x+1)] === 255 ? 1 : 0)
        if (cnt < 2) out2[idx] = 0
      }
    }
  }

  for (let i = 0; i < n; i++) {
    d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = out2[i]
  }
}

function clamp(v: number): number { return v < 0 ? 0 : v > 255 ? 255 : Math.round(v) }
