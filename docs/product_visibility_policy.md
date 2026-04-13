# Product Visibility Policy

문서 상태: implementation-ready draft
기준 문서:
- `docs/product_api_contract_draft.md`
- `docs/product_authorization_matrix.md`
- `docs/product_team_project_domain.md`

## 1. 문서 목적

이 문서는 제품 레이어에서 어떤 정보를 누구에게 어디까지 보여줄지 고정하기 위한 가시성 정책 문서다.

핵심 목적:
- 권한 정책과 조회 정책을 분리해 명확히 한다.
- member가 볼 수 있는 협업용 정보와 제한 공개 정보의 경계를 고정한다.
- 다음 단계 DB/API/UI 설계에서 화면별 공개 범위가 흔들리지 않도록 한다.

---

## 2. 제품 포지션

이 서비스는 `협업 보조형 기여도 검증 툴`이다.

의미:
- 팀과 프로젝트 안에서 누가 어떤 작업을 진행했고 어떤 제출이 있었는지 협업 관점에서 볼 수 있어야 한다.
- 동시에 평가 상세, bonus 승인 이력, 운영 예외 정보까지 모두에게 무제한 공개하는 제품은 아니다.

즉, 이 서비스는:
- 협업 가시성은 높게 유지
- 민감 평가 정보는 제한 공개

라는 방향을 기본값으로 둔다.

---

## 3. 가시성 레벨 정의

제품 1차 가시성 레벨은 아래 4단계로 고정한다.

## 3.1 My View

본인 작업 중심 화면.

대상:
- 현재 사용자 본인의 task와 제출 흐름

## 3.2 Project Overview View

프로젝트 전체 협업 요약 화면.

대상:
- 프로젝트 멤버 전체에게 공개 가능한 협업용 정보

## 3.3 Project Sensitive Review View

프로젝트 내부의 민감 검토 정보 화면.

대상:
- manager / owner 중심

## 3.4 Admin/Owner Exception View

운영 예외와 복구 정보까지 포함한 상위 뷰.

대상:
- owner 또는 운영 관리자

---

## 4. 기본 공개 원칙

최소 공개 권장안:
- member도 프로젝트 전체 요약, 담당자, `work_status`, 제출 여부, 제출물 공유 범위 내 본문은 볼 수 있다.
- AI 질문/답변/평가 상세/bonus 승인 이력/운영 메모는 제한 공개 가능 항목이다.

핵심 기준:
- 협업에 필요한 정보는 overview에 포함할 수 있다.
- 평가와 운영의 민감 정보는 sensitive review 또는 exception view로 올린다.

---

## 5. 제출물 공개 정책

제출물 공개 원칙:
- 협업용 제출물은 프로젝트 멤버에게 보이게 한다.
- 평가 세부정보는 제한 공개한다.

실무 해석:
- `submission_content`, `submission_note`는 프로젝트 멤버에게 공개 가능한 기본 후보
- `ai_question`, `user_answer`, `ai_comment`, `raw_score`, `provisional_score`는 민감도에 따라 제한 공개

제품 1차 권장:
- 본문은 overview 또는 task 상세에서 공개 가능
- AI 질문/답변/세부 평가는 manager review 계층에서 우선 공개

---

## 6. 점수 공개 정책

## 6.1 대시보드 공개 항목

프로젝트 멤버 공통 대시보드 또는 overview에서 공개 가능한 항목 예시:
- task 수
- 진행 상태 요약
- 제출 여부
- 승인 여부

주의:
- 상세 점수 잠금 이력이나 bonus 상세 이력은 기본 overview 공개 대상이 아니다.

## 6.2 민감 점수 상세 항목

민감 상세 예시:
- `locked_main_score` 상세 승인 맥락
- `total_delta_bonus`의 구성 상세
- bonus 승인 사유 상세
- 평가 코멘트와 점수 근거

이 정보는 기본적으로 `Project Sensitive Review View` 이상에서 다룬다.

---

## 7. 역할별 / 화면별 공개 범위 표

| 화면/정보 | owner | manager | member | 비고 |
|---|---:|---:|---:|---|
| My View | Y | Y | Y | 본인 task 중심 |
| Project Overview View | Y | Y | Y | 협업용 요약 공개 |
| Project Sensitive Review View | Y | Y | N | 민감 평가/점수/운영 정보 |
| Admin/Owner Exception View | Y | N | N | 운영 예외, reopen/cancel 복구 맥락 |
| 제출물 본문 | Y | Y | Y | 프로젝트 멤버 공유 범위 |
| AI 질문/답변 | Y | Y | N/C | 기본은 제한 공개, 필요 시 정책 완화 가능 |
| 평가 상세 코멘트 | Y | Y | N | 민감 평가 정보 |
| locked main score 상세 승인 이력 | Y | Y | N | 민감 점수 상세 |
| delta bonus 승인 이력 상세 | Y | Y | N | 민감 운영 정보 |
| manager 내부 메모 | Y | Y | N | 내부 운영 메모 |
| reopen / cancel 운영 이력 | Y | Y | N | 예외 운영 정보 |

`N/C` 해석:
- 기본값은 `N`
- 프로젝트 정책상 제한 완화가 필요할 때만 일부 공개 가능

---

## 8. 화면 연결

## 8.1 내 작업 화면

기본 역할:
- 첫 진입 화면
- 본인 task, 제출 상태, answer 필요 여부, retry 가능 여부 중심

공개 원칙:
- My View 중심
- 필요한 경우 본인 관련 민감 정보 일부 표시 가능

## 8.2 프로젝트 전체 화면

기본 역할:
- 협업 진행 현황 파악
- 필터/검색 기반 탐색

공개 원칙:
- Project Overview View 중심
- 과도한 세부 평가보다는 상태와 제출 흐름 위주

## 8.3 Task 상세 화면

기본 역할:
- 특정 task의 제출 이력, 상태, 공유 가능한 본문 확인

공개 원칙:
- 프로젝트 멤버는 submission 본문 중심
- manager/owner는 필요 시 민감 평가 상세까지 확장

## 8.4 Manager Review 화면

기본 역할:
- 승인, 보완 요청, 민감 평가 확인, bonus 판단

공개 원칙:
- Project Sensitive Review View 중심

---

## 9. 기본 UX 원칙

- 첫 진입은 `내 작업` 화면으로 한다.
- 프로젝트 전체 화면은 필터/검색 기반으로 제공한다.
- 과도한 정보 노출보다 역할별 요약 중심으로 설계한다.
- member에게는 협업용 overview를 충분히 보여주되 민감 평가 상세는 기본적으로 숨긴다.

---

## 10. 문서 간 정합성 규칙

이 문서는 authorization matrix와 모순 없이 아래 기준을 확정한다.

- member는 overview를 볼 수 있다.
- member는 민감 평가 상세를 기본적으로 볼 수 없다.
- manager와 owner는 sensitive review 정보를 볼 수 있다.
- owner는 운영 예외 정보까지 포함한 exception view에 접근할 수 있다.

---

## 11. 구현 메모

- API는 `view=overview`, `view=my`, `view=sensitive-review` 같은 조회 계층을 지원하는 방향이 적합하다.
- UI는 한 화면에서 모든 정보를 다 보여주기보다 뷰 계층을 나눠 노출한다.
- DB에서는 가시성 정책 자체를 별도 테이블로 분리하지 않아도, API 응답 직렬화 계층에서 우선 통제 가능하다.

---

## 12. 연결 문구

이 문서는 아래 문서들과 직접 연결된다.

- `product_db_schema_draft`: 어떤 필드가 민감 정보인지, 어떤 필드가 overview에 노출 가능한지 해석 기준을 제공한다.
- `product_api_contract_draft`: `view=overview`, `view=my`, `view=sensitive-review`, `activity-logs` 조회 계층의 제품적 의미를 제공한다.
- `product_authorization_matrix`: member overview 허용, sensitive review 제한이라는 권한/가시성 정합성을 확정한다.
