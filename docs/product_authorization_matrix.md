# Product Authorization Matrix

문서 상태: implementation-ready draft
기준 문서:
- `docs/product_scoring_policy.md`
- `docs/product_state_transition_policy.md`
- `docs/product_db_schema_draft.md`
- `docs/product_api_contract_draft.md`

## 1. 문서 목적

이 문서는 제품 MVP와 다음 확장 단계에서 필요한 최소 역할별 권한 범위를 구현 직전 수준으로 고정한다.

대상 역할:
- `owner`
- `manager`
- `member`

권한 원칙:
- 최소 권한 원칙
- 기존 MVP 루프를 깨지 않고 additive하게 확장
- member는 본인 task 중심으로 작업한다
- member도 프로젝트 전체 협업용 요약 정보는 조회 가능하다
- 제출물 본문은 프로젝트 멤버에게 공개 가능한 범위로 본다
- AI 질문/답변/세부 평가 코멘트는 제한 공개 가능 항목으로 둔다
- 점수 잠금/bonus/운영 예외 정보는 관리자 계층 중심으로 둔다

---

## 2. 역할 정의

## 2.1 owner

프로젝트 운영 최상위 권한.

주요 책임:
- 프로젝트 전체 overview 및 민감 상세 조회
- 예외적 상태 복구 승인
- reopen 같은 운영 액션 수행
- manager 권한의 상위 호환 수행

## 2.2 manager

task 생성, 배정, 검토, 승인, 보완 요청, bonus 승인 책임자.

주요 책임:
- task 메타 관리
- submission 검토
- approve / request changes
- child task 승인
- delta bonus 승인

## 2.3 member

실제 수행자.

주요 책임:
- 배정된 task 수행
- submission 생성
- answer 제출
- FAILED 상태 retry 실행
- 프로젝트 전체 협업용 overview 조회

중요 원칙:
- member는 task 핵심 메타를 직접 수정하는 주체가 아니다.
- member의 실제 작업 내용 변경은 submission version으로만 관리한다.

---

## 3. 권한 표기

- `Y`: 허용
- `C`: 조건부 허용
- `N`: 불가

---

## 4. 액션별 권한 매트릭스

| 액션 | owner | manager | member | 조건/비고 |
|---|---:|---:|---:|---|
| task 생성 | Y | Y | N | member self-draft는 제품 1차 범위 밖 |
| task 메타 수정 | Y | Y | N | 제목, 설명, 배정, manager, 상태 메타 중심 |
| task 조회 | Y | Y | C | member는 가시성 정책 범위 내 task 조회 |
| project overview 조회 | Y | Y | Y | 협업용 요약, 담당자, 제출 여부, 공유 범위 내 제출물 |
| project sensitive review 조회 | Y | Y | N | 잠금 점수 상세, bonus 상세, 운영 이력, 민감 평가 상세 |
| submission 생성 | Y | Y | Y | 일반적으로 assignee 중심 |
| answer 제출 | Y | Y | Y | 일반적으로 assignee 중심, `AWAITING_A`에서만 |
| retry 실행 | Y | Y | Y | `FAILED`에서만, 기본은 동일 task / 동일 submission 복구 |
| task 승인 | Y | Y | N | `evaluation_status=DONE`인 submission만 |
| 보완 요청 | Y | Y | N | `request changes` |
| close | Y | Y | N | 보통 `APPROVED` 이후 |
| cancel | Y | Y | N | 운영/관리 판단 |
| delta bonus 승인 | Y | Y | N | 승인 이후 additive 반영 |
| child task 생성 | Y | Y | N | 범위 확장 분리 |
| child task 승인 | Y | Y | N | 점수 중복 방지 목적 |
| reopen | Y | N | N | 예외 운영 액션, owner 전용 권장 |
| activity log 조회 | Y | Y | N | 제품 1차 필수 감사 로그 대상 |

---

## 5. 요청된 핵심 액션 상세 정리

## 5.1 task 생성

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 가능 |
| manager | Y | 기본 생성 주체 |
| member | N | 제품 1차 비허용 권장 |

## 5.2 task 승인

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 예외 운영 포함 상위 권한 |
| manager | Y | 기본 승인 주체 |
| member | N | 점수 잠금 권한 없음 |

## 5.3 보완 요청

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 가능 |
| manager | Y | 기본 주체 |
| member | N | self-review 불가 |

## 5.4 delta bonus 승인

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 가능 |
| manager | Y | 기본 주체 |
| member | N | 점수 승인권 없음 |

## 5.5 child task 승인

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 가능 |
| manager | Y | 기본 주체 |
| member | N | 범위 확장 판단 권한 없음 |

## 5.6 retry 실행

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 운영 개입 가능 |
| manager | Y | 지원 목적 개입 가능 |
| member | Y | 기본 수행자, `FAILED` 상태에서만 |

## 5.7 project overview 조회

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 전체 overview 가능 |
| manager | Y | 관리 범위 overview 가능 |
| member | Y | 협업용 overview 조회 가능 |

포함 가능한 정보 예시:
- task 제목
- 담당자
- 진행 상태
- 제출 여부
- 공유 범위 내 submission 본문 또는 본문 요약

## 5.8 project sensitive review 조회

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 전체 민감 상세 가능 |
| manager | Y | 검토/운영 범위 민감 상세 가능 |
| member | N | 기본 비허용 |

민감 상세 예시:
- locked main score 상세 승인 이력
- delta bonus 승인 이력 상세
- reopen / cancel 운영 이력
- manager 내부 메모
- AI 질문/답변/세부 평가 코멘트

## 5.9 reopen

| 역할 | 허용 | 설명 |
|---|---:|---|
| owner | Y | 예외 복구 전용 |
| manager | N | 초안 기준 비허용 권장 |
| member | N | 비허용 |

reopen을 owner 전용으로 두는 이유:
- 잠긴 점수 정합성에 직접 영향
- 잘못된 매핑/승인 복구는 운영 감사가 필요
- 일반 manager 플로우와 분리해야 정책 남용을 줄일 수 있음

---

## 6. 상태 기반 권한 보정

같은 액션이라도 상태에 따라 추가 제한이 필요하다.

| 액션 | 필수 상태 조건 |
|---|---|
| submission 생성 | `work_status IN (IN_PROGRESS, CHANGES_REQUESTED)` |
| answer 제출 | `evaluation_status = AWAITING_A` |
| retry 실행 | `evaluation_status = FAILED` |
| task 승인 | `work_status = SUBMITTED_FOR_REVIEW` 그리고 대상 submission `evaluation_status = DONE` |
| 보완 요청 | `work_status = SUBMITTED_FOR_REVIEW` |
| close | `work_status = APPROVED` |
| cancel | `work_status IN (DRAFT, ASSIGNED, IN_PROGRESS)` 권장 |
| delta bonus 승인 | `score_lock_status IN (LOCKED, LOCKED_WITH_BONUS)` |
| reopen | `work_status IN (APPROVED, CLOSED)` 권장 |

즉, 권한 체크는 아래 2단계로 구현한다.

1. 역할 권한 체크
2. 상태 전이 가능 여부 체크

---

## 7. 기본 권장 정책

아래 정책은 선택적 추가 정책이 아니라 기본 권장 정책으로 둔다.

- self-approval 금지
- self-bonus approval 금지
- reopen 시 사유 필수
- cancel 시 사유 필수
- approve, request changes, delta bonus 승인, close, cancel, reopen은 필수 감사 로그 대상

---

## 8. 감사 로그 정책

제품 1차에서 아래 액션은 감사 로그를 필수로 남긴다.

- approve
- request changes
- delta bonus 승인
- close
- cancel
- reopen

감사 로그에는 최소 아래 정보가 포함되어야 한다.
- actor
- task
- 관련 submission
- 상태 전이 전/후
- 수행 시각
- 사유 또는 메타데이터

---

## 9. 구현 권장 사항

### 9.1 API 레벨

- 모든 변경 API는 역할과 상태를 함께 검증한다.
- `403 FORBIDDEN`과 `409 INVALID_STATE_TRANSITION`을 분리한다.
- overview 조회와 sensitive review 조회를 별도 권한으로 분리한다.

### 9.2 UI 레벨

- 허용되지 않은 액션 버튼은 숨기거나 비활성화한다.
- member 화면에서는 overview 중심 정보와 본인 작업 액션을 우선 노출한다.
- 민감 평가 상세와 운영 이력은 manager/owner 뷰에서만 노출한다.

### 9.3 데이터 가시성

- member는 본인 task 중심으로 작업한다.
- member도 프로젝트 전체의 협업용 요약 정보는 조회 가능하다.
- submission 본문은 프로젝트 멤버에게 공개 가능한 범위로 본다.
- AI 질문/답변/세부 평가 코멘트는 제한 공개 가능 항목으로 둔다.
- 점수 잠금, bonus, 운영 예외 정보는 관리자 계층 중심으로 둔다.

---

## 10. 결론

이 권한 매트릭스는 owner, manager, member의 최소 역할만으로도 현재 MVP와 다음 단계 확장을 모두 감당할 수 있도록 정리되었다.

핵심은 다음 두 가지다.
- 제출과 평가 루프는 member 중심으로 유지
- 승인, 점수 잠금, bonus, 운영 예외, 민감 상세 조회는 manager/owner 권한으로 분리
