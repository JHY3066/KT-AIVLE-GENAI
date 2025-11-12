# -*- coding: utf-8 -*-
"""
Day3: 정부사업 공고 에이전트
- 역할: 사용자 질의를 받아 Day3 본체(impl/agent.py)의 Day3Agent.handle을 호출
- 결과를 writer로 표/요약 마크다운으로 렌더 → 파일 저장(envelope 포함) → LlmResponse 반환
- 이 파일은 의도적으로 '구현 없음' 상태입니다. TODO만 보고 직접 채우세요.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path

from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

# Day3 본체
from student.day3.impl.agent import Day3Agent
# 공용 렌더/저장/스키마
from student.common.fs_utils import save_markdown
from student.common.writer import render_day3, render_enveloped
from student.common.schemas import Day3Plan
from .impl.pipeline import run_pipeline
from student.disclosure.command import is_disclosure_command, handle_disclosure_command


# ------------------------------------------------------------------------------
# TODO[DAY3-A-01] 모델 선택:
#  - 경량 LLM 식별자를 정해 MODEL에 넣으세요. (예: "openai/gpt-4o-mini")
#  - LiteLlm(model=...) 형태로 초기화합니다.
# ------------------------------------------------------------------------------
MODEL = LiteLlm(model="openai/gpt-4o-mini")  # <- LiteLlm(...)


# ------------------------------------------------------------------------------
# TODO[DAY3-A-02] _handle(query):
#  요구사항
#   1) Day3Plan 인스턴스를 만든다. (필요 시 소스별 topk / 웹 폴백 여부 등 지정)
#      - 예: Day3Plan(nipa_topk=3, bizinfo_topk=2, web_topk=2, use_web_fallback=True)
#   2) Day3Agent 인스턴스를 만든다. (외부 키는 본체에서 환경변수로 접근)
#   3) agent.handle(query, plan)을 호출해 payload(dict)를 반환한다.
#  반환 형태(예):
#   {"type":"gov_notices","query":"...", "items":[{title, url, deadline, agency, ...}, ...]}
# ------------------------------------------------------------------------------
def _handle(query: str) -> Dict[str, Any]:
    # 여기에 구현
    plan = Day3Plan(
        nipa_topk=3,
        bizinfo_topk=2,
        web_topk=2,
        use_web_fallback=True,
    )
    agent = Day3Agent()
    return agent.handle(query, plan)

# ------------------------------------------------------------------------------
# TODO[DAY3-A-03] before_model_callback:
#  요구사항
#   1) llm_request에서 사용자 최근 메시지를 찾아 query 텍스트를 꺼낸다.
#   2) _handle(query)로 payload를 만든다.
#   3) writer로 본문 MD를 만든다: render_day3(query, payload)
#   4) 파일 저장: save_markdown(query=query, route='day3', markdown=본문MD)
#   5) envelope로 감싸기: render_enveloped(kind='day3', query=query, payload=payload, saved_path=경로)
#   6) LlmResponse로 최종 마크다운을 반환한다.
#  예외 처리
#   - try/except로 감싸고, 실패 시 "Day3 에러: {e}" 형식의 짧은 메시지로 반환
# ------------------------------------------------------------------------------
def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
    **kwargs,
) -> Optional[LlmResponse]:
    # 여기에 구현
    try:
        if not llm_request.contents:
            raise ValueError("요청에 내용이 없습니다.")
        last = llm_request.contents[-1]
        if getattr(last, "role", None) != "user":
            raise ValueError("마지막 메시지가 user가 아닙니다.")
        if not getattr(last, "parts", None) or not getattr(last.parts[0], "text", None):
            raise ValueError("텍스트 파트를 찾을 수 없습니다.")
        query = last.parts[0].text.strip()

        payload = _handle(query)
        body_md = render_day3(query, payload)
        saved = save_markdown(query=query, route="day3", markdown=body_md)
        md = render_enveloped(kind="day3", query=query, payload=payload, saved_path=saved)

        return LlmResponse(content=types.Content(parts=[types.Part(text=md)], role="model"))
    except Exception as e:
        msg = f"Day3 에러: {e}"
        return LlmResponse(content=types.Content(parts=[types.Part(text=msg)], role="model"))


# ------------------------------------------------------------------------------
# TODO[DAY3-A-04] 에이전트 메타데이터:
#  - name/description/instruction 문구를 명확하게 다듬으세요.
#  - MODEL은 위 TODO[DAY3-A-01]에서 설정한 LiteLlm 인스턴스를 사용합니다.
# ------------------------------------------------------------------------------
day3_gov_agent = Agent(
    name="Day3GovAgent",                        # <- 필요 시 수정
    model=MODEL,                                # <- TODO[DAY3-A-01]에서 설정
    description="정부사업 공고/바우처 정보 수집 및 표 제공",   # <- 필요 시 수정
    instruction="질의를 기반으로 정부/공공 포털에서 관련 공고를 수집하고 표로 요약해라.",
    tools=[],
    before_model_callback=before_model_callback,
)

def load_company_docs(base_dir: str) -> List[Dict]:
    # data/processed에 요약된 내부 문서를 단순 로딩(필요 시 커스텀)
    p = Path(base_dir)
    docs = []
    for f in p.glob("*.md"):
        docs.append({"id": f.stem, "text": f.read_text(encoding="utf-8"), "tags": ["processed"]})
    return docs

def main(query: str,
         data_processed_dir: str = "data/processed",
         index_dir: str = "indices/day3"):
    docs = load_company_docs(data_processed_dir)
    result = run_pipeline(query=query, company_docs=docs, index_dir=index_dir)
    return result

if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="검색 키워드")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--index", default="indices/day3")
    args = ap.parse_args()
    print(json.dumps(main(args.q, args.processed, args.index), ensure_ascii=False, indent=2))

_LAST_DAY3_RESULT: Dict[str, Any] | None = None

def handle_user_text(user_text: str) -> Dict[str, Any]:
    global _LAST_DAY3_RESULT
    # 1) 커맨드면: 기존 결과 있으면 바로 사용, 없으면 일단 검색부터
    if is_disclosure_command(user_text):
        if not _LAST_DAY3_RESULT:
            # 기본 쿼리로 당일 인기 키워드 혹은 최근 사용 쿼리를 넣어도 됨
            agent = Day3Agent(tavily_api_key=None)
            _LAST_DAY3_RESULT = agent.handle(query="관광 상품 개발 지원", plan=None)
        return handle_disclosure_command(user_text, _LAST_DAY3_RESULT)

    # 2) 일반 쿼리면: Day3 검색 수행 → 결과 캐시 저장 후 반환
    agent = Day3Agent(tavily_api_key=None)
    res = agent.handle(query=user_text, plan=None)
    _LAST_DAY3_RESULT = res
    return res