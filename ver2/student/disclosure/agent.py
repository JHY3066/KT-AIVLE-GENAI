# -*- coding: utf-8 -*-
from __future__ import annotations
import uuid, datetime
from typing import Optional
from student.common.schemas import DisclosureTicket
from .generator import build_disclosure_request

def open_ticket(
    agency: str,
    project_title: str,
    period_from: str,
    period_to: str,
    portal_link: Optional[str] = None,
    status: str = "submitted",
) -> DisclosureTicket:
    """
    정보공개 청구서 초안을 만들고, 내부 티켓(상태/기한) 객체를 반환합니다.
    실제 제출/추적은 UI나 별도 저장 로직에서 처리하세요.
    """
    # 법정 처리기한(접수 기준 10일) - 여기서는 편의상 period_to+10일로 산정
    due = (
        datetime.date.fromisoformat(period_to) + datetime.timedelta(days=10)
    ).isoformat()
    md = build_disclosure_request(agency, project_title, period_from, period_to)
    return DisclosureTicket(
        id=str(uuid.uuid4()),
        agency=agency,
        project_title=project_title,
        period_from=period_from,
        period_to=period_to,
        status=status,
        request_text_md=md,
        links=[portal_link] if portal_link else [],
        due_date=due,
    )
