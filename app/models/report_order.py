from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ReportOrder(Base):
    __tablename__ = "report_order"
    __table_args__ = (
        UniqueConstraint("payment_id", name="uq_report_order_payment_id"),
        CheckConstraint("status IN ('PENDING', 'PAID', 'FAILED')", name="ck_report_order_status"),
        Index("uq_report_order_paid_entitlement", "user_id", "report_id", unique=True, sqlite_where=text("status = 'PAID'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.idx", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("esg_report.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_krw: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="PENDING")

    report: Mapped["EsgReport"] = relationship()
