from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class EsgReport(Base):
    __tablename__ = "esg_report"
    __table_args__ = (UniqueConstraint("company_id", "report_year", name="uq_esg_report_company_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("esg_company.company_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    report_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    landing_page_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    verification_date: Mapped[str] = mapped_column(String(10), nullable=False)

    company: Mapped["EsgCompany"] = relationship(back_populates="reports")
