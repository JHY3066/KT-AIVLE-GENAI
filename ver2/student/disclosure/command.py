# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from datetime import date
from student.disclosure.agent import open_ticket
from student.common.fs_utils import save_markdown

TRIGGER_PAT = re.compile(r"(정보공개\s*청구서\s*생성|정보공개청구서\s*생성)", re.IGNORECASE)

def is_disclosure_command(text: str) -> bool:
    return bool(TRIGGER_PAT.search(text or ""))

def _find_target_item(items: List[Dict[str, Any]], user_text: str) -> Optional[Dict[str, Any]]:
    """user_text에 포함된 키워드로 title/agency 부분매칭 → 없으면 Top-1"""
    if not items:
        return None
    # 제목/기관 키워드 추출(따옴표 안 우선, 없으면 띄어쓰기 기준 1~3 토큰)
    m = re.findall(r"\"([^\"]+)\"", user_text)
    if not m:
        toks = [t for t in re.split(r"\s+", user_text) if len(t) >= 2]
        m = [" ".join(toks[:3])] if toks else []
    if m:
        key = m[0]
        for it in items:
            t = (it.get("title") or "") + " " + (it.get("agency") or "")
            if key and key.lower() in t.lower():
                return it
    # fallback: 1순위(랭킹 상위)
    return items[0]

def generate_disclosure_for_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """기존 버튼 플로우를 함수화: 티켓 생성 + MD 저장 경로 반환"""
    agency = item.get("agency", "")
    project = item.get("title", "")
    period_from = (item.get("decision_date") or item.get("deadline") or date.today().isoformat())
    period_to   = (item.get("decision_date") or item.get("deadline") or date.today().isoformat())
    ticket = open_ticket(agency=agency, project_title=project,
                         period_from=period_from, period_to=period_to)
    saved_path = save_markdown(query=project, route="disclosure", markdown=ticket.request_text_md)
    return {"ticket": ticket, "saved_path": saved_path}

def handle_disclosure_command(user_text: str, day3_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    day3_payload 예시: {"items":[{... 정규화 결과 ...}, ...], ...}
    """
    items = day3_payload.get("items") or day3_payload.get("recommendations") or []
    target = _find_target_item(items, user_text)
    if not target:
        return {"ok": False, "message": "생성할 대상을 찾지 못했습니다. 먼저 공고 검색/랭킹을 수행하세요."}
    out = generate_disclosure_for_item(target)
    return {
        "ok": True,
        "message": f"정보공개 청구서 초안을 생성했습니다: {out['saved_path']}",
        "saved_path": out["saved_path"],
        "ticket": out["ticket"].__dict__,
        "target": {"title": target.get("title"), "agency": target.get("agency")},
    }
