# student/day3/impl/competitor.py
import re
from typing import Dict, List

COMPANY_RX = re.compile(r"(주식회사|㈜)?\s?[가-힣A-Za-z0-9&\.\- ]{2,30}(?:기술|정보|시스템|솔루션|랩|랩스|테크|컴퍼니)?")

def extract_competitors(notice_body: str, extra_texts: List[str] | None=None) -> List[Dict]:
    pool = [notice_body] + (extra_texts or [])
    names: dict[str,int] = {}
    for text in pool:
        for m in COMPANY_RX.findall(text or ""):
            name = normalize_company(m)
            if len(name) < 2: 
                continue
            names[name] = names.get(name, 0) + 1
    # 간단 랭킹
    return [{"name": n, "mentions": c} for n, c in sorted(names.items(), key=lambda x:x[1], reverse=True)[:10]]

def normalize_company(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    s = s.replace("주식회사", "").replace("㈜", "").strip(" ()·,.")
    return s.upper()
