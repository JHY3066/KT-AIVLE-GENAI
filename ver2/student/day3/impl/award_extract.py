# student/day3/impl/award_extract.py
from typing import Dict

def extract_award_info(notice: Dict) -> Dict:
    """
    notice: {"id","title","body","meta":{...}}
    return: {"criteria": [...], "weights": {...}, "budget": int|None, "agency": str|None}
    """
    body = (notice.get("body") or "")
    meta = notice.get("meta", {})
    out = {
        "criteria": [],
        "weights": {},
        "budget": meta.get("budget"),
        "agency": meta.get("agency"),
    }
    # 규칙기반 예: '평가항목', '배점', '정량/정성' 키워드
    if "배점" in body or "평가항목" in body:
        out["criteria"].extend(["사업이해도","수행계획","인력/조직","유사실적"])
        out["weights"].update({"수행계획":40, "유사실적":30})
    return out
