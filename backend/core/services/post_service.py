"""
文章服务层 - 业务逻辑
"""

from datetime import datetime
from sqlalchemy import or_, and_, select, func, update, case
from sqlalchemy.orm import joinedload
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
        needs_review: bool = False,
    ) -> dict:
        """获取文章列表（分页、筛选、搜索、排序）"""
        conditions = []

        if status and status != "all":
            conditions.append(Post.status == status)

        # 公开列表过滤管理员隐藏的博文；管理员视图可见所有
        if status == 'published' and not admin_view:
            conditions.append(Post.is_hidden == 0)

        if category_id:
            conditions.append(Post.category_id == category_id)

        if author_id:
            conditions.append(Post.author_id == author_id)

        if needs_review:
            conditions.append(
                or_(Post.is_hidden == 1, Post.review_status != 'none', Post.report_count > 0)
            )

        if search:
            search = search[:100]
            try:
                from sqlalchemy import text as _text
                # 优先用 FULLTEXT 全文索引（需已建 idx_posts_fulltext）
                ft_ids = db_session.session.execute(
                    _text(
                        "SELECT id FROM posts"
                        " WHERE MATCH(title, content) AGAINST(:q IN BOOLEAN MODE)"
                        " LIMIT 200"
                    ),
                    {"q": search}
                ).scalars().all()
                conditions.append(Post.id.in_(ft_ids))
            except Exception:
                # FULLTEXT 索引未就绪时降级为 LIKE
                search_pattern = f"%{search}%"
                conditions.append(
                    or_(Post.title.like(search_pattern), Post.content.like(search_pattern))
                )

        if needs_review:
            # 审核视图：未处理举报(0) → 申诉待审(1) → 历史记录(2)，组内按举报次数倒序
            urgency = case(
                (and_(Post.report_count > 0, Post.is_hidden == 0, Post.review_status == 'none'), 0),
                (Post.review_status == 'pending', 1),
                else_=2
            )
            order = [urgency, Post.report_count.desc(), Post.created_at.desc()]
        elif sort == "hot":
            # 加权热门算法：点赞*2 + 收藏*3 + 评论*1.5 + 浏览*0.1，近7天内发布的帖子有1.5x加成
            # 置顶帖子始终优先
            recency_bonus = case(
                (func.datediff(func.now(), Post.published_at) <= 7, 1.5),
                else_=1.0
            )
            hot_score = (
                Post.like_count * 2.0 +
                Post.collect_count * 3.0 +
                Post.comment_count * 1.5 +
                Post.view_count * 0.1
            ) * recency_bonus
            order = [Post.is_pinned.desc(), hot_score.desc()]
        else:
            order = [Post.is_pinned.desc(), Post.created_at.desc()]

        total = db_session.session.execute(
            select(func.count(Post.id)).where(*conditions)
        ).scalar() or 0

        posts = db_session.session.execute(
            select(Post)
            .options(joinedload(Post.author), joinedload(Post.category))
            .where(*conditions)
            .order_by(*order)
            .offset((page - 1) * limit)
            .limit(limit)
        ).scalars().all()

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
        conditions = [Post.author_id == author_id]
        if status and status != "all":
            conditions.append(Post.status == status)

        total = db_session.session.execute(
            select(func.count(Post.id)).where(*conditions)
        ).scalar() or 0

        posts = db_session.session.execute(
            select(Post)
            .options(joinedload(Post.category))
            .where(*conditions)
            .order_by(Post.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

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

        conditions = [
            Post.author_id == user.id,
            Post.status == "published",
            Post.is_hidden == 0,
        ]

        total = db_session.session.execute(
            select(func.count(Post.id)).where(*conditions)
        ).scalar() or 0

        posts = db_session.session.execute(
            select(Post)
            .options(joinedload(Post.author), joinedload(Post.category))
            .where(*conditions)
            .order_by(Post.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return {
            "items": [p.to_dict(include_category=True, include_author=True) for p in posts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_post_by_id(post_id: int, increment_view: bool = True, viewer_key: str = None,
                       viewer_id: int = None, is_admin: bool = False) -> dict:
        """获取文章详情（SQL 层过滤：公开博文任何人可访问，非公开仅作者/管理员可访问）"""
        # 先尝试公开博文（SQL 层过滤，杜绝草稿/隐藏博文泄露）
        post = db_session.session.execute(
            select(Post).where(
                Post.id == post_id,
                Post.status == 'published',
                Post.is_hidden == 0,
            )
        ).scalar_one_or_none()

        if not post:
            # 非公开博文：仅作者或管理员可访问；故意返回 404 不泄露存在性
            if viewer_id:
                candidate = db_session.session.execute(
                    select(Post).where(Post.id == post_id)
                ).scalar_one_or_none()
                if candidate and (candidate.author_id == viewer_id or is_admin):
                    post = candidate
            if not post:
                raise ValueError("文章不存在")
            # 非公开博文不统计浏览量
            increment_view = False

        if increment_view:
            if viewer_key:
                # 去重：每用户每天只计一次
                try:
                    from core.models.post_view import PostView
                    from datetime import date
                    today = date.today()
                    existing = db_session.session.execute(
                        select(PostView).where(
                            PostView.post_id == post_id,
                            PostView.viewer_key == viewer_key,
                            PostView.viewed_date == today,
                        )
                    ).scalar_one_or_none()
                    if not existing:
                        pv = PostView(post_id=post_id, viewer_key=viewer_key, viewed_date=today)
                        db_session.session.add(pv)
                        # P2: 原子 SQL 更新，防并发竞争
                        db_session.session.execute(
                            update(Post).where(Post.id == post_id).values(
                                view_count=Post.view_count + 1
                            )
                        )
                        db_session.session.commit()
                        db_session.session.refresh(post)
                except Exception:
                    # 表不存在时降级到原子更新
                    db_session.session.execute(
                        update(Post).where(Post.id == post_id).values(
                            view_count=Post.view_count + 1
                        )
                    )
                    db_session.session.commit()
                    db_session.session.refresh(post)
            else:
                # P2: 原子 SQL 更新，防并发竞争
                db_session.session.execute(
                    update(Post).where(Post.id == post_id).values(
                        view_count=Post.view_count + 1
                    )
                )
                db_session.session.commit()
                db_session.session.refresh(post)

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

        conditions = [
            Post.author_id.in_(following_ids),
            Post.status == "published",
            Post.is_hidden == 0,
        ]

        total = db_session.session.execute(
            select(func.count(Post.id)).where(*conditions)
        ).scalar() or 0

        posts = db_session.session.execute(
            select(Post)
            .options(joinedload(Post.author), joinedload(Post.category))
            .where(*conditions)
            .order_by(Post.published_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

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
            if not db_session.session.get(Category, category_id):
                raise ValueError("分类不存在")

        if cover_image_id:
            f = db_session.session.get(File, cover_image_id)
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

        if not post.summary:
            post.summary = post._auto_summary()

        if status == "published":
            post.published_at = datetime.utcnow()

        db_session.session.add(post)
        db_session.session.commit()

        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def update_post(post_id: int, operator_id: int, **kwargs) -> dict:
        """更新文章"""
        post = db_session.session.get(Post, post_id)
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
                    if not db_session.session.get(Category, kwargs[field]):
                        raise ValueError("分类不存在")
                if field == "status" and kwargs[field] not in ["draft", "published", "archived"]:
                    raise ValueError("无效的状态值")
                if field == "cover_image_id" and kwargs[field]:
                    f = db_session.session.get(File, kwargs[field])
                    if not f or f.user_id != post.author_id:
                        raise ValueError("封面图文件不存在或不属于作者")
                setattr(post, field, kwargs[field])

        # 内容变更时重算摘要（除非本次明确传入了 summary）
        if 'content' in kwargs and kwargs.get('summary') is None:
            post.summary = post._auto_summary()

        db_session.session.commit()
        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def publish_post(post_id: int, operator_id: int) -> dict:
        """发布博文（仅作者）"""
        post = db_session.session.get(Post, post_id)
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
        post = db_session.session.get(Post, post_id)
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
        post = db_session.session.get(Post, post_id)
        if not post:
            raise ValueError("文章不存在")
        if post.author_id != operator_id:
            raise PermissionError("只有作者可以管理附件")

        f = db_session.session.get(File, file_id)
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
        post = db_session.session.get(Post, post_id)
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
    def get_attachments(post_id: int, viewer_id: int = None, is_admin: bool = False) -> list:
        """获取博文附件列表（公开博文任何人可访问，非公开仅作者/管理员可访问）"""
        # SQL 层过滤：先查公开博文
        post = db_session.session.execute(
            select(Post).where(
                Post.id == post_id,
                Post.status == 'published',
                Post.is_hidden == 0,
            )
        ).scalar_one_or_none()

        if not post:
            if viewer_id:
                candidate = db_session.session.execute(
                    select(Post).where(Post.id == post_id)
                ).scalar_one_or_none()
                if candidate and (candidate.author_id == viewer_id or is_admin):
                    post = candidate
            if not post:
                raise ValueError("文章不存在")

        return [pa.to_dict() for pa in (post.attachments or [])]
