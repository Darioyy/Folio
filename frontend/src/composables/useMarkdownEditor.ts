import { type Ref, nextTick } from 'vue'

export function useMarkdownEditor(
  content: Ref<string>,
  textareaRef: Ref<HTMLTextAreaElement | null>
) {
  /** 在光标处插入文字，插入后光标移到末尾 */
  function insertAtCursor(text: string) {
    const ta = textareaRef.value
    if (!ta) { content.value += text; return }
    const start = ta.selectionStart
    const end = ta.selectionEnd
    content.value = content.value.slice(0, start) + text + content.value.slice(end)
    nextTick(() => { ta.selectionStart = ta.selectionEnd = start + text.length; ta.focus() })
  }

  /** 用前缀/后缀包裹选中内容；无选中则插入占位词并自动选中它 */
  function wrapSelection(prefix: string, suffix: string, placeholder = 'text') {
    const ta = textareaRef.value
    if (!ta) return
    const start = ta.selectionStart
    const end = ta.selectionEnd
    const hasSelection = start !== end
    const selected = hasSelection ? content.value.slice(start, end) : placeholder
    const newText = prefix + selected + suffix
    content.value = content.value.slice(0, start) + newText + content.value.slice(end)
    nextTick(() => {
      if (hasSelection) {
        ta.selectionStart = ta.selectionEnd = start + newText.length
      } else {
        // 无选中时，选中插入的占位词，方便用户直接覆盖
        ta.selectionStart = start + prefix.length
        ta.selectionEnd = start + prefix.length + placeholder.length
      }
      ta.focus()
    })
  }

  function handleKeydown(e: KeyboardEvent) {
    // Tab → 插入两个空格缩进
    if (e.key === 'Tab') {
      e.preventDefault()
      const ta = e.target as HTMLTextAreaElement
      const start = ta.selectionStart
      const end = ta.selectionEnd
      content.value = content.value.slice(0, start) + '  ' + content.value.slice(end)
      nextTick(() => { ta.selectionStart = ta.selectionEnd = start + 2 })
      return
    }

    // Enter（非 Shift/Ctrl/Meta）→ 智能列表延续
    if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
      const ta = e.target as HTMLTextAreaElement
      const pos = ta.selectionStart
      const lineStart = content.value.lastIndexOf('\n', pos - 1) + 1
      const line = content.value.slice(lineStart, pos)

      // 无序列表：- / * / +
      const ulMatch = line.match(/^(\s*)([-*+]) /)
      if (ulMatch) {
        e.preventDefault()
        const body = line.slice(ulMatch[0].length)
        if (!body.trim()) {
          // 空列表项 → 退出列表，插入空行
          content.value = content.value.slice(0, lineStart) + '\n' + content.value.slice(pos)
          nextTick(() => { ta.selectionStart = ta.selectionEnd = lineStart + 1 })
        } else {
          const cont = '\n' + ulMatch[1] + ulMatch[2] + ' '
          content.value = content.value.slice(0, pos) + cont + content.value.slice(ta.selectionEnd)
          nextTick(() => { ta.selectionStart = ta.selectionEnd = pos + cont.length })
        }
        return
      }

      // 有序列表：1. / 2. 等
      const olMatch = line.match(/^(\s*)(\d+)\. /)
      if (olMatch) {
        e.preventDefault()
        const body = line.slice(olMatch[0].length)
        if (!body.trim()) {
          content.value = content.value.slice(0, lineStart) + '\n' + content.value.slice(pos)
          nextTick(() => { ta.selectionStart = ta.selectionEnd = lineStart + 1 })
        } else {
          const cont = '\n' + olMatch[1] + (parseInt(olMatch[2]) + 1) + '. '
          content.value = content.value.slice(0, pos) + cont + content.value.slice(ta.selectionEnd)
          nextTick(() => { ta.selectionStart = ta.selectionEnd = pos + cont.length })
        }
        return
      }

      // 任务列表：- [ ] / - [x]
      const taskMatch = line.match(/^(\s*)([-*+]) \[[ x]\] /)
      if (taskMatch) {
        e.preventDefault()
        const body = line.slice(taskMatch[0].length)
        if (!body.trim()) {
          content.value = content.value.slice(0, lineStart) + '\n' + content.value.slice(pos)
          nextTick(() => { ta.selectionStart = ta.selectionEnd = lineStart + 1 })
        } else {
          const cont = '\n' + taskMatch[1] + taskMatch[2] + ' [ ] '
          content.value = content.value.slice(0, pos) + cont + content.value.slice(ta.selectionEnd)
          nextTick(() => { ta.selectionStart = ta.selectionEnd = pos + cont.length })
        }
        return
      }
    }
  }

  return { insertAtCursor, wrapSelection, handleKeydown }
}
