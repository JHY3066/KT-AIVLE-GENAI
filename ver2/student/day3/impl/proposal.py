# student/day3/impl/proposal.py
from typing import Dict, List

BASE_OUTLINE = [
    "표지/요약",
    "사업이해 및 문제정의",
    "수행 범위와 일정(WBS, 간트)",
    "기술/데이터 아키텍처",
    "조직/역할/PM 계획",
    "유사실적 및 레퍼런스",
    "예산 및 산출물",
    "위험관리 및 품질보증(QA)"
]

def make_proposal_outline(notice: Dict, award_info: Dict, match_reasons: List[str]) -> Dict:
    must_docs = ["사업자등록증", "재무제표/신용평가", "유사실적 증빙", "개인정보/보안서약"]
    if award_info.get("weights", {}).get("유사실적", 0) >= 30:
        must_docs.append("실적증명원(발주처 직인)")
    return {
        "outline": BASE_OUTLINE,
        "must_attachments": must_docs,
        "tips": [
            "평가항목-배점표에 맞춰 장 제목을 동일 용어로 매핑",
            f"우리 강점 근거: {', '.join(match_reasons[:3]) if match_reasons else 'RAG 근거 정리'}"
        ]
    }
