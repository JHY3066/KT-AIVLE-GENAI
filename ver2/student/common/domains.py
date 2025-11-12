# -*- coding: utf-8 -*-
import re
from urllib.parse import urlparse

# ▶ 정부·공공 포털 중심 화이트리스트 (필요 시 추가)
WHITELIST_DAY3 = [
    "www.bizinfo.go.kr",     # 기업마당
    "www.g2b.go.kr",         # 나라장터(메인)
    "www.pps.go.kr",         # 조달청
    "www.kostat.go.kr",      # 통계청(보도자료 등 필요 시)
    # 지자체/공공기관 도메인 패턴(예: seoul.go.kr, busan.go.kr, gangwon.go.kr, ...):
    # 도메인 전체 나열이 어렵다면 패턴 허용(아래 REGEX_WHITELIST 참조)
]

# ▶ 와일드카드/패턴 허용(지자체·산하기관)
REGEX_WHITELIST = [
    r".*\.go\.kr$",          # 모든 정부/지자체(예: seoul.go.kr)
    r".*\.or\.kr$",          # 공공·비영리 법인(관광재단 등)
    r".*\.re\.kr$",          # 공공 연구기관
]

_WHITELIST_RE = [re.compile(p) for p in REGEX_WHITELIST]

def is_allowed_domain(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc in {d.lower() for d in WHITELIST_DAY3}:
            return True
        return any(r.match(netloc) for r in _WHITELIST_RE)
    except Exception:
        return False

def filter_allowed_urls(urls):
    return [u for u in urls if is_allowed_domain(u)]
