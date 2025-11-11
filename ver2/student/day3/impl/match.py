# student/day3/impl/match.py
from typing import List, Dict
from student.common.vectorstore import get_store

def score_tenders(company_docs: List[Dict], notices: List[Dict], index_dir: str) -> List[Dict]:
    """
    company_docs: [{"id":..., "text":..., "tags":[...]}]
    notices:      [{"id":..., "title":..., "body":..., "meta":{...}}]
    return:       [{"notice_id":..., "score": float, "reasons":[...]}]
    """
    store = get_store(index_dir)
    # 1) 회사 문서 인덱싱
    for d in company_docs:
        store.add_document(doc_id=d["id"], text=d["text"], meta={"tags": d.get("tags", [])})
    store.save()
    # 2) 공고 본문으로 질의 → 상위 매칭 스코어 취합(간단 버전)
    results = []
    for n in notices:
        hits = store.search(query_text=(n.get("title","") + "\n" + n.get("body",""))[:5000], k=5)
        score = sum(h["score"] for h in hits) / max(1, len(hits))
        reasons = [f'{h["doc_id"]}:{round(h["score"],3)}' for h in hits]
        results.append({"notice_id": n["id"], "score": float(score), "reasons": reasons})
    # 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
