/**
 * marked + highlight.js 配置模块
 * 在此模块级别初始化，确保 marked.use() 只执行一次
 */
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import go from 'highlight.js/lib/languages/go'
import java from 'highlight.js/lib/languages/java'
import 'highlight.js/styles/github.min.css'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('go', go)
hljs.registerLanguage('java', java)

marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  }
}))

// 显式启用 GFM（表格、删除线、任务列表、自动链接等），单换行转 <br>
marked.use({ gfm: true, breaks: true })

// 图片渲染：添加 loading="lazy"，避免影响首屏性能
marked.use({
  renderer: {
    image({ href, title, text }: { href: string; title?: string | null; text: string }) {
      const titleAttr = title ? ` title="${title}"` : ''
      return `<img src="${href}" alt="${text}"${titleAttr} loading="lazy">`
    }
  }
})

// 表格：用 .md-table-wrap 包裹，支持圆角容器 + 横向滚动
marked.use({
  hooks: {
    postprocess(html: string) {
      return html
        .replace(/<table>/g, '<div class="md-table-wrap"><table>')
        .replace(/<\/table>/g, '</table></div>')
    }
  }
})

export { marked }
