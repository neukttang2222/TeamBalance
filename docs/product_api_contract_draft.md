# Product API Contract Draft

문서 상태: implementation-ready draft
기준 문서:
- `docs/product_scoring_policy.md`
- `docs/product_state_transition_policy.md`
- `docs/product_db_schema_draft.md`

## 1. 문서 목적

이 문서는 task 단위 API와 submission version 단위 API를 분리하여, 기존 MVP의 `submit / answer / retry` 흐름을 유지하면서도 version 구조에 맞게 확장된 API 계약 고정 초안을 정의한다.

대원칙:
- 기존 MVP 핵심 루프를 깨지 않는다.
- 기존 검증 완료된 `submit / answer / retry` 엔드포인트는 버전 구조로 확장 또는 래핑하는 방식으로 유지한다.
- 기존 retry 원칙인 동일 task / 동일 submission 기준 복구 우선을 유지한다.
- 전면 재설계가 아니라 additive migration을 우선한다.

---

## 2. 리소스 모델

### Task 리소스

책임:
- 업무 단위 생성/조회
- 제목, 설명, 배정, 상태, 승인 메타 관리
- 점수 잠금 메타와 집계 점수 관리

핵심 필드:
- `id`
- `project_id`
- `title`
- `description`
- `task_goal`
- `task_type`
- `task_template_id`
- `difficulty_policy_code`
- `assignee_user_id`
- `manager_user_id`
- `work_status`
- `score_lock_status`
- `base_points`
- `locked_main_score`
- `total_delta_bonus`
- `approved_version_no`
- `final_contribution_score`

주의:
- task는 메타와 최종 상태의 단위다.
- 실제 작업 결과물 수정과 보완은 task update가 아니라 submission version으로 처리한다.

### Submission 리소스

책임:
- version별 제출
- AI 질문/답변/채점
- 실패/retry

핵심 필드:
- `id`
- `task_id`
- `version_no`
- `submission_content`
- `submission_note`
- `evaluation_status`
- `ai_question`
- `user_answer`
- `raw_score`
- `ai_factor`
- `provisional_score`
- `failed_stage`
- `error_message`

---

## 3. 가시성 계층

API는 최소 아래 두 단계의 조회 계층을 전제로 설계한다.

### 3.1 project overview read

협업용 프로젝트 전체 요약 조회.

member도 조회 가능해야 하는 정보 예시:
- task 제목
- 담당자
- 현재 work status
- 제출 여부
- 제출물 공유 범위 내 본문 요약 또는 본문
- 프로젝트 진행 현황 요약

### 3.2 project sensitive review read

관리자 계층 중심의 민감 상세 조회.

제한 공개 대상 예시:
- `locked_main_score` 상세 승인 이력
- delta bonus 승인 이력 상세
- reopen / cancel 운영 이력
- manager 내부 메모
- AI 질문/답변/세부 평가 코멘트 등 민감 평가 상세

---

## 4. 상태값 공통 규약

### Task 수준

`work_status`
- `DRAFT`
- `ASSIGNED`
- `IN_PROGRESS`
- `SUBMITTED_FOR_REVIEW`
- `CHANGES_REQUESTED`
- `APPROVED`
- `CLOSED`
- `CANCELED`

`score_lock_status`
- `UNLOCKED`
- `LOCKED`
- `LOCKED_WITH_BONUS`

### Submission 수준

`evaluation_status`
- `TODO`
- `GENERATING_Q`
- `AWAITING_A`
- `SCORING`
- `DONE`
- `FAILED`

---

## 5. Task 단위 API

## 5.1 Task 생성

`POST /api/projects/{projectId}/tasks`

설명:
- 새 task 생성
- 생성 직후 기본값은 보통 `work_status=DRAFT`, `score_lock_status=UNLOCKED`
- `base_points`는 요청 본문에서 직접 받지 않는다.
- 서버가 `task_type`, `task_template_id`, `difficulty_policy_code` 같은 정책 입력값을 바탕으로 계산한다.

요청 예시:

```json
{
  "title": "로그인 화면 QA 정리",
  "description": "로그인 플로우 오류 케이스를 정리한다.",
  "task_goal": "재현 가능한 QA 결과와 우선순위 정리",
  "task_type": "QA_REVIEW",
  "difficulty_policy_code": "NORMAL",
  "assignee_user_id": 101,
  "manager_user_id": 7,
  "parent_task_id": null
}
```

응답 예시:

```json
{
  "id": 501,
  "project_id": 10,
  "title": "로그인 화면 QA 정리",
  "task_type": "QA_REVIEW",
  "difficulty_policy_code": "NORMAL",
  "work_status": "DRAFT",
  "score_lock_status": "UNLOCKED",
  "base_points": 2.0,
  "locked_main_score": null,
  "total_delta_bonus": 0.0,
  "approved_version_no": null,
  "created_at": "2026-04-11T10:00:00+09:00"
}
```

추가 원칙:
- 예외적 점수 조정이 필요하면 task 생성 요청 본문에 `base_points`를 직접 받지 않는다.
- 별도 manager 전용 조정 액션 또는 정책 운영 문구로 분리한다.

## 5.2 Task 조회

`GET /api/tasks/{taskId}`

설명:
- task 메타 + 점수 집계 + 최신 submission 요약 포함
- 응답 필드는 조회 권한 계층에 따라 마스킹 가능하다.

응답 예시:

```json
{
  "id": 501,
  "project_id": 10,
  "title": "로그인 화면 QA 정리",
  "work_status": "SUBMITTED_FOR_REVIEW",
  "score_lock_status": "UNLOCKED",
  "base_points": 2.0,
  "locked_main_score": null,
  "total_delta_bonus": 0.0,
  "approved_version_no": null,
  "latest_submission": {
    "id": 9001,
    "version_no": 1,
    "evaluation_status": "AWAITING_A",
    "provisional_score": null
  }
}
```

## 5.3 Task 메타 수정

`PATCH /api/tasks/{taskId}`

설명:
- task 메타 수정 전용
- 제목, 설명, 담당자, manager, 상태 관련 메타를 다룬다.
- 작업 결과물 본문 수정, 보완 제출, 답변 변경은 이 API가 아니라 submission version API로 처리한다.

요청 예시:

```json
{
  "title": "로그인 화면 QA 정리 v2",
  "assignee_user_id": 102
}
```

## 5.4 Approve

`POST /api/tasks/{taskId}/approve`

설명:
- 특정 submission version을 승인하여 본점수를 잠근다.
- 최초 승인 시 `locked_main_score`를 설정한다.
- 감사 로그를 필수로 남긴다.

요청 예시:

```json
{
  "submission_id": 9001,
  "comment": "목표 범위를 충족하여 승인합니다."
}
```

응답 예시:

```json
{
  "task_id": 501,
  "work_status": "APPROVED",
  "score_lock_status": "LOCKED",
  "approved_version_no": 1,
  "locked_main_score": 2.2,
  "total_delta_bonus": 0.0,
  "final_contribution_score": 2.2,
  "approved_at": "2026-04-11T11:10:00+09:00"
}
```

## 5.5 Request Changes

`POST /api/tasks/{taskId}/request-changes`

설명:
- 같은 task 안에서 다음 version 제출을 요청한다.
- 본점수는 잠기지 않는다.
- 감사 로그를 필수로 남긴다.

요청 예시:

```json
{
  "submission_id": 9001,
  "reason": "오류 원인 분석이 부족하여 보완이 필요합니다."
}
```

응답 예시:

```json
{
  "task_id": 501,
  "work_status": "CHANGES_REQUESTED",
  "requested_against_submission_id": 9001,
  "message": "동일 task 내 새 version 제출이 가능합니다."
}
```

## 5.6 Close

`POST /api/tasks/{taskId}/close`

설명:
- 승인 완료 후 업무를 최종 종료한다.
- 감사 로그를 필수로 남긴다.

요청 예시:

```json
{
  "reason": "후속 작업 반영 완료, 추가 액션 없음"
}
```

응답 예시:

```json
{
  "task_id": 501,
  "work_status": "CLOSED",
  "closed_at": "2026-04-11T12:30:00+09:00"
}
```

## 5.7 Cancel

`POST /api/tasks/{taskId}/cancel`

설명:
- 중복, 무효, 범위 변경 등의 이유로 task를 취소한다.
- 감사 로그를 필수로 남긴다.

## 5.8 Delta Bonus 지급

`POST /api/tasks/{taskId}/delta-bonuses`

설명:
- 승인 이후 추가 기여에 대해 bonus를 지급한다.
- 본점수는 변경하지 않는다.
- 감사 로그를 필수로 남긴다.

요청 예시:

```json
{
  "submission_id": 9002,
  "bonus_points": 0.5,
  "reason_code": "REVISION_ACCEPTED",
  "reason_detail": "보완 요청 반영으로 QA 재현 경로와 근거 스크린샷이 추가됨"
}
```

응답 예시:

```json
{
  "task_id": 501,
  "score_lock_status": "LOCKED_WITH_BONUS",
  "locked_main_score": 2.2,
  "total_delta_bonus": 0.5,
  "final_contribution_score": 2.7
}
```

## 5.9 Reopen

`POST /api/tasks/{taskId}/reopen`

설명:
- 예외적 운영 액션
- 잘못된 승인, 잘못된 매핑, 범위판단 오류 복구에만 사용
- 감사 로그를 필수로 남긴다.

요청 예시:

```json
{
  "reason": "잘못된 task에 승인됨"
}
```

응답 예시:

```json
{
  "task_id": 501,
  "work_status": "IN_PROGRESS",
  "score_lock_status": "UNLOCKED",
  "message": "기존 잠금 점수는 감사 이력으로 보존되어야 합니다."
}
```

---

## 6. Submission version 단위 API

## 6.1 Submission 생성

`POST /api/tasks/{taskId}/submissions`

설명:
- 새 version 제출 생성
- 기존 MVP의 `submit` 액션을 version 구조로 확장한 엔드포인트
- 생성 직후 AI 질문 생성이 비동기 시작될 수 있다.
- 기존 엔드포인트를 폐기하기보다 내부적으로 이 구조로 래핑하는 방식을 우선한다.

요청 예시:

```json
{
  "submission_content": "QA 결과: 로그인 실패 시 토스트 문구와 서버 응답 정리",
  "submission_note": "1차 제출"
}
```

응답 예시:

```json
{
  "id": 9001,
  "task_id": 501,
  "version_no": 1,
  "evaluation_status": "GENERATING_Q",
  "submitted_at": "2026-04-11T10:20:00+09:00"
}
```

## 6.2 Submission 조회

`GET /api/tasks/{taskId}/submissions/{submissionId}`

응답 예시:

```json
{
  "id": 9001,
  "task_id": 501,
  "version_no": 1,
  "evaluation_status": "AWAITING_A",
  "ai_question": "이번 QA 결과에서 가장 치명적인 실패 조건 1개를 근거와 함께 설명해주세요.",
  "user_answer": null,
  "raw_score": null,
  "ai_factor": null,
  "provisional_score": null,
  "failed_stage": null,
  "error_message": null
}
```

가시성 원칙:
- submission 본문은 프로젝트 멤버에게 공개 가능한 범위로 본다.
- AI 질문, 사용자 답변, 세부 평가 코멘트는 제한 공개 대상일 수 있다.

## 6.3 Answer 제출

`POST /api/tasks/{taskId}/submissions/{submissionId}/answer`

설명:
- 기존 MVP의 `answer` 액션 유지
- `AWAITING_A` 상태에서만 허용

요청 예시:

```json
{
  "user_answer": "가장 치명적인 실패 조건은 비밀번호가 틀렸을 때 서버는 401을 반환하지만 UI는 일반 네트워크 오류로 표시하는 점입니다."
}
```

응답 예시:

```json
{
  "id": 9001,
  "evaluation_status": "SCORING",
  "user_answer": "가장 치명적인 실패 조건은 비밀번호가 틀렸을 때..."
}
```

## 6.4 Retry

`POST /api/tasks/{taskId}/submissions/{submissionId}/retry`

설명:
- 기존 MVP의 `retry` 액션 유지
- `FAILED` 상태에서만 허용
- 기존 검증 완료된 retry 원칙대로 동일 task / 동일 submission 기준 복구를 우선한다.
- 실패 단계에 따라 직전 유효 상태로 복구한다.

요청 예시:

```json
{
  "reason": "일시적 AI 평가 오류 재시도"
}
```

응답 예시:

```json
{
  "id": 9001,
  "evaluation_status": "GENERATING_Q",
  "failed_stage": null,
  "error_message": null,
  "retry_count": 1
}
```

---

## 7. 권장 조회 API

### 7.1 프로젝트 전체 요약 조회

`GET /api/projects/{projectId}/tasks?view=overview`

설명:
- member도 접근 가능한 협업용 overview
- 예시 필드:
  - `task_id`
  - `title`
  - `assignee`
  - `work_status`
  - `has_submission`
  - `latest_submission_version_no`

### 7.2 내 작업 중심 조회

`GET /api/projects/{projectId}/tasks?view=my`

설명:
- 본인 assignee task 또는 본인 제출 관련 task 중심 조회

### 7.3 프로젝트 민감 상세 조회

`GET /api/projects/{projectId}/tasks?view=sensitive-review`

설명:
- manager/owner 중심 조회
- 승인 이력, bonus 상세, 운영 예외 정보, 민감 평가 상세 포함 가능

### 7.4 Submission 목록 조회

`GET /api/tasks/{taskId}/submissions`

### 7.5 Bonus 로그 목록 조회

`GET /api/tasks/{taskId}/delta-bonuses`

### 7.6 감사 로그 조회

`GET /api/tasks/{taskId}/activity-logs`

설명:
- approve, request changes, delta bonus, close, cancel, reopen 이력 조회

---

## 8. 상태별 허용 액션 표

## 8.1 Task 상태 기준

| `work_status` | member | manager | 시스템 결과 |
|---|---|---|---|
| `DRAFT` | overview 조회 | assign, cancel, 메타 수정 | 아직 점수 없음 |
| `ASSIGNED` | 작업 시작, overview 조회 | assignee 변경, cancel, 메타 수정 | 진행 준비 상태 |
| `IN_PROGRESS` | submission 생성 | 진행 모니터링, 메타 수정 | 아직 review 전 |
| `SUBMITTED_FOR_REVIEW` | 직접 메타 수정 불가, 결과 대기 | approve, request changes, child task 판단 | 최신 submission 검토 |
| `CHANGES_REQUESTED` | 새 submission 생성 | 추가 가이드 제공 | 같은 task 내 version 증가 |
| `APPROVED` | 일반 수정 불가 | close, delta bonus 승인, child task 승인 | 본점수 잠금 가능 |
| `CLOSED` | 조회만 가능 | 조회만 가능 | 종료 |
| `CANCELED` | 조회만 가능 | 조회만 가능 | 무효 |

## 8.2 Submission 상태 기준

| `evaluation_status` | 허용 액션 | 비고 |
|---|---|---|
| `TODO` | submit 시작 처리 | 내부 초기 상태 |
| `GENERATING_Q` | 대기 | 질문 생성 중 |
| `AWAITING_A` | answer 제출 | 사용자 입력 가능 |
| `SCORING` | 대기 | 채점 중 |
| `DONE` | manager review | approve 또는 request changes 대상 |
| `FAILED` | retry | 실패 단계별 복구 |

---

## 9. API 흐름 예시

## 9.1 최초 제출 흐름

1. `POST /api/projects/{projectId}/tasks`
2. `POST /api/tasks/{taskId}/submissions`
3. 시스템이 `GENERATING_Q -> AWAITING_A`
4. `POST /api/tasks/{taskId}/submissions/{submissionId}/answer`
5. 시스템이 `SCORING -> DONE`
6. manager가 `POST /api/tasks/{taskId}/approve`

## 9.2 보완 요청 흐름

1. 최초 version이 `DONE`
2. manager가 `POST /api/tasks/{taskId}/request-changes`
3. member가 `POST /api/tasks/{taskId}/submissions`로 v2 생성
4. 동일한 질문/답변/채점 루프 재진행
5. manager가 approve 또는 추가 request changes

## 9.3 실패 복구 흐름

1. submission 상태가 `FAILED`
2. `POST /api/tasks/{taskId}/submissions/{submissionId}/retry`
3. 실패 단계에 따라 `GENERATING_Q` 또는 `AWAITING_A` 등으로 복구

## 9.4 승인 이후 추가 보상 흐름

1. task가 `APPROVED`, `score_lock_status=LOCKED`
2. 후속 보완 반영 완료
3. manager가 `POST /api/tasks/{taskId}/delta-bonuses`
4. `total_delta_bonus` 증가, 필요 시 `LOCKED_WITH_BONUS` 전환

---

## 10. 오류 응답 원칙

공통 오류 예시:

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "현재 상태에서는 approve를 수행할 수 없습니다."
  }
}
```

권장 오류 코드:
- `INVALID_STATE_TRANSITION`
- `FORBIDDEN`
- `NOT_FOUND`
- `VALIDATION_ERROR`
- `EVALUATION_FAILED`
- `RETRY_NOT_ALLOWED`
- `SENSITIVE_VIEW_FORBIDDEN`

---

## 11. 구현 메모

- `approve`는 `evaluation_status=DONE`인 submission만 대상으로 허용한다.
- `request changes`는 같은 task 내 새 version 생성 권한을 여는 액션이다.
- `close`는 승인 이후에만 가능하도록 제한한다.
- `delta bonus 지급`은 승인 이후에만 가능하도록 제한한다.
- `reopen`은 일반 사용자 플로우가 아니라 운영 예외 플로우로 분리한다.
- `task update`는 메타 수정 중심이며 submission version과 혼동하지 않도록 분리한다.
- member는 본인 task 중심으로 작업하되, 프로젝트 전체 협업용 overview는 조회 가능하도록 설계한다.

---

## 12. 결론

이 API 초안은 기존 MVP의 submit / answer / retry 동작을 유지하면서도, task와 submission의 책임을 분리하고 조회 가시성 계층과 감사 로그 요구사항까지 반영한 구현 직전 수준의 계약이다.
