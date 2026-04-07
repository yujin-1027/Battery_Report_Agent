# Battery Report Agent

글로벌 배터리 시장 구조 변화 속 LG에너지솔루션 vs CATL 전략 비교 보고서를 자동 생성하는 AI Agent.

## 실행 방법

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env
# .env 에 API 키 입력 (OPENAI_API_KEY, TAVILY_API_KEY 필수)
```

### 2. 의존성 설치 (uv)

```bash
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Qdrant Docker 실행 (RAG 사용 시)

```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

> Qdrant 없이 실행해도 됩니다. 웹 검색(Tavily)만으로 동작합니다.

### 4. 에이전트 실행

```bash
python main.py
```

또는 코드에서 직접 호출:

```python
from main import run_battery_report

report = run_battery_report(
    "LG에너지솔루션과 CATL의 전략을 비교 분석해주세요.",
    session_id="my-session-001"   # 생략 시 새 세션 자동 생성
)
```

최종 보고서는 `output/battery_report_{session_id}_{timestamp}.md` 에 저장됩니다.

## 코드 검토 순서

1. `config.py` — 전역 상수 및 환경 변수
2. `state.py` — BatteryReportState, ResourceItem 타입 정의
3. `tool/web_search.py`, `tool/rag_retriever.py` — 도구 인터페이스
4. `memory/memory_manager.py` — 세션 메모리 로드/저장
5. `prompt/*.py` — 각 에이전트 프롬프트
6. `agent/query_agent.py` — 쿼리 파싱 노드
7. `agent/market_agent.py` — 산업 동향 서브 그래프
8. `agent/lg_agent.py`, `agent/catl_agent.py` — 기업 분석 노드
9. `agent/report_agent.py` — Aggregator + 보고서 작성 + 품질 검사
10. `agent/supervisor_agent.py` — Supervisor + 강제 종료 노드
11. `graph.py` — 전체 그래프 조립
12. `main.py` — 실행 진입점
