"""
[tool/rag_retriever.py]
개념: Qdrant 기반 RAG(벡터 검색) 도구 인터페이스 및 Stub
기능:
  - RagResult            : RAG 검색 결과 단건의 기대 타입 정의
  - get_rag_retriever_tool() : LangChain Tool 객체 반환
  연결 대상: Qdrant Docker Container (기본 localhost:6333)
  교체: 다른 팀 구현체 완성 시 이 함수 내부만 교체

[다른 팀을 위한 기대 출력 타입 — RagResult]
  doc_id   : str   — Qdrant 내 문서 고유 ID (step 2 DB 연동 시 활용)
  content  : str   — 청크 원문 텍스트 (ResourceItem.raw_content 로 연결)
  source   : str   — PDF 파일명 또는 원본 URL (ResourceItem.source_url 로 연결)
  score    : float — 코사인 유사도 점수 (0~1)
  metadata : dict  — 추가 메타 정보 (page_number, section, document_title 등)
"""

from typing import TypedDict
from langchain_core.tools import tool
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, RAG_TOP_K


class RagResult(TypedDict):
    """
    RAG 검색 단건 결과 기대 타입.
    다른 팀 구현 시 이 스키마를 준수해야 함.
    """
    doc_id:   str    # Qdrant 문서 ID → step 2 DB 관리 키
    content:  str    # 청크 원문 → ResourceItem.raw_content
    source:   str    # 출처 파일명/URL → ResourceItem.source_url
    score:    float  # 유사도 점수 (0~1)
    metadata: dict   # page_number, section, document_title 등


def get_rag_retriever_tool(top_k: int = RAG_TOP_K):
    """
    Qdrant 기반 RAG LangChain Tool 반환.
    Docker 컨테이너 미실행 시 연결 실패를 안전하게 처리하고 빈 결과 반환.
    """
    # Qdrant 연결 및 vectorstore 초기화 (모듈 로드 시 1회 시도)
    _vectorstore = None
    try:
        from qdrant_client import QdrantClient
        from langchain_qdrant import QdrantVectorStore
        from langchain_openai import OpenAIEmbeddings

        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=5)
        _client.get_collections()   # 연결 확인 (실패 시 예외 발생)

        _vectorstore = QdrantVectorStore(
            client=_client,
            collection_name=QDRANT_COLLECTION,
            embedding=OpenAIEmbeddings(),
        )
        print(f"[RAG] Qdrant 연결 성공 — {QDRANT_HOST}:{QDRANT_PORT}/{QDRANT_COLLECTION}")

    except Exception as e:
        # Docker 미실행 등 연결 실패: 경고만 출력하고 stub 모드로 동작
        print(f"[RAG WARNING] Qdrant 연결 실패 ({e}). RAG 검색은 빈 결과를 반환합니다.")

    @tool
    def rag_search(query: str) -> str:
        """
        배터리 산업 관련 내부 문서(PDF 보고서, 리서치 자료)에서 관련 정보를 검색합니다.
        Qdrant 벡터 DB에서 쿼리와 가장 유사한 문서 청크를 반환합니다.
        """
        if _vectorstore is None:
            return "[RAG] Qdrant 미연결 — 내부 문서 검색 결과 없음. 웹 검색 결과를 활용하세요."

        results = _vectorstore.similarity_search_with_score(query, k=top_k)

        if not results:
            return "관련 내부 문서를 찾지 못했습니다."

        parts = []
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            page   = doc.metadata.get("page_number", "")
            parts.append(
                f"[출처: {source}{f' p.{page}' if page else ''}] "
                f"[유사도: {score:.3f}]\n{doc.page_content}"
            )

        return "\n\n---\n\n".join(parts)

    return rag_search
