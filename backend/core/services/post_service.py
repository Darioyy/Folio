"""
文章服务层 - 业务逻辑
"""

from sqlalchemy import or_
from core.models.post import Post
from core.models.category import Category
from core.utils.permissions import can_modify_user
from db.session import db as db_session


class PostService:
    """文章服务类"""

    @staticmethod
    def get_posts(
        page: int = 1,
        limit: int = 10,
        status: str = "all",
        category_id: int = None,
        search: str = "",
    ) -> dict:
        """
        获取文章列表（分页、筛选、搜索）

        Args:
            page: 页码
            limit: 每页数量
            status: 状态筛选 (all/draft/published/archived)
            category_id: 分类ID筛选
            search: 搜索关键词

        Returns:
            dict: 包含 items 和 pagination 的字典
        """
        # 构建查询
        query = Post.query

        # 状态筛选
        if status and status != "all":
            query = query.filter(Post.status == status)

        # 分类筛选
        if category_id:
            query = query.filter(Post.category_id == category_id)

        # 搜索（标题或内容）
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(Post.title.like(search_pattern), Post.content.like(search_pattern))
            )

        # 按创建时间倒序
        query = query.order_by(Post.created_at.desc())

        # 分页
        total = query.count()
        offset = (page - 1) * limit
        posts = query.offset(offset).limit(limit).all()

        # 转换为字典（包含关联数据）
        items = []
        for post in posts:
            post_dict = post.to_dict(include_category=True, include_author=True)
            items.append(post_dict)

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
    def get_post_by_id(post_id: int, increment_view: bool = True) -> dict:
        """
        获取文章详情

        Args:
            post_id: 文章ID
            increment_view: 是否增加浏览次数

        Returns:
            dict: 文章数据

        Raises:
            ValueError: 文章不存在
        """
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        # 增加浏览次数
        if increment_view:
            post.view_count += 1
            db_session.session.commit()

        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def create_post(
        author_id: int,
        title: str,
        content: str,
        summary: str = None,
        category_id: int = None,
        status: str = "draft",
    ) -> dict:
        """
        创建文章

        Args:
            author_id: 作者ID
            title: 文章标题
            content: 文章内容
            summary: 文章摘要
            category_id: 分类ID
            status: 文章状态

        Returns:
            dict: 新创建的文章数据
        """
        # 验证分类是否存在（如果指定了分类）
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                raise ValueError("分类不存在")

        # 验证状态值
        if status not in ["draft", "published", "archived"]:
            status = "draft"

        # 创建文章
        post = Post(
            title=title,
            content=content,
            summary=summary,
            category_id=category_id,
            author_id=author_id,
            status=status,
        )

        db_session.session.add(post)
        db_session.session.commit()

        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def update_post(post_id: int, operator_id: int, **kwargs) -> dict:
        """
        更新文章

        Args:
            post_id: 文章ID
            operator_id: 操作者ID
            **kwargs: 要更新的字段

        Returns:
            dict: 更新后的文章数据

        Raises:
            ValueError: 文章不存在或无权限
        """
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        # 权限检查：只有管理员或文章作者可以更新
        if not can_modify_user(operator_id, post.author_id, allow_admin=True):
            raise ValueError("没有权限更新此文章")

        # 可更新字段
        updatable_fields = ["title", "content", "summary", "category_id", "status"]

        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                # 验证分类是否存在
                if field == "category_id" and kwargs[field]:
                    category = Category.query.get(kwargs[field])
                    if not category:
                        raise ValueError("分类不存在")

                # 验证状态值
                if field == "status" and kwargs[field] not in [
                    "draft",
                    "published",
                    "archived",
                ]:
                    raise ValueError("无效的状态值")

                setattr(post, field, kwargs[field])

        db_session.session.commit()

        return post.to_dict(include_category=True, include_author=True)

    @staticmethod
    def delete_post(post_id: int, operator_id: int) -> None:
        """
        删除文章

        Args:
            post_id: 文章ID
            operator_id: 操作者ID

        Raises:
            ValueError: 文章不存在或无权限
        """
        post = Post.query.get(post_id)
        if not post:
            raise ValueError("文章不存在")

        # 权限检查：只有管理员或文章作者可以删除
        if not can_modify_user(operator_id, post.author_id, allow_admin=True):
            raise ValueError("没有权限删除此文章")

        db_session.session.delete(post)
        db_session.session.commit()
