<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  mimeType?: string
  fileName?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  mimeType: '',
  fileName: '',
  size: 'md'
})

const sizeMap = { sm: 44, md: 64, lg: 88 }
const svgHeight = computed(() => sizeMap[props.size])
const svgWidth = computed(() => Math.round(sizeMap[props.size] * 0.8))

const typeInfo = computed((): { label: string; color: string } => {
  const mime = (props.mimeType || '').toLowerCase()
  const ext = (props.fileName || '').split('.').pop()?.toLowerCase() || ''

  if (mime.includes('pdf') || ext === 'pdf')
    return { label: 'PDF', color: '#ef4444' }
  if (mime.includes('msword') || mime.includes('wordprocessingml') || ['doc', 'docx'].includes(ext))
    return { label: 'DOC', color: '#3b82f6' }
  if (mime.includes('spreadsheetml') || mime.includes('excel') || ['xls', 'xlsx', 'csv'].includes(ext))
    return { label: 'XLS', color: '#22c55e' }
  if (mime.includes('presentationml') || mime.includes('powerpoint') || ['ppt', 'pptx'].includes(ext))
    return { label: 'PPT', color: '#f97316' }
  if (mime.match(/zip|rar|7z|tar|gzip|x-compressed/) || ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(ext))
    return { label: 'ZIP', color: '#eab308' }
  if (mime.startsWith('audio/') || ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'].includes(ext))
    return { label: 'MP3', color: '#a855f7' }
  if (mime.startsWith('video/') || ['mp4', 'avi', 'mkv', 'mov', 'webm', 'flv'].includes(ext))
    return { label: 'MP4', color: '#6366f1' }
  if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs', 'rb', 'php', 'swift', 'kt'].includes(ext))
    return { label: 'CODE', color: '#10b981' }
  if (ext === 'md' || ext === 'markdown' || mime.includes('markdown'))
    return { label: 'MD', color: '#0ea5e9' }
  if (mime.startsWith('text/') || ['txt', 'log', 'ini', 'yaml', 'yml', 'json', 'xml', 'toml'].includes(ext))
    return { label: 'TXT', color: '#94a3b8' }

  if (ext && ext.length <= 4)
    return { label: ext.toUpperCase(), color: '#6366f1' }

  const sub = mime.split('/')[1] || ''
  const parts = sub.split(/[.+\-]/)
  const fallback = (parts[parts.length - 1] || '').toUpperCase().substring(0, 4)
  return { label: fallback || 'FILE', color: '#6366f1' }
})

const fillColor = computed(() => {
  const hex = typeInfo.value.color.slice(1)
  const r = parseInt(hex.slice(0, 2), 16)
  const g = parseInt(hex.slice(2, 4), 16)
  const b = parseInt(hex.slice(4, 6), 16)
  return `rgba(${r},${g},${b},0.08)`
})

const fontSize = computed(() => {
  // Adjust font size based on label length (in SVG units, viewBox is 32x40)
  if (typeInfo.value.label.length >= 4) return '6.5'
  return '8'
})
</script>

<template>
  <svg
    :width="svgWidth"
    :height="svgHeight"
    viewBox="0 0 32 40"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Document body -->
    <path
      d="M2 0H21L30 9V40H2V0Z"
      :fill="fillColor"
      :stroke="typeInfo.color"
      stroke-width="1.5"
      stroke-linejoin="round"
    />
    <!-- Fold crease -->
    <path
      d="M21 0V9H30"
      :stroke="typeInfo.color"
      stroke-width="1.5"
      stroke-linejoin="round"
    />
    <!-- Type label -->
    <text
      x="16"
      y="27"
      text-anchor="middle"
      dominant-baseline="central"
      :font-size="fontSize"
      font-weight="700"
      font-family="system-ui,-apple-system,sans-serif"
      :fill="typeInfo.color"
    >{{ typeInfo.label }}</text>
  </svg>
</template>
