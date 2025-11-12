# -*- coding: utf-8 -*-
"""
정부/공공 포털 및 일반 웹에서 '사업 공고'를 찾기 위한 검색 래퍼

설계 포인트
- '도메인 제한' + '키워드 보강'을 동시에 사용해 노이즈를 줄입니다.
- Tavily Search API를 통해 결과를 가져오며, 결과 스키마는 Day1 web 결과와 동일한 단순 형태를 사용합니다.
- 여기선 '검색'만 담당합니다. 정규화/랭킹은 normalize.py / rank.py에서 수행합니다.

권장 쿼리 전략
- NIPA(정보통신산업진흥원):  site:nipa.kr  +  ("공고" OR "모집" OR "지원")
- Bizinfo(기업마당):       site:bizinfo.go.kr + 유사 키워드
- 일반 웹(Fallback):       쿼리 + "모집 공고 지원 사업" 같은 보조 키워드로 recall 확보
"""
from __future__ import annotations
from urllib.parse import urlparse
from .normalize import normalize_notice

from typing import List, Dict, Any, Optional
import os
# Day1에서 제작한 Tavily 래퍼를 사용합니다.
from student.day1.impl.tavily_client import search_tavily 
from student.common.domains import is_allowed_domain, filter_allowed_urls, WHITELIST_DAY3

# 기본 설정값
DEFAULT_TOPK = 7
DEFAULT_TIMEOUT = 20

# 기본 TopK(권장: NIPA 3, Bizinfo 2, Web 2)
NIPA_TOPK = 3
BIZINFO_TOPK = 2
WEB_TOPK = 2

def fetch_nipa(query: str, topk: int = NIPA_TOPK) -> List[Dict[str, Any]]:
    """
    NIPA 도메인에 한정한 사업 공고 검색.
    - include_domains=["nipa.kr"] 힌트를 주고, 검색 쿼리에도 site:nipa.kr을 붙입니다.
    - '공고/모집/지원' 같은 키워드로 사업 공고 문서를 우선 노출시킵니다.
    
    반환: Day1 Web 스키마 리스트 [{title, url, content/snippet, ...}, ...]
    """
    # api_key = os.getenv("TAVILY_API_KEY", "")
    
    search_query = f"{query} 공고 모집 지원 site:nipa.kr"

    results = search_tavily(
        query=search_query,
        top_k=topk,
        timeout=DEFAULT_TIMEOUT,
        include_domains=["nipa.kr"]
    )
    
    return results

    # TODO[DAY3-F-01]:
    # 1) os.getenv("TAVILY_API_KEY","")로 키를 읽습니다.
    # 2) 질의 q를 만들 때: f"{query} 공고 모집 지원 site:nipa.kr"
    # 3) search_tavily(q, key, top_k=topk, timeout=DEFAULT_TIMEOUT, include_domains=["nipa.kr"])
    # 4) 그대로 반환

def fetch_bizinfo(query: str, topk: int = BIZINFO_TOPK) -> List[Dict[str, Any]]:
    """
    Bizinfo(기업마당) 도메인에 한정한 사업 공고 검색
    - include_domains=["bizinfo.go.kr"]
    - '공고/모집/지원' 키워드 보강
    """

    search_query = f"{query} 공고 모집 지원 site:bizinfo.go.kr"
    
    # search_tavily를 사용하여 bizinfo.go.kr 도메인으로 한정 검색
    # top_k=topk, timeout=DEFAULT_TIMEOUT, include_domains=["bizinfo.go.kr"]
    results = search_tavily(
        query=search_query,
        top_k=topk,
        timeout=DEFAULT_TIMEOUT,
        include_domains=["bizinfo.go.kr"]
    )

    return results

    # TODO[DAY3-F-02]:
    # 위 NIPA와 동일한 패턴이며, site:bizinfo.go.kr / include_domains=["bizinfo.go.kr"] 를 사용

def fetch_web(query: str, topk: int = WEB_TOPK) -> List[Dict[str, Any]]:
    """
    일반 웹 Fallback: 사업 공고와 관련된 키워드를 넣어 Recall 확보
    - 도메인 제한 없이 Tavily 기본 검색 사용
    - 가짜/홍보성 페이지 노이즈는 뒤 단계(normalize/rank)에서 걸러냅니다.
    """
    # TODO[DAY3-F-03]:
    # 1) 키 읽기
    # 2) q = f"{query} 모집 공고 지원 사업"
    # 3) search_tavily(q, key, top_k=topk, timeout=DEFAULT_TIMEOUT)
    try:
        # 1) API 키 읽기
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            print("[fetch_web] Warning: TAVILY_API_KEY not set")
            return []
        
        # 2) 사업 공고 관련 키워드를 추가한 쿼리 생성
        q = f"{query} 모집 공고 지원 사업"
        
        # 3) Tavily 검색 호출 (도메인 제한 없음)
        results = search_tavily(
            q, 
            api_key, 
            top_k=topk, 
            timeout=DEFAULT_TIMEOUT
        )
        
        return results
    
    except Exception as e:
        print(f"[fetch_web] Error during web search: {e}")
        return []

def fetch_all(query: str) -> List[Dict[str, Any]]:
    """
    편의 함수: 현재 설정된 전 소스에서 가져오기
    주의) 실전에서는 소스별 topk를 plan을 통해 주입받아야 합니다.
    """
    # TODO[DAY3-F-04]:
    # - 위 세 함수를 순서대로 호출해 리스트를 이어붙여 반환
    # - 실패 시 빈 리스트라도 반환(try/except로 유연 처리 가능)
    all_results = []
    
    try:
        # NIPA 검색
        print(f"[fetch_all] Fetching from NIPA...")
        nipa_results = fetch_nipa(query, topk=NIPA_TOPK)
        all_results.extend(nipa_results)
        print(f"[fetch_all] NIPA: {len(nipa_results)} results")
    except Exception as e:
        print(f"[fetch_all] NIPA search failed: {e}")
    
    try:
        # Bizinfo 검색
        print(f"[fetch_all] Fetching from Bizinfo...")
        bizinfo_results = fetch_bizinfo(query, topk=BIZINFO_TOPK)
        all_results.extend(bizinfo_results)
        print(f"[fetch_all] Bizinfo: {len(bizinfo_results)} results")
    except Exception as e:
        print(f"[fetch_all] Bizinfo search failed: {e}")
    
    try:
        # 일반 웹 검색
        print(f"[fetch_all] Fetching from Web...")
        web_results = fetch_web(query, topk=WEB_TOPK)
        all_results.extend(web_results)
        print(f"[fetch_all] Web: {len(web_results)} results")
    except Exception as e:
        print(f"[fetch_all] Web search failed: {e}")
    
    print(f"[fetch_all] Total results: {len(all_results)}")
    return all_results

ALLOW_DOMAINS = [
    "www.g2b.go.kr",           # 나라장터(로그인 페이지 제외, 크롤링은 요약용 메타)
    "www PPS go kr".replace(" ",".").lower(),  # (프록시/미러 고려시 추가)
    "www.pps.go.kr",
    "www.korea.kr",
    "www.mois.go.kr", "www.mcst.go.kr", "www.kto.or.kr",
    "www.seoul.go.kr", "www.seoul tourism or kr".replace(" ",".").lower(),
    "www.innopolis.or.kr", "www.nipa.kr", "www.iitp.kr",
    "www.keiti.re.kr", "www.kisa.or.kr", "www.kisa.re.kr",
    "www.koreaedufair.or.kr", "www.mss.go.kr",
]

DENY_KEYWORDS = ["채용", "채용공고", "구인", "구직", "경력", "신입", "잡코리아", "사람인", "원티드", "로켓펀치", "잡플래닛"]
DENY_DOMAINS = ["jobkorea.co.kr", "saramin.co.kr", "wanted.co.kr", "rocketpunch.com", "jobplanet.co.kr"]

QUERY_TEMPLATES = [
    "{topic} 입찰 공고",
    "{topic} 제안요청서",
    "{topic} RFP",
    "{topic} 용역 공고",
    "{topic} 위탁 사업 공고",
    "{topic} 지원사업 공고",
]

def is_allowed(url: str) -> bool:
    host = urlparse(url).hostname or ""
    if any(d in host for d in DENY_DOMAINS):
        return False
    return any(host.endswith(d) for d in ALLOW_DOMAINS)

def looks_like_job_posting(text: str) -> bool:
    return any(k in text for k in DENY_KEYWORDS)

def company_topics(company: Dict) -> List[str]:
    caps = company.get("capabilities", {})
    topics = (caps.get("domains", []) or []) + (caps.get("solutions", []) or []) + (company.get("keywords") or [])
    # 과도한 회사명 일치 방지: 회사명 제거
    name = (company.get("company_name") or "").replace("주식회사","").replace("(주)","").strip()
    topics = [t for t in topics if name not in t]
    # 짧은 토픽/일반어 제거
    return [t for t in topics if len(t) >= 2 and t not in ["AI", "데이터", "솔루션"]]

def search_notices(web_search, company_profile: Dict, limit=30) -> List[Dict]:
    results = []
    for topic in company_topics(company_profile)[:6]:  # 과다 호출 방지
        for tpl in QUERY_TEMPLATES:
            q = tpl.format(topic=topic)
            hits = web_search(q, num=10, lang="ko")  # <-- 네가 쓰는 web_search 래퍼 시그니처에 맞춰 조정
            for h in hits:
                if not is_allowed(h["url"]): 
                    continue
                title = (h.get("title") or "") + " " + (h.get("snippet") or "")
                if looks_like_job_posting(title):
                    continue
                results.append({
                    "source": "web",
                    "title": h.get("title") or "",
                    "url": h["url"],
                    "agency": guess_agency(h["url"]),
                    "raw_snippet": h.get("snippet") or "",
                })
    # 중복 URL 제거
    seen, dedup = set(), []
    for r in results:
        if r["url"] in seen: 
            continue
        seen.add(r["url"]); dedup.append(r)
    return dedup[:limit]

def guess_agency(url: str) -> str:
    host = urlparse(url).hostname or ""
    if "g2b.go.kr" in host: return "나라장터"
    if "mois.go.kr" in host: return "행정안전부"
    if "mcst.go.kr" in host: return "문화체육관광부"
    if "kto.or.kr" in host: return "한국관광공사"
    if "seoul.go.kr" in host: return "서울특별시"
    return host

def fetch_by_web(query: str, api_key: str, top_k: int = 10) -> list[dict]:
    """
    Day3 웹 보강용 검색. 반드시 화이트리스트 도메인만 허용.
    """
    items = []
    results = search_tavily(
        query,
        api_key,
        top_k=top_k,
        timeout=20,
        include_domains=WHITELIST_DAY3,  # ▶ 화이트리스트 강제
        exclude_domains=None,
    ) or []

    for r in results:
        url = r.get("url") or r.get("link") or ""
        if not is_allowed_domain(url):
            continue  # ▶ 추가 방어
        items.append({
            "title": r.get("title") or "",
            "url": url,
            "snippet": r.get("content") or r.get("snippet") or "",
            "source": "web",
        })
    return items