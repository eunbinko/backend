from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class EsgCompany(Base):
    __tablename__ = "esg_company"

    company_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revenue_basis: Mapped[str] = mapped_column(String(24), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    revenue_krw: Mapped[int] = mapped_column(Integer, nullable=False)
    industry: Mapped[str] = mapped_column(String(120), nullable=False)
    headquarters_label: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    esg_highlights: Mapped[str] = mapped_column(Text, nullable=False)
    ranking_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    ranking_crosscheck_url: Mapped[str] = mapped_column(Text, nullable=False)
    ranking_verification_date: Mapped[str] = mapped_column(String(10), nullable=False)
    headquarters_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    headquarters_verification_date: Mapped[str] = mapped_column(String(10), nullable=False)
    esg_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    esg_verification_date: Mapped[str] = mapped_column(String(10), nullable=False)

    reports: Mapped[list["EsgReport"]] = relationship(back_populates="company", cascade="all, delete-orphan")
