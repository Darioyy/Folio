<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  mimeType?: string
  fileName?: string
  fileCategory?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  mimeType: '',
  fileName: '',
  fileCategory: '',
  size: 'md'
})

const sizeMap = { sm: 18, md: 28, lg: 36 }
const iconSize = computed(() => sizeMap[props.size])

type IconDef = { paths: string; color: string; mode: 'stroke' | 'fill' }

const iconDef = computed((): IconDef => {
  const mime = (props.mimeType || '').toLowerCase()
  const ext = (props.fileName || '').split('.').pop()?.toLowerCase() || ''
  const cat = (props.fileCategory || '').toLowerCase()

  // Folder
  if (cat === 'folder')
    return {
      paths: `<path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" opacity="0.9"/>`,
      color: '#f59e0b',
      mode: 'fill',
    }

  // Image
  if (cat === 'image' || mime.startsWith('image/') || ['jpg','jpeg','png','gif','webp','svg','bmp','avif','ico','tiff'].includes(ext))
    return {
      paths: `<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>`,
      color: '#10b981',
      mode: 'stroke',
    }

  // Video
  if (cat === 'video' || mime.startsWith('video/') || ['mp4','avi','mkv','mov','webm','flv','wmv','m4v','rmvb'].includes(ext))
    return {
      paths: `<polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>`,
      color: '#ec4899',
      mode: 'stroke',
    }

  // Audio
  if (mime.startsWith('audio/') || ['mp3','wav','ogg','flac','aac','m4a','wma'].includes(ext))
    return {
      paths: `<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>`,
      color: '#06b6d4',
      mode: 'stroke',
    }

  // PDF
  if (mime.includes('pdf') || ext === 'pdf')
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>`,
      color: '#ef4444',
      mode: 'stroke',
    }

  // Word
  if (mime.includes('msword') || mime.includes('wordprocessingml') || ['doc','docx'].includes(ext))
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>`,
      color: '#3b82f6',
      mode: 'stroke',
    }

  // Excel / CSV
  if (mime.includes('spreadsheetml') || mime.includes('excel') || ['xls','xlsx','csv'].includes(ext))
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>`,
      color: '#22c55e',
      mode: 'stroke',
    }

  // PowerPoint
  if (mime.includes('presentationml') || mime.includes('powerpoint') || ['ppt','pptx'].includes(ext))
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>`,
      color: '#f97316',
      mode: 'stroke',
    }

  // Archive
  if (mime.match(/zip|rar|7z|tar|gzip|x-compressed/) || ['zip','rar','7z','tar','gz','bz2'].includes(ext))
    return {
      paths: `<rect x="3" y="2" width="18" height="20" rx="2"/><path d="M21 6H3"/><path d="M21 10H3"/><path d="M12 12v8"/><path d="M9 15h6"/>`,
      color: '#8b5cf6',
      mode: 'stroke',
    }

  // Code
  if (['js','ts','jsx','tsx','py','java','cpp','c','go','rs','rb','php','swift','kt','vue','css','scss','html','json','xml','yaml','yml','toml'].includes(ext))
    return {
      paths: `<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>`,
      color: '#5a67d8',
      mode: 'stroke',
    }

  // Markdown
  if (ext === 'md' || ext === 'markdown' || mime.includes('markdown'))
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>`,
      color: '#0ea5e9',
      mode: 'stroke',
    }

  // TXT / plain text (三条不等长线，区别于 Word/Excel)
  if (['txt','log','ini'].includes(ext) || mime === 'text/plain')
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="14.5" x2="14" y2="14.5"/><line x1="8" y1="18" x2="12" y2="18"/>`,
      color: '#64748b',
      mode: 'stroke',
    }

  // Other text (csv-like, markdown-like, generic text)
  if (mime.startsWith('text/'))
    return {
      paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>`,
      color: '#94a3b8',
      mode: 'stroke',
    }

  // Generic
  return {
    paths: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>`,
    color: '#9ca3af',
    mode: 'stroke',
  }
})
</script>

<template>
  <svg
    :width="iconSize"
    :height="iconSize"
    viewBox="0 0 24 24"
    :fill="iconDef.mode === 'fill' ? iconDef.color : 'none'"
    :stroke="iconDef.mode === 'stroke' ? iconDef.color : 'none'"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    v-html="iconDef.paths"
  />
</template>
