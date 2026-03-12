"""
通知服务（含去重逻辑）
"""
from datetime import datetime
from typing import Dict
from sqlalchemy import select, func, and_
from db.session import db
from core.models.notification import Notification


class NotificationService:

    @staticmethod
    def create(user_id: int, type_: str, actor_id: int,
               target_id: int = None, extra: dict = None) -> None:
        """创建通知。自己触发的不通知自己。"""
        if user_id == actor_id:
            return
        notif = Notification(
            user_id=user_id,
            type=type_,
            actor_id=actor_id,
            target_id=target_id,
            extra=extra or {}
        )
        db.session.add(notif)
        db.session.commit()

    @staticmethod
    def upsert(user_id: int, type_: str, actor_id: int,
               target_id: int = None, extra: dict = None) -> None:
        """幂等创建通知：若同 actor+type+target 通知已存在则刷新时间，否则新建。
        用于 like/collect/follow，避免反复操作产生大量重复通知。"""
        if user_id == actor_id:
            return
        existing = db.session.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.type == type_,
                    Notification.actor_id == actor_id,
                    Notification.target_id == target_id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.is_read = 0
            existing.created_at = datetime.utcnow()
            if extra:
                existing.extra = extra
        else:
            db.session.add(Notification(
                user_id=user_id, type=type_, actor_id=actor_id,
                target_id=target_id, extra=extra or {}
            ))
        db.session.commit()

    @staticmethod
    def delete_by_actor(user_id: int, type_: str, actor_id: int,
                        target_id: int = None) -> None:
        """删除特定 actor 对 user 的某类通知（取消操作时调用）。"""
        existing = db.session.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.type == type_,
                    Notification.actor_id == actor_id,
                    Notification.target_id == target_id,
                )
            )
        ).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

    @staticmethod
    def get_notifications(user_id: int, page: int = 1, page_size: int = 20) -> Dict:
        offset = (page - 1) * page_size
        total = db.session.execute(
            select(func.count(Notification.id)).where(Notification.user_id == user_id)
        ).scalar() or 0

        notifications = db.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset).limit(page_size)
        ).scalars().all()

        return {
            'items': [n.to_dict(include_actor=True) for n in notifications],
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        return db.session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == 0
            )
        ).scalar() or 0

    @staticmethod
    def mark_all_read(user_id: int) -> None:
        db.session.execute(
            Notification.__table__.update()
            .where(Notification.user_id == user_id, Notification.is_read == 0)
            .values(is_read=1)
        )
        db.session.commit()

    @staticmethod
    def delete_notification(notification_id: int, user_id: int) -> bool:
        notif = db.session.get(Notification, notification_id)
        if not notif or notif.user_id != user_id:
            raise ValueError('通知不存在或无权删除')
        db.session.delete(notif)
        db.session.commit()
        return True


notification_service = NotificationService()
