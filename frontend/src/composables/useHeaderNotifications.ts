import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { Notification } from '@/types/models'
import { notificationsApi } from '@/api/modules/notifications'

export function useHeaderNotifications() {
  const router = useRouter()
  const unreadCount = ref(0)
  const notifications = ref<Notification[]>([])
  const notifLoading = ref(false)

  async function fetchUnreadCount() {
    try {
      const res = await notificationsApi.getUnreadCount()
      unreadCount.value = res.data.count
    } catch { /* ignore */ }
  }

  async function loadNotifications() {
    notifLoading.value = true
    try {
      const res = await notificationsApi.getList(1, 10)
      notifications.value = res.items
    } catch { /* ignore */ } finally {
      notifLoading.value = false
    }
  }

  async function clearAllNotifications() {
    try {
      await notificationsApi.clearAll()
      notifications.value = []
      unreadCount.value = 0
    } catch {
      ElMessage.error('清除失败')
    }
  }

  function handleNotifClick(n: Notification) {
    if (!n.is_read) {
      n.is_read = 1
      if (unreadCount.value > 0) unreadCount.value--
      notificationsApi.readOne(n.id).catch(() => {})
    }
    if (n.type === 'follow') {
      router.push(`/u/${n.actor_username}`)
    } else if (n.type === 'admin') {
      const action = n.extra?.action
      if (action === 'report_invalid') {
        if (n.target_id) router.push(`/post/${n.target_id}`)
      } else if (action !== 'report_valid') {
        if (n.target_id) router.push(`/post/${n.target_id}/moderation`)
      }
    } else if (n.type === 'review_result') {
      if (n.target_id) {
        const action = n.extra?.action
        if (action === 'approved') router.push(`/post/${n.target_id}`)
        else router.push(`/post/${n.target_id}/moderation`)
      }
    } else if (n.type === 'appeal' || n.type === 'report') {
      router.push('/admin/review')
    } else if (n.type === 'pinned' && n.target_id) {
      router.push(`/post/${n.target_id}`)
    } else if (n.target_id) {
      const hash = (n.type === 'comment' || n.type === 'reply') ? '#comments' : ''
      router.push(`/post/${n.target_id}${hash}`)
    }
  }

  function formatNotif(n: Notification): string {
    const actor = n.actor_nickname || n.actor_username || '管理员'
    const postTitle = n.extra?.post_title ? `《${n.extra.post_title}》` : '你的博文'
    const content = n.extra?.content ? `：${n.extra.content}` : ''
    const reason = n.extra?.reason || ''
    switch (n.type) {
      case 'like':     return `${actor} 赞了 ${postTitle}`
      case 'collect':  return `${actor} 收藏了 ${postTitle}`
      case 'comment':  return `${actor} 评论了 ${postTitle}${content}`
      case 'reply':    return `${actor} 回复了你的评论${content}`
      case 'follow':   return `${actor} 关注了你`
      case 'new_post': return `您关注的 ${actor} 发布了新博文 ${postTitle}`
      case 'admin': {
        const action = n.extra?.action
        if (action === 'report_valid')   return `您举报的博文 ${postTitle} 经审核已被隐藏，感谢您维护社区环境`
        if (action === 'report_invalid') return `您举报的博文 ${postTitle} 经审核暂不违规，感谢您对社区的贡献`
        return `你的博文 ${postTitle} 已被隐藏${reason ? '，原因：' + reason : ''}`
      }
      case 'appeal': {
        const appealPost = n.extra?.post_title ? `《${n.extra.post_title}》` : '某博文'
        return `${actor} 对 ${appealPost} 提交了申诉`
      }
      case 'review_result': {
        const approved = n.extra?.action === 'approved'
        return approved
          ? `你对 ${postTitle} 的申诉已通过，博文已恢复`
          : `你对 ${postTitle} 的申诉被拒绝${reason ? '，原因：' + reason : ''}`
      }
      case 'report': {
        const reportPost = n.extra?.post_title ? `《${n.extra.post_title}》` : '某博文'
        return `${actor} 对 ${reportPost} 提交了举报${reason ? '，理由：' + n.extra?.reason : ''}`
      }
      case 'pinned': return `博文 ${postTitle} 已被置顶推荐`
      default: return '新通知'
    }
  }

  return {
    unreadCount, notifications, notifLoading,
    fetchUnreadCount, loadNotifications, clearAllNotifications,
    handleNotifClick, formatNotif,
  }
}
