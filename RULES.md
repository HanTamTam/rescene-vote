# 📜 RESCENE 프로젝트 AI 어시스턴트 대화 및 운영 규칙 (RULES)

> **💡 본 문서의 목적**  
> 사용자와 대화하거나 작업을 수행할 때 AI 어시스턴트가 **반드시 준수해야 하는 핵심 원칙**과, **상황별로 어떤 문서를 가장 먼저 확인해야 하는지(문서 라우팅 규칙)**를 정의한 기준 문서입니다.  
> 세션이 새로 시작되거나 대화가 압축(Compaction)되더라도, 본 문서를 가장 먼저 읽고 맥락을 이어갑니다. 새로운 규칙은 생각날 때마다 지속해서 추가됩니다.

---

## 1. 상황별 문서 참조 규칙 (어떨 때 어떤 문서를 볼 것인가?)

AI 어시스턴트는 사용자의 요청이나 상황에 따라 아래 매핑 규칙에 맞춰 해당 문서를 즉시 열람하고 작업을 진행합니다.

| 상황 및 사용자 요청 | 가장 먼저 참고할 문서 | 핵심 확인 내용 |
| :--- | :--- | :--- |
| **"오늘 워크플로 확인해줘"**<br>**"오늘 오류내역 검사해줘"**<br>**"오늘 머지된 거 점검해줘"** | [**`DAILY_OPS_GUIDE.md`**](file:///Users/hanchangmin/Documents/Rescene/DAILY_OPS_GUIDE.md) | 5단계 일일 점검 SOP 실행 (`daily_audit.py` 가동, 404 깨진 링크 및 중복 카드 자동 수정, 재검증 후 깃 반영) |
| **프로젝트 구조 파악**<br>**데이터 스키마 및 카드 추가**<br>**자동화 파이프라인/권한 확인** | [**`HANDOVER.md`**](file:///Users/hanchangmin/Documents/Rescene/HANDOVER.md) | `voteCardsData` 규격, FxTwitter 크롤링 엔진 원리, GitHub Actions 설정 및 로컬 개발 환경 가이드 |
| **과거 오류 해결 내역 확인**<br>**동일 문제 재발 방지 검토** | [**`WORK_HISTORY.md`**](file:///Users/hanchangmin/Documents/Rescene/WORK_HISTORY.md) | 트위터 차단 우회 히스토리, LiNC 딥링크 404 가짜오류 해결법, 워크플로 중단 방지 패치 기록 |
| **최근 자동 테스트 결과 확인**<br>**현재 대시보드 상태 진단** | [**`qa_report.md`**](file:///Users/hanchangmin/Documents/Rescene/qa_report.md) | 가장 최근 실행된 DOM 무결성, JS 문법, 39개 버튼 링크 전수 검사 결과 및 통과/경고/실패 판정 |
| **연합 투표 지침 및 공지 원문 확인** | [**`mma_alliance_voting_notice.md`**](file:///Users/hanchangmin/Documents/Rescene/mma_alliance_voting_notice.md) | 음원총공팀 공식 수집 공지 원문, 연합 대상 아이돌 리스트 및 투표 규칙 아카이브 |

---

## 2. 작업 및 대화 시 무조건 준수해야 하는 절대 규칙

1. **이중 HTML 파일 100% 동기화 (Double Mirroring)**  
   - `index.html`을 수정할 때는 반드시 [`rescene_voting_schedule.html`](file:///Users/hanchangmin/Documents/Rescene/rescene_voting_schedule.html)에도 100% 동일하게 반영한다.
2. **LiNC 인기가요 공식 직행 딥링크 보존**  
   - 인기가요 메인 버튼에는 반드시 `https://app.linc.fan/31TL/UPBjE3DC`를 유지하며, 봇 차단(404/403) 경고가 떠도 임의로 스토어 링크로 바꾸지 않는다.
3. **검증 통과(PASS) 후 결과 보고**  
   - 코드를 수정했을 때는 반드시 `python3 scripts/test_dashboard.py`를 실행하여 실패가 0건인지 확인한 후 사용자에게 완료 보고를 한다.
4. **결과 보고는 핵심 위주로 명확하게**  
   - 작업 후 보고는 군더더기 없이 **[1. 점검 내역 / 2. 발견된 문제 / 3. 수정 및 배포 결과]** 위주로 읽기 쉽게 요약한다.
5. **작업 시작 전 관련 문서 및 히스토리 사전 검토 (Pre-Work Context Check)**  
   - 코드를 수정하거나 작업을 시작하기 전, 반드시 관련 문서([`HANDOVER.md`](file:///Users/hanchangmin/Documents/Rescene/HANDOVER.md), [`WORK_HISTORY.md`](file:///Users/hanchangmin/Documents/Rescene/WORK_HISTORY.md), [`DAILY_OPS_GUIDE.md`](file:///Users/hanchangmin/Documents/Rescene/DAILY_OPS_GUIDE.md) 등)를 먼저 열람하여 기존 아키텍처, 과거 해결 히스토리 및 개발 방향성을 명확히 파악한 후, 그 맥락과 일관성을 유지하는 방향으로 작업을 진행한다.
6. **코드 작업 후 문서 동기화 필수 체크 (Doc-Sync Rule)**  
   - 스크립트, HTML, 워크플로 등 코드를 하나라도 수정하거나 기능을 추가·변경할 때마다, 관련 문서에 반영할 사항이 있는지 반드시 확인하고 코드와 함께 문서를 최신화한다.

---

## 3. 추가 규칙 기록 공간 (추후 업데이트용)
* *(새로운 대화 규칙이나 요청 사항이 생길 때마다 이곳에 자유롭게 추가)*
