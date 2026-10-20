from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings


class PortOneConfigurationError(RuntimeError):
    pass


def require_portone_settings() -> tuple[str, str, str]:
    store_id = settings.PORTONE_STORE_ID.strip()
    channel_key = settings.PORTONE_TOSSPAYMENTS_CHANNEL_KEY.strip()
    api_secret = settings.PORTONE_API_SECRET.strip()
    if not store_id or not channel_key or not api_secret:
        raise PortOneConfigurationError("PortOne V2 설정(PORTONE_STORE_ID, PORTONE_TOSSPAYMENTS_CHANNEL_KEY, PORTONE_API_SECRET)이 필요합니다.")
    return store_id, channel_key, api_secret


def get_portone_payment(payment_id: str) -> dict:
    _, _, api_secret = require_portone_settings()
    response = httpx.get(
        f"https://api.portone.io/payments/{quote(payment_id, safe='')}",
        headers={"Authorization": f"PortOne {api_secret}"}, timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


def create_pending_order(session: Session, user_id: int, report_id: int) -> dict:
    from uuid import uuid4

    from app.models.esg_report import EsgReport
    from app.models.report_order import ReportOrder
    from app.services.esg_pricing import calculate_report_price

    report = session.get(EsgReport, report_id)
    if report is None:
        raise LookupError("보고서를 찾을 수 없습니다.")
    amount = calculate_report_price(report.page_count)
    if amount is None or not report.pdf_url:
        raise ValueError("구매 가능한 검증된 PDF 보고서가 아닙니다.")
    store_id, channel_key, _ = require_portone_settings()
    paid = session.scalar(select(ReportOrder).where(
        ReportOrder.user_id == user_id, ReportOrder.report_id == report_id, ReportOrder.status == "PAID",
    ))
    if paid:
        raise FileExistsError("이미 구매한 보고서입니다.")
    pending = session.scalar(select(ReportOrder).where(
        ReportOrder.user_id == user_id, ReportOrder.report_id == report_id, ReportOrder.status == "PENDING",
    ))
    if pending:
        order = pending
    else:
        order = ReportOrder(
            user_id=user_id, report_id=report_id, payment_id=f"esg-{uuid4()}",
            amount_krw=amount, status="PENDING",
        )
        session.add(order)
        session.commit()
    return {
        "payment_id": order.payment_id, "amount_krw": order.amount_krw,
        "currency": "KRW", "order_name": report.title,
        "store_id": store_id, "channel_key": channel_key,
    }


def complete_pending_order(session: Session, user_id: int, payment_id: str) -> dict:
    from app.models.report_order import ReportOrder

    order = session.scalar(select(ReportOrder).where(ReportOrder.payment_id == payment_id))
    if order is None or order.user_id != user_id:
        raise LookupError("주문을 찾을 수 없습니다.")
    if order.status == "PAID":
        return {"payment_id": payment_id, "status": "PAID", "report_id": order.report_id}
    payment = get_portone_payment(order.payment_id)
    amount = payment.get("amount")
    if (payment.get("id") != order.payment_id or payment.get("status") != "PAID"
            or not isinstance(amount, dict) or amount.get("total") != order.amount_krw
            or amount.get("currency") != "KRW"):
        if payment.get("status") in {"FAILED", "CANCELLED"}:
            order.status = "FAILED"
            session.commit()
        raise ValueError("결제 상태, ID 또는 금액을 확인할 수 없습니다.")
    order.status = "PAID"
    session.commit()
    return {"payment_id": payment_id, "status": "PAID", "report_id": order.report_id}
