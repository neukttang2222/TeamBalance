# Product DB Schema Draft

문서 상태: implementation-ready draft
기준 문서:
- `docs/product_scoring_policy.md`
- `docs/product_state_transition_policy.md`

## 1. 문서 목적

이 문서는 현재 점수 정책과 상태 전이 정책을 실제 저장 구조로 내리기 위한 DB 스키마 고정 초안이다.

대원칙:
- 기존 MVP 핵심 루프를 깨지 않는다.
- 기존 `submit / answer / retry` 흐름을 전면 재설계하지 않는다.
- additive migration을 우선한다.
- 기존 MVP의 `AI 질문 1개`, `답변 1회`, `raw_score 1~5`, `FAILED/retry` 정책은 그대로 유지한다.

핵심 방향:
- `tasks` 테이블은 유지하되 task 메타와 최종 확정 상태 중심으로 재정의한다.
- 실제 작업 결과물, 보완 제출, AI 평가, retry 이력은 `task_submissions`에 저장한다.
- 승인 이후 추가 기여는 `task_bonus_logs`에 additive하게 누적한다.
- 제품 1차부터 필수 감사 로그를 남기기 위해 `task_activity_logs`를 포함한다.

---

## 2. 제안 테이블 개요

제품 1차 기준 핵심 테이블은 아래 4개다.

1. `tasks`
- task 메타데이터, 담당자, 최종 작업 상태, 점수 잠금 상태, 승인 메타, 집계 점수 보관

2. `task_submissions`
- 같은 task 내 version별 제출 본문, 제출 메모, AI 질문/답변, AI 평가, 실패/retry 상태 보관

3. `task_bonus_logs`
- 승인 이후 동일 task에 대한 delta bonus 지급 이력 보관

4. `task_activity_logs`
- 승인/보완 요청/bonus 지급/종결/취소/reopen 등 필수 감사 로그 보관

선택적 후속 테이블은 별도 검토 가능하다.
- `task_comments`
- `task_submission_retry_logs`
- `task_visibility_policies`

다만 `task_activity_logs`는 후순위 optional이 아니라 제품 1차 필수 또는 강권 범위로 본다.

---

## 3. 저장 책임 원칙

가장 중요한 저장 책임 경계는 아래와 같다.

| 저장 대상 | 저장 위치 | 원칙 |
|---|---|---|
| task 메타 | `tasks` | 제목, 설명, 담당자, 상태, 승인 메타, 점수 잠금 메타는 task가 책임진다 |
| 작업 결과물 변경 | `task_submissions` | member의 실제 작업 내용 변경은 task 수정이 아니라 submission version으로 저장한다 |
| AI 평가 흐름 | `task_submissions` | 질문/답변/raw score/provisional score/실패/retry는 version 단위로 저장한다 |
| 확정 본점수 | `tasks` | 승인 후 잠긴 main score는 task 단위 단일 값으로 유지한다 |
| 추가 bonus | `task_bonus_logs` + `tasks.total_delta_bonus` | 잠긴 본점수는 건드리지 않고 bonus만 additive하게 누적한다 |
| 운영/승인 감사 이력 | `task_activity_logs` | 제품 1차 필수 감사 로그로 저장한다 |

즉, member는 task의 핵심 메타를 직접 수정하는 주체가 아니라 submission version을 추가하는 주체다.

---

## 4. 테이블별 상세 초안

## 4.1 `tasks`

역할:
- 기존 `tasks` 테이블 유지
- task의 메타데이터, 업무 단위 상태, 승인 메타, 잠긴 점수의 단일 진실 공급원 역할

### 필드 초안

| 필드명 | 타입 예시 | NULL | 설명 |
|---|---|---:|---|
| `id` | bigint / uuid | N | PK |
| `project_id` | bigint / uuid | N | 프로젝트 FK |
| `parent_task_id` | bigint / uuid | Y | child task인 경우 상위 task |
| `title` | varchar(255) | N | task 제목 |
| `description` | text | Y | task 설명 |
| `task_goal` | text | Y | task 목표/범위 |
| `task_type` | varchar(50) | Y | 정책 기반 base_points 계산용 분류 |
| `task_template_id` | bigint / uuid | Y | 정책 템플릿 기준값 |
| `difficulty_policy_code` | varchar(50) | Y | 난이도 정책 코드 |
| `creator_user_id` | bigint / uuid | N | 생성자 |
| `assignee_user_id` | bigint / uuid | Y | 담당 member |
| `manager_user_id` | bigint / uuid | Y | 검토 책임자 |
| `work_status` | varchar(32) enum | N | task 작업 상태 |
| `score_lock_status` | varchar(32) enum | N | 점수 잠금 상태 |
| `base_points` | decimal(6,2) | N | 서버 정책에 따라 계산된 task 기본 점수 |
| `locked_main_score` | decimal(6,2) | Y | 승인 후 확정 본점수 |
| `total_delta_bonus` | decimal(6,2) | N | 누적 bonus 합계, 기본값 0 |
| `approved_version_no` | int | Y | 승인된 submission version 번호 |
| `approved_submission_id` | bigint / uuid | Y | 승인된 submission FK |
| `approved_by` | bigint / uuid | Y | 승인자 |
| `approved_at` | datetime | Y | 승인 시각 |
| `closed_by` | bigint / uuid | Y | 종료 처리자 |
| `closed_at` | datetime | Y | 종료 시각 |
| `canceled_by` | bigint / uuid | Y | 취소 처리자 |
| `canceled_at` | datetime | Y | 취소 시각 |
| `reopened_from_task_id` | bigint / uuid | Y | reopen 이력 추적용 선택 필드 |
| `created_at` | datetime | N | 생성 시각 |
| `updated_at` | datetime | N | 수정 시각 |

### enum 후보

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

### PK / FK

- PK: `tasks.id`
- FK 후보:
  - `project_id -> projects.id`
  - `parent_task_id -> tasks.id`
  - `task_template_id -> task_templates.id`
  - `creator_user_id -> users.id`
  - `assignee_user_id -> users.id`
  - `manager_user_id -> users.id`
  - `approved_submission_id -> task_submissions.id`
  - `approved_by -> users.id`
  - `closed_by -> users.id`
  - `canceled_by -> users.id`

### 인덱스 후보

- `idx_tasks_project_status` on (`project_id`, `work_status`)
- `idx_tasks_assignee_status` on (`assignee_user_id`, `work_status`)
- `idx_tasks_manager_status` on (`manager_user_id`, `work_status`)
- `idx_tasks_parent` on (`parent_task_id`)
- `idx_tasks_project_created_at` on (`project_id`, `created_at desc`)
- `idx_tasks_project_overview` on (`project_id`, `work_status`, `assignee_user_id`)
- unique 후보: `uq_tasks_approved_submission_id` on (`approved_submission_id`)

### 저장 책임

이 테이블에서 반드시 저장되는 개념:
- `work_status`
- `score_lock_status`
- `base_points`
- `locked_main_score`
- `total_delta_bonus`
- `approved_version_no`

주의:
- `evaluation_status`는 task 전체 상태가 아니라 version 상태이므로 `task_submissions`에 둔다.
- member의 작업 내용 변경은 `tasks`가 아니라 `task_submissions`에 저장한다.
- task 조회에서 “현재 평가 상태”가 필요하면 최신 submission join 또는 projection으로 제공한다.

---

## 4.2 `task_submissions`

역할:
- 같은 task 안의 제출 version 이력 저장
- 기존 MVP의 `submit / answer / retry`를 version 단위로 확장 또는 래핑하는 중심 테이블
- AI 질문/답변/채점/실패/retry를 version 단위로 보관

### 필드 초안

| 필드명 | 타입 예시 | NULL | 설명 |
|---|---|---:|---|
| `id` | bigint / uuid | N | PK |
| `task_id` | bigint / uuid | N | 소속 task |
| `version_no` | int | N | task 내 1부터 증가 |
| `submission_content` | text / json | Y | 제출 본문 또는 구조화된 payload |
| `submission_note` | text | Y | 제출 메모 |
| `evaluation_status` | varchar(32) enum | N | AI 평가 상태 |
| `ai_question` | text | Y | AI 생성 질문 1개 |
| `user_answer` | text | Y | 질문에 대한 답변 1회 |
| `raw_score` | int | Y | 1~5 |
| `ai_factor` | decimal(4,2) | Y | raw_score 기반 계수 |
| `provisional_score` | decimal(6,2) | Y | 잠금 전 임시 점수 |
| `ai_comment` | text | Y | 민감 평가 상세 정보 후보 |
| `failed_stage` | varchar(32) enum | Y | 실패 단계 |
| `error_message` | text | Y | 사용자/운영 노출 가능한 실패 메시지 |
| `retry_count` | int | N | retry 횟수, 기본값 0 |
| `submitted_by` | bigint / uuid | N | 제출자 |
| `submitted_at` | datetime | N | 제출 시각 |
| `question_generated_at` | datetime | Y | 질문 생성 완료 시각 |
| `answered_at` | datetime | Y | 답변 제출 시각 |
| `scored_at` | datetime | Y | 채점 완료 시각 |
| `last_retried_at` | datetime | Y | 마지막 retry 시각 |
| `created_at` | datetime | N | 생성 시각 |
| `updated_at` | datetime | N | 수정 시각 |

### enum 후보

`evaluation_status`
- `TODO`
- `GENERATING_Q`
- `AWAITING_A`
- `SCORING`
- `DONE`
- `FAILED`

`failed_stage`
- `QUESTION_GENERATION`
- `ANSWER_VALIDATION`
- `SCORING`
- `SYSTEM_UNKNOWN`

### PK / FK

- PK: `task_submissions.id`
- FK:
  - `task_id -> tasks.id`
  - `submitted_by -> users.id`

### 제약 조건 후보

- unique: `uq_task_submissions_task_version` on (`task_id`, `version_no`)
- check: `raw_score between 1 and 5`
- check: `retry_count >= 0`
- check: `version_no >= 1`

### 인덱스 후보

- `idx_task_submissions_task_version_desc` on (`task_id`, `version_no desc`)
- `idx_task_submissions_task_eval_status` on (`task_id`, `evaluation_status`)
- `idx_task_submissions_eval_status` on (`evaluation_status`, `updated_at`)
- `idx_task_submissions_submitted_by` on (`submitted_by`, `submitted_at desc`)

### 저장 책임

이 테이블에서 반드시 저장되는 개념:
- `evaluation_status`
- `ai_question`
- `user_answer`
- `raw_score`
- `ai_factor`
- `provisional_score`
- `failed_stage`
- `error_message`

중요 원칙:
- 실제 작업 결과물과 보완은 모두 `task_submissions`에 version으로 남긴다.
- member가 수정하는 실질적 작업 내용은 `submission_content`, `submission_note`, `user_answer`다.
- `tasks`의 제목/설명/배정/승인 메타를 member가 직접 갱신하는 구조는 지양한다.

### 상태 복구 원칙

- 기존 검증 완료된 retry 원칙을 유지한다.
- retry는 새 row 생성보다 같은 `submission` row의 `evaluation_status`를 직전 가용 상태로 복구하는 방식을 우선 추천한다.
- 즉, 동일 task / 동일 submission 기준 복구를 기본 원칙으로 둔다.
- 추후 세밀한 장애 추적이 더 필요하면 `task_submission_retry_logs`를 additive하게 도입할 수 있다.

---

## 4.3 `task_bonus_logs`

역할:
- 승인 이후 동일 task 내 추가 기여를 delta bonus로 누적 저장
- 잠긴 본점수를 수정하지 않고 bonus만 additive하게 합산

### 필드 초안

| 필드명 | 타입 예시 | NULL | 설명 |
|---|---|---:|---|
| `id` | bigint / uuid | N | PK |
| `task_id` | bigint / uuid | N | bonus 대상 task |
| `submission_id` | bigint / uuid | Y | bonus 근거가 된 version |
| `version_no` | int | Y | 조회 편의용 version 번호 |
| `bonus_points` | decimal(6,2) | N | 승인 bonus |
| `reason_code` | varchar(32) enum | N | bonus 사유 분류 |
| `reason_detail` | text | Y | 상세 설명 |
| `approved_by` | bigint / uuid | N | 승인자 |
| `approved_at` | datetime | N | 승인 시각 |
| `created_at` | datetime | N | 생성 시각 |

### enum 후보

`reason_code`
- `REVISION_ACCEPTED`
- `EXTRA_ANALYSIS`
- `FOLLOW_UP_REQUEST`
- `MANUAL_ADJUSTMENT`

### PK / FK

- PK: `task_bonus_logs.id`
- FK:
  - `task_id -> tasks.id`
  - `submission_id -> task_submissions.id`
  - `approved_by -> users.id`

### 제약 조건 후보

- check: `bonus_points > 0`
- check: `version_no >= 1` when not null

### 인덱스 후보

- `idx_task_bonus_logs_task_created_at` on (`task_id`, `created_at desc`)
- `idx_task_bonus_logs_submission` on (`submission_id`)
- `idx_task_bonus_logs_approved_by` on (`approved_by`, `approved_at desc`)

### 집계 규칙

- `tasks.total_delta_bonus`는 `task_bonus_logs.bonus_points` 누적합으로 관리한다.
- 구현은 애플리케이션 트랜잭션에서 아래를 함께 처리하는 방식을 권장한다.
  - `task_bonus_logs` insert
  - `tasks.total_delta_bonus` update
  - 필요 시 `tasks.score_lock_status`를 `LOCKED_WITH_BONUS`로 전환

---

## 4.4 `task_activity_logs`

역할:
- 제품 1차 필수 감사 로그 저장
- 승인, 보완 요청, bonus 지급, close, cancel, reopen 같은 운영성 액션을 추적

### 필드 초안

| 필드명 | 타입 예시 | NULL | 설명 |
|---|---|---:|---|
| `id` | bigint / uuid | N | PK |
| `task_id` | bigint / uuid | N | 대상 task |
| `submission_id` | bigint / uuid | Y | 관련 submission |
| `actor_user_id` | bigint / uuid | N | 액션 수행자 |
| `action_type` | varchar(32) enum | N | 감사 로그 액션 종류 |
| `from_work_status` | varchar(32) | Y | 변경 전 work status |
| `to_work_status` | varchar(32) | Y | 변경 후 work status |
| `from_score_lock_status` | varchar(32) | Y | 변경 전 점수 잠금 상태 |
| `to_score_lock_status` | varchar(32) | Y | 변경 후 점수 잠금 상태 |
| `metadata` | json / text | Y | 사유, 코멘트, bonus 값 등 부가 정보 |
| `created_at` | datetime | N | 생성 시각 |

### action_type enum 후보

- `APPROVE`
- `REQUEST_CHANGES`
- `DELTA_BONUS_GRANTED`
- `CLOSE`
- `CANCEL`
- `REOPEN`

### PK / FK

- PK: `task_activity_logs.id`
- FK:
  - `task_id -> tasks.id`
  - `submission_id -> task_submissions.id`
  - `actor_user_id -> users.id`

### 인덱스 후보

- `idx_task_activity_logs_task_created_at` on (`task_id`, `created_at desc`)
- `idx_task_activity_logs_submission` on (`submission_id`)
- `idx_task_activity_logs_actor_created_at` on (`actor_user_id`, `created_at desc`)
- `idx_task_activity_logs_action_type` on (`action_type`, `created_at desc`)

### 감사 로그 필수 범위

제품 1차에서 아래 액션은 감사 로그를 필수로 남긴다.
- approve
- request changes
- delta bonus 승인
- close
- cancel
- reopen

---

## 5. 추천 ERD 관계 설명

텍스트 ERD:

- `projects 1 - N tasks`
- `tasks 1 - N task_submissions`
- `tasks 1 - N task_bonus_logs`
- `tasks 1 - N task_activity_logs`
- `task_submissions 1 - N task_bonus_logs`는 선택 관계
- `task_submissions 1 - N task_activity_logs`는 선택 관계
- `tasks.parent_task_id -> tasks.id`로 child task 관계 표현

관계 해석:
- task는 업무 단위다.
- submission은 같은 업무 단위 안의 버전이다.
- bonus log는 잠긴 본점수 이후의 추가 기여 승인 이력이다.
- activity log는 상태 전이와 운영성 의사결정의 감사 이력이다.

---

## 6. 상태/점수/가시성 저장 책임 분리

| 책임 | 저장 위치 | 이유 |
|---|---|---|
| 작업 진행 상태 | `tasks.work_status` | task 단위 라이프사이클이기 때문 |
| AI 평가 상태 | `task_submissions.evaluation_status` | version별 평가 흐름이기 때문 |
| 점수 잠금 여부 | `tasks.score_lock_status` | 최종 확정 점수는 task 단위이기 때문 |
| 기본 점수 | `tasks.base_points` | 생성 요청의 입력값이 아니라 서버 정책 계산 결과이기 때문 |
| 작업 결과물 본문 | `task_submissions.submission_content` | member의 작업 내용 변경은 submission version에 저장하기 때문 |
| 제출 메모 | `task_submissions.submission_note` | version 부가정보이기 때문 |
| AI 질문/답변 | `task_submissions.ai_question`, `task_submissions.user_answer` | MVP 루프가 version 단위이기 때문 |
| 임시 점수 | `task_submissions.provisional_score` | version별 AI 결과이기 때문 |
| 확정 본점수 | `tasks.locked_main_score` | 승인 후 단일 확정값이어야 하기 때문 |
| 추가 보너스 합계 | `tasks.total_delta_bonus` | task 집계 응답 최적화용 |
| bonus 상세 승인 이력 | `task_bonus_logs` | additive bonus 세부 이력이기 때문 |
| 운영/승인 감사 이력 | `task_activity_logs` | 필수 감사 추적이기 때문 |

---

## 7. 최소 수정 관점의 마이그레이션 방향

### 7.1 `tasks` 유지 + 컬럼 추가

가능하면 기존 `tasks` 테이블은 rename 없이 유지한다.

추가/정비 권장 컬럼:
- `work_status`
- `score_lock_status`
- `task_type`
- `task_template_id`
- `difficulty_policy_code`
- `base_points`
- `locked_main_score`
- `total_delta_bonus`
- `approved_version_no`
- `approved_submission_id`
- `approved_by`
- `approved_at`
- `closed_at`

### 7.2 새 테이블 추가

신규 생성:
- `task_submissions`
- `task_bonus_logs`
- `task_activity_logs`

### 7.3 기존 MVP와의 연결

- 기존 `submit` 엔드포인트는 내부적으로 `task_submissions` row 생성으로 확장 또는 래핑한다.
- 기존 `answer` / `retry` 엔드포인트는 `task_submissions` 중심으로 유지한다.
- 기존 retry 원칙인 동일 task / 동일 submission 기준 복구 우선을 유지한다.
- 승인 시점에만 `tasks.locked_main_score`를 갱신한다.
- 전면 재설계보다 additive migration을 우선한다.

---

## 8. 구현 메모

### 8.1 점수 계산 시점

- `provisional_score = base_points * ai_factor`
- approval 전까지는 `tasks.locked_main_score`를 채우지 않는다.
- manager approve 시:
  - 대상 submission의 `provisional_score`를 `tasks.locked_main_score`에 저장
  - `approved_version_no` 기록
  - `score_lock_status = LOCKED`
  - `task_activity_logs`에 `APPROVE` 기록

### 8.2 bonus 반영 시점

- bonus 승인 시 `task_bonus_logs` insert
- 같은 트랜잭션에서:
  - `tasks.total_delta_bonus += bonus_points`
  - 필요 시 `score_lock_status = LOCKED_WITH_BONUS`
  - `task_activity_logs`에 `DELTA_BONUS_GRANTED` 기록

### 8.3 상태 전이 감사 로그

아래 액션은 DB 저장 시 반드시 `task_activity_logs`를 남긴다.
- approve
- request changes
- close
- cancel
- reopen

### 8.4 조회 응답 계산값

API 응답에서는 아래 계산값을 함께 제공 가능하다.
- `final_contribution_score = locked_main_score + total_delta_bonus`
- `current_submission_version_no = max(task_submissions.version_no)`
- `latest_evaluation_status = latest submission의 evaluation_status`

---

## 9. 결론

이 초안은 기존 MVP의 단순한 평가 루프를 유지하면서도 아래 네 가지를 분리한다.

- task 최종 상태와 잠긴 점수
- version별 제출 및 AI 평가 흐름
- 승인 이후 additive bonus 이력
- 제품 1차 필수 감사 로그

이 구조를 사용하면 기존 검증 완료된 submit / answer / retry 흐름을 무리하게 파괴하지 않으면서 구현 직전 수준의 DB 설계로 이어갈 수 있다.
