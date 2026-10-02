from datetime import datetime

from pgvector.sqlalchemy import Vector

from ai.embeddings import EMBEDDING_DIMENSIONS

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    ForeignKey
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class Article(Base):

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
    )

    url: Mapped[str] = mapped_column(
        String(2000),
        unique=True,
        index=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(200),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        index=True,
    )

    embedding: Mapped[list | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
    )

class Story(Base):

    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    headline: Mapped[str] = mapped_column(
        String(500)
    )

    summary: Mapped[str | None] = mapped_column(
        Text
    )

    category: Mapped[str | None] = mapped_column(
        String(100)
    )

    importance: Mapped[float | None]

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # Indexed because the clustering window and the "today"
    # view filter on it.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True,
    )

    embedding: Mapped[list | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS)
    )

class StoryArticle(Base):

    __tablename__ = "story_articles"

    story_id: Mapped[int] = mapped_column(
        ForeignKey("stories.id"),
        primary_key=True,
    )

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id"),
        primary_key=True,
    )

    similarity: Mapped[float]
    

class StoryMergeRejection(Base):
    """
    Story pairs the LLM judged to be different events, so
    the merge step doesn't ask about them again.
    """

    __tablename__ = "story_merge_rejections"

    story_a: Mapped[int] = mapped_column(
        primary_key=True,
    )

    story_b: Mapped[int] = mapped_column(
        primary_key=True,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
