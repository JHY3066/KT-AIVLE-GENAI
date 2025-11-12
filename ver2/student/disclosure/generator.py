TEMPLATE = """# 정보공개 청구서(초안)
기관: {agency}
사업명: {project}
기간: {period_from} ~ {period_to}

청구 내용:
1) 평가결과 총괄표(평가항목·배점·위원별 점수 합산)
2) 우선협상대상자 선정사유 요약 또는 회의록(가능 범위 내)
3) 계약서(개인정보·영업비밀은 가림 처리된 부분공개 요청)

청구 목적: 제안서 개선 및 이의신청 대비(법률상 정당한 목적)
비공개 우려: 관련 항목은 부분공개(마스킹) 처리 요청
"""

def build_disclosure_request(agency, project, period_from, period_to):
    return TEMPLATE.format(agency=agency, project=project, period_from=period_from, period_to=period_to)
