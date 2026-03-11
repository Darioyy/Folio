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

const W = 120
const H = 40
const canvasRef = ref<HTMLCanvasElement | null>(null)
const code = ref('')

// 不含易混淆字符（0/O, 1/I/l）的字符集
const CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'

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

  // 背景
  const bg = ctx.createLinearGradient(0, 0, W, H)
  bg.addColorStop(0, '#eef0ff')
  bg.addColorStop(1, '#ede9fe')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, W, H)

  // 噪点
  for (let i = 0; i < 100; i++) {
    ctx.fillStyle = `rgba(${randInt(60, 200)},${randInt(60, 200)},${randInt(60, 255)},${rand(0.15, 0.35).toFixed(2)})`
    ctx.beginPath()
    ctx.arc(rand(0, W), rand(0, H), rand(0.5, 1.5), 0, Math.PI * 2)
    ctx.fill()
  }

  // 干扰线（贝塞尔曲线）
  for (let i = 0; i < 4; i++) {
    ctx.strokeStyle = `rgba(${randInt(80, 180)},${randInt(80, 160)},${randInt(160, 240)},${rand(0.35, 0.55).toFixed(2)})`
    ctx.lineWidth = rand(1, 2)
    ctx.beginPath()
    ctx.moveTo(rand(0, W * 0.3), rand(0, H))
    ctx.bezierCurveTo(
      rand(W * 0.1, W * 0.5), rand(0, H),
      rand(W * 0.5, W * 0.9), rand(0, H),
      rand(W * 0.7, W), rand(0, H)
    )
    ctx.stroke()
  }

  // 绘制验证码字符
  const chars = code.value
  const step = W / (chars.length + 1)
  for (let i = 0; i < chars.length; i++) {
    const x = step * (i + 0.9) + rand(-3, 3)
    const y = H / 2 + rand(-4, 6)
    const angle = rand(-0.35, 0.35)
    const size = randInt(15, 20)
    const r = randInt(20, 120)
    const g = randInt(20, 80)
    const b = randInt(140, 220)

    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    ctx.font = `bold ${size}px 'Arial Black',Arial,sans-serif`
    ctx.fillStyle = `rgb(${r},${g},${b})`
    // 描边增加可读性
    ctx.strokeStyle = `rgba(${r},${g},${b},0.3)`
    ctx.lineWidth = 0.5
    ctx.fillText(chars[i], 0, 0)
    ctx.restore()
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
