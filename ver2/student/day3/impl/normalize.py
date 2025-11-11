# -*- coding: utf-8 -*-
"""
raw → GovNotice 표준 스키마 정규화 (강사용/답지)
- fetchers.py에서 온 Day1형 raw 결과를 GovNotice 필드로 매핑
- URL 중복 제거
"""
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime
import re

DATE_FMTS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%dT%H:%M:%S%z")

_BUDGET_RX = re.compile(r"(예산|추정\s*가격|계약\s*금액)\s*[:：]?\s*([\d,]+)\s*(원|KRW)?")
_AGENCY_RX = re.compile(r"(발주처|수요기관|주관기관|기관)\s*[:：]?\s*([^\n\r]+)")
_DEADLINE_RX = re.compile(r"(마감|제출\s*마감|접수\s*마감)\s*[:：]?\s*([0-9]{4}[.\-/년][0-9]{1,2}[.\-/월]?[0-9]{1,2})")
_DATE_CLEAN_RX = re.compile(r"[년./-]")

DATE_PAT = re.compile(r"(접수\s*마감|제출\s*마감|마감)\s*[:\-]?\s*(\d{4}[./-]\d{1,2}[./-]\d{1,2})")
WON_PAT  = re.compile(r"(예산|사업비|추정가격)\s*[:\-]?\s*([0-9,]+)\s*(원|억원|천만|백만)")
CERT_PAT = re.compile(r"(GS\s*인증|ISO\s*9?0?0?1|정보보안관리체계|ISMS|조달우수|성능인증|벤처인증)")


def _parse_int(s: str | None) -> int | None:
    if not s: return None
    try:
        return int(re.sub(r"[^\d]", "", s))
    except Exception:
        return None

def _parse_date(d: str | None) -> str | None:
    if not d: return None
    ds = _DATE_CLEAN_RX.sub("-", d).replace("--", "-")
    parts = [p for p in ds.split("-") if p]
    # YYYY-MM-DD 형태로 정규화 시도
    try:
        if len(parts) == 3:
            y = int(parts[0]); m = int(parts[1]); day = int(parts[2])
            return datetime(y, m, day).strftime("%Y-%m-%d")
    except Exception:
        return None
    return None

def normalize_notice(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    입력: {"id","title","body","meta":{...}}
    출력: {"id","title","body","meta":{"budget","agency","deadline",...}}
    """
    nid = raw.get("id")
    title = (raw.get("title") or "").strip()
    body = raw.get("body") or ""
    meta = dict(raw.get("meta") or {})

    # 예산
    bud = None
    mb = _BUDGET_RX.search(body)
    if mb:
        bud = _parse_int(mb.group(2))

    # 기관
    agency = None
    ma = _AGENCY_RX.search(body)
    if ma:
        agency = ma.group(2).strip()

    # 마감일
    deadline = None
    md = _DEADLINE_RX.search(body)
    if md:
        deadline = _parse_date(md.group(2))

    meta.update({
        "budget": bud,
        "agency": agency,
        "deadline": deadline,
        "source": meta.get("source", "unknown")
    })

    return {
        "id": nid,
        "title": title or "무제 공고",
        "body": body,
        "meta": meta
    }

def _as_date_iso(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    for fmt in DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            continue
    # 숫자 8자리(YYYYMMDD) 대응
    if s.isdigit() and len(s) == 8:
        try:
            return datetime.strptime(s, "%Y%m%d").date().isoformat()
        except Exception:
            pass
    return ""


def normalize_all(raw_items: List[Dict]) -> List[Dict]:
    norm: List[Dict] = []
    for r in raw_items or []:
        # Day1 웹결과 스키마: title/url/source/snippet/date
        title = (r.get("title") or "").strip()
        url = (r.get("url") or "").strip()
        source = (r.get("source") or "").strip().lower()
        snippet = (r.get("snippet") or "").strip()
        date_guess = _as_date_iso(r.get("date") or "")

        norm.append({
            "title": title,
            "url": url,
            "source": "nipa" if "nipa" in source else ("bizinfo" if "bizinfo" in source else "web"),
            "agency": "",
            "announce_date": date_guess,   # 알 수 없으면 빈 값
            "close_date": "",              # 랭커에서 없을 경우 패널티
            "budget": "",
            "snippet": snippet,
            "attachments": [],
            "content_type": "notice",
            "score": 0.0,
        })

    # URL 기준 중복 제거
    seen = set()
    deduped = []
    for n in norm:
        u = n["url"]
        if not u or u in seen:
            continue
        seen.add(u)
        deduped.append(n)
    return deduped

def parse_date(s: str) -> str | None:
    s = s.replace(".", "-").replace("/", "-")
    try:
        # YYYY-MM-DD만 처리 (간단)
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        return None

def extract_fields(html_or_text: str) -> dict:
    text = html_or_text
    deadline = None
    m = DATE_PAT.search(text)
    if m:
        deadline = parse_date(m.group(2)) or m.group(2)

    budget = None
    m2 = WON_PAT.search(text)
    if m2:
        amount = m2.group(2).replace(",", "")
        unit = m2.group(3)
        budget = f"{amount}{unit}"

    certs = list({m.group(0) for m in CERT_PAT.finditer(text)})

    return {"deadline": deadline, "budget": budget, "required_certs": certs}

def normalize_notice(raw: dict) -> dict:
    """
    raw = {"title","url","agency","raw_snippet","raw_html"} ...
    """
    base = {
        "title": raw.get("title","").strip(),
        "url": raw.get("url","").strip(),
        "agency": raw.get("agency"),
        "source": raw.get("source","web"),
        "summary": raw.get("raw_snippet","").strip(),
    }
    # 본문 원문이 있다면 추출
    body = raw.get("raw_html") or raw.get("raw_text") or ""
    extra = extract_fields(base["summary"] + "\n" + body)
    base.update(extra)
    return base