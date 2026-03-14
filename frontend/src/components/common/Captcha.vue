<template>
  <div class="captcha-container">
    <canvas
      ref="canvasRef"
      :width="W"
      :height="H"
      class="captcha-canvas"
      title="点击刷新验证码"
      @click="refresh"
    />
    <el-button :icon="RefreshRight" circle size="small" text class="captcha-refresh" @click="refresh" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RefreshRight } from '@element-plus/icons-vue'

const W = 140
const H = 46
const canvasRef = ref<HTMLCanvasElement | null>(null)
const code = ref('')

// 不含易混淆字符（0/O, 1/I/l）的字符集
const CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'

// 字体样式池
const FONT_STYLES = ['bold', 'italic', 'bold italic', '900', '800']

function genCode(len = 5) {
  let s = ''
  for (let i = 0; i < len; i++) s += CHARS[Math.floor(Math.random() * CHARS.length)]
  return s
}

function rand(min: number, max: number) {
  return Math.random() * (max - min) + min
}

function randInt(min: number, max: number) {
  return Math.floor(rand(min, max))
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空
  ctx.clearRect(0, 0, W, H)

  // 背景：细腻纹理渐变
  const bg = ctx.createLinearGradient(0, 0, W, H)
  bg.addColorStop(0, '#edf0ff')
  bg.addColorStop(0.5, '#ede9fe')
  bg.addColorStop(1, '#e8f0ff')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, W, H)

  // 背景纹理点（细密噪点）
  for (let i = 0; i < 180; i++) {
    ctx.fillStyle = `rgba(${randInt(40, 180)},${randInt(40, 160)},${randInt(120, 240)},${rand(0.06, 0.2).toFixed(2)})`
    ctx.beginPath()
    ctx.arc(rand(0, W), rand(0, H), rand(0.3, 1.2), 0, Math.PI * 2)
    ctx.fill()
  }

  // 干扰线：多条贝塞尔曲线，更粗、更密
  for (let i = 0; i < 6; i++) {
    const alpha = rand(0.3, 0.55)
    ctx.strokeStyle = `rgba(${randInt(60, 160)},${randInt(60, 130)},${randInt(150, 230)},${alpha.toFixed(2)})`
    ctx.lineWidth = rand(1, 2.5)
    ctx.beginPath()
    ctx.moveTo(rand(0, W * 0.25), rand(0, H))
    ctx.bezierCurveTo(
      rand(W * 0.1, W * 0.4), rand(-4, H + 4),
      rand(W * 0.5, W * 0.85), rand(-4, H + 4),
      rand(W * 0.75, W), rand(0, H)
    )
    ctx.stroke()
  }

  // 绘制字符到临时 canvas，再波形变换到主 canvas
  const tmp = document.createElement('canvas')
  tmp.width = W; tmp.height = H
  const tc = tmp.getContext('2d')!

  const chars = code.value
  const step = W / (chars.length + 1)
  for (let i = 0; i < chars.length; i++) {
    const x = step * (i + 0.85) + rand(-4, 4)
    const y = H / 2 + rand(-4, 5)
    const angle = rand(-0.55, 0.55)        // 更大旋转角
    const size = randInt(16, 24)           // 更大字号
    const style = FONT_STYLES[randInt(0, FONT_STYLES.length)]
    const r = randInt(20, 100)
    const g = randInt(10, 60)
    const b = randInt(120, 210)

    tc.save()
    tc.translate(x, y)
    tc.rotate(angle)
    // 随机 X 轴缩放（字体扁平/拉伸变形）
    const scaleX = rand(0.75, 1.25)
    const scaleY = rand(0.85, 1.15)
    tc.scale(scaleX, scaleY)
    tc.font = `${style} ${size}px 'Arial Black','Impact',Arial,sans-serif`
    tc.fillStyle = `rgb(${r},${g},${b})`
    // 白色描边增加对比度和可读性
    tc.strokeStyle = `rgba(255,255,255,0.6)`
    tc.lineWidth = 2
    tc.strokeText(chars[i], 0, 0)
    tc.fillText(chars[i], 0, 0)
    tc.restore()
  }

  // 波形扭曲：逐列采样，上下位移
  const amplitude = rand(3, 6)    // 波幅
  const frequency = rand(0.03, 0.06)  // 频率
  const phaseH = rand(0, Math.PI * 2)
  const phaseV = rand(0, Math.PI * 2)

  const imgData = tc.getImageData(0, 0, W, H)
  const dst = ctx.createImageData(W, H)
  const src = imgData.data
  const out = dst.data

  for (let x = 0; x < W; x++) {
    for (let y = 0; y < H; y++) {
      // 双向正弦波形偏移
      const dx = Math.round(amplitude * Math.sin(y * frequency * 1.5 + phaseH))
      const dy = Math.round(amplitude * Math.sin(x * frequency + phaseV))
      const sx = Math.max(0, Math.min(W - 1, x - dx))
      const sy = Math.max(0, Math.min(H - 1, y - dy))
      const srcIdx = (sy * W + sx) * 4
      const dstIdx = (y * W + x) * 4
      out[dstIdx]     = src[srcIdx]
      out[dstIdx + 1] = src[srcIdx + 1]
      out[dstIdx + 2] = src[srcIdx + 2]
      out[dstIdx + 3] = src[srcIdx + 3]
    }
  }
  ctx.putImageData(dst, 0, 0)

  // 最后再叠加几条前景干扰线（覆盖在字符上方）
  for (let i = 0; i < 2; i++) {
    ctx.strokeStyle = `rgba(${randInt(80, 180)},${randInt(60, 120)},${randInt(160, 240)},${rand(0.2, 0.35).toFixed(2)})`
    ctx.lineWidth = rand(0.8, 1.5)
    ctx.beginPath()
    ctx.moveTo(rand(0, W * 0.2), rand(4, H - 4))
    ctx.quadraticCurveTo(rand(W * 0.3, W * 0.7), rand(2, H - 2), rand(W * 0.8, W), rand(4, H - 4))
    ctx.stroke()
  }
}

function refresh() {
  code.value = genCode()
  draw()
}

/** 校验用户输入（大小写不敏感） */
function validate(input: string): boolean {
  return input.trim().toLowerCase() === code.value.toLowerCase()
}

onMounted(() => {
  refresh()
})

defineExpose({ validate, refresh })
</script>

<style scoped lang="scss">
.captcha-container {
  display: flex;
  align-items: center;
  gap: 6px;
}

.captcha-canvas {
  border-radius: 6px;
  border: 1px solid var(--el-border-color);
  cursor: pointer;
  display: block;
  flex-shrink: 0;

  &:hover {
    opacity: 0.85;
    border-color: var(--el-color-primary);
  }
}

.captcha-refresh {
  flex-shrink: 0;
  color: var(--el-text-color-secondary);
}
</style>
