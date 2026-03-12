"""
文章服务层 - 业务逻辑
"""

from datetime import datetime
from sqlalchemy import or_, select, func
from core.models.post import Post
from core.models.post_attachment import PostAttachment
from core.models.category import Category
from core.models.file import File
from core.utils.permissions import can_modify_user
from db.session import db as db_session


class PostService:
    """文章服务类"""

    @staticmethod
    def get_posts(
        page: int = 1,
        limit: int = 10,
        status: str = "published",
        category_id: int = None,
        search: str = "",
        author_id: int = None,
        sort: str = "latest",
        admin_view: bool = False,
    ) -> dict:
        """获取文章列表（分页、筛选、搜索、排序）"""
        query = Post.query

        if status and status != "all":
            query = query.filter(Post.status == status)

        # 公开列表过滤管理员隐藏的博文；管理员视图可见所有
        if status == 'published' and not admin_view:
            query = query.filter(Post.is_hidden == 0)

        if category_id:
            query = query.filter(Post.category_id == category_id)

        if author_id:
            query = query.filter(Post.author_id == author_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(Post.title.like(search_pattern), Post.content.like(search_pattern))
            )

        if sort == "hot":
            query = query.order_by((Post.like_count + Post.view_count).desc())
        else:
            query = query.order_by(Post.created_at.desc())

        total = query.count()
        offset = (page - 1) * limit
        posts = query.offset(offset).limit(limit).all()

        items = [p.to_dict(include_category=True, include_author=True) for p in posts]

        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }

    @staticmethod
    def get_my_posts(author_id: int, page: int = 1, page_size: int = 20, status: str = "all") -> dict:
        """获取当前用户自己的博文列表（支持 status 筛选）"""
        query = Post.query.filter(Post.author_id == author_id)

        if status and status != "all":
            query = query.filter(Post.status == status)

        query = query.order_by(Post.created_at.desc())

        total = query.count()
        offset = (page - 1) * page_size
        posts = query.offset(offset).limit(page_size).all()

        return {
            "items": [p.to_dict(include_category=True) for p in posts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_user_posts(username: str, page: int = 1, page_size: int = 20) -> dict:
        """获取指定用户的已发布博文列表（公开）"""
        from core.models.user import User
        user = db_session.session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        query = Post.query.filter(
            Post.author_id == user.id,
            Post.status == "published",
            Post.is_hidden == 0
        ).order_by(Post.created_at.desc())

        total = query.count()
        posts = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [p.to_dict(include_category=True, include_author=True) for p in posts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_post_by_id(post_id: int, increment_view: bool = True, viewer_key: str = None) -> dict:
        """获取文章详情"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        if increment_view:
            if viewer_key:
                # 去重：每用户每天只计一次
                try:
                    from core.models.post_view import PostView
                    from datetime import date
                    today = date.today()
                    existing = PostView.query.filter_by(
                        post_id=post_id, viewer_key=viewer_key, viewed_date=today
                    ).first()
                    if not existing:
                        pv = PostView(post_id=post_id, viewer_key=viewer_key, viewed_date=today)
                        db_session.session.add(pv)
                        post.view_count += 1
                        db_session.session.commit()
                except Exception:
                    # 表不存在时降级到直接计数
                    post.view_count += 1
                    db_session.session.commit()
            else:
                post.view_count += 1
                db_session.session.commit()

        return post.to_dict(include_category=True, include_author=True, include_attachments=True)

    @staticmethod
    def get_following_posts(user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取关注用户已发布的博文（公开、未隐藏）"""
        from core.models.follow import Follow
        following_ids = db_session.session.execute(
            select(Follow.following_id).where(Follow.follower_id == user_id)
        ).scalars().all()

        if not following_ids:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "pages": 0}

        query = Post.query.filter(
            Post.author_id.in_(following_ids),
            Post.status == "published",
            Post.is_hidden == 0
        ).order_by(Post.published_at.desc())

        total = query.count()
        posts = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [p.to_dict(include_category=True, include_author=True) for p in posts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def create_post(
        author_id: int,
        title: str,
        content: str,
        summary: str = None,
        category_id: int = None,
        cover_image_id: int = None,
        status: str = "draft",
    ) -> dict:
        """创建文章"""
        if category_id:
            if not Category.query.get(category_id):
                raise ValueError("分类不存在")

        if cover_image_id:
            f = File.query.get(cover_image_id)
            if not f or f.user_id != author_id:
                raise ValueError("封面图文件不存在或不属于您")

        if status not in ["draft", "published", "archived"]:
            status = "draft"

        post = Post(
            title=title,
            content=content,
            summary=summary,
            category_id=category_id,
            cover_image_id=cover_image_id,
            author_id=author_id,
            status=status,
        )

        if status == "published":
            post.published_at = datetime.utcnow()

        db_session.session.add(post)
        db_session.session.commit()

        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def update_post(post_id: int, operator_id: int, **kwargs) -> dict:
        """更新文章"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        from core.models.user import User
        operator = db_session.session.get(User, operator_id)
        if not operator:
            raise ValueError("操作者不存在")

        # 仅作者、admin 或 root 可修改
        if not (operator.is_root or operator.is_admin or post.author_id == operator_id):
            raise PermissionError("没有权限更新此文章")

        updatable_fields = ["title", "content", "summary", "category_id", "cover_image_id", "status"]

        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                if field == "category_id" and kwargs[field]:
                    if not Category.query.get(kwargs[field]):
                        raise ValueError("分类不存在")
                if field == "status" and kwargs[field] not in ["draft", "published", "archived"]:
                    raise ValueError("无效的状态值")
                if field == "cover_image_id" and kwargs[field]:
                    f = File.query.get(kwargs[field])
                    if not f or f.user_id != post.author_id:
                        raise ValueError("封面图文件不存在或不属于作者")
                setattr(post, field, kwargs[field])

        db_session.session.commit()
        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def publish_post(post_id: int, operator_id: int) -> dict:
        """发布博文（仅作者）"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        if post.author_id != operator_id:
            raise PermissionError("只有作者可以发布博文")

        if post.status == "published":
            return post.to_dict(include_category=True, include_author=True)

        post.status = "published"
        post.published_at = datetime.utcnow()
        db_session.session.commit()

        # 异步通知粉丝（失败静默）
        try:
            from core.models.follow import Follow
            from core.services.notification_service import notification_service
            follower_ids = db_session.session.execute(
                select(Follow.follower_id).where(Follow.following_id == operator_id)
            ).scalars().all()
            for fid in follower_ids:
                notification_service.create(
                    user_id=fid,
                    type_='new_post',
                    actor_id=operator_id,
                    target_id=post_id,
                    extra={'post_title': post.title}
                )
        except Exception:
            pass

        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def delete_post(post_id: int, operator_id: int) -> None:
        """删除文章"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        from core.models.user import User
        operator = db_session.session.get(User, operator_id)
        if not operator:
            raise ValueError("操作者不存在")

        if not (operator.is_root or operator.is_admin or post.author_id == operator_id):
            raise PermissionError("没有权限删除此文章")

        db_session.session.delete(post)
        db_session.session.commit()

    # ============================================================
    # 附件管理
    # ============================================================

    @staticmethod
    def add_attachment(post_id: int, file_id: int, operator_id: int) -> dict:
        """添加附件（博文和文件都必须属于 operator）"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")
        if post.author_id != operator_id:
            raise PermissionError("只有作者可以管理附件")

        f = File.query.get(file_id)
        if not f:
            raise ValueError("文件不存在")
        if f.user_id != operator_id:
            raise PermissionError("文件不属于您")

        # 检查是否已存在
        existing = db_session.session.execute(
            select(PostAttachment).where(
                PostAttachment.post_id == post_id,
                PostAttachment.file_id == file_id
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("该文件已是附件")

        # 计算 sort_order
        max_order = db_session.session.execute(
            select(func.max(PostAttachment.sort_order)).where(PostAttachment.post_id == post_id)
        ).scalar() or 0

        pa = PostAttachment(post_id=post_id, file_id=file_id, sort_order=max_order + 1)
        db_session.session.add(pa)
        db_session.session.commit()
        db_session.session.refresh(pa)
        return pa.to_dict()

    @staticmethod
    def remove_attachment(post_id: int, file_id: int, operator_id: int) -> None:
        """移除附件"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")
        if post.author_id != operator_id:
            raise PermissionError("只有作者可以管理附件")

        pa = db_session.session.execute(
            select(PostAttachment).where(
                PostAttachment.post_id == post_id,
                PostAttachment.file_id == file_id
            )
        ).scalar_one_or_none()
        if not pa:
            raise ValueError("附件不存在")

        db_session.session.delete(pa)
        db_session.session.commit()

    @staticmethod
    def get_attachment_file(post_id: int, file_id: int) -> File:
        """获取附件对应的 File 对象（校验附件属于该博文）"""
        pa = db_session.session.execute(
            select(PostAttachment).where(
                PostAttachment.post_id == post_id,
                PostAttachment.file_id == file_id
            )
        ).scalar_one_or_none()
        if not pa:
            raise ValueError("附件不存在")
        return pa.file

    @staticmethod
    def get_attachments(post_id: int) -> list:
        """获取博文附件列表"""
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")
        return [pa.to_dict() for pa in (post.attachments or [])]
