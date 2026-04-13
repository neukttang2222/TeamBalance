# Product Integrated Schema And Migration Plan

문서 상태: implementation-ready draft

## 1. 문서 목적

이 문서는 지금까지 분리되어 작성된 평가 엔진 레이어 문서와 제품 레이어 문서를 실제 구현 가능한 통합 기준으로 묶기 위한 문서다.

핵심 목표:
- 현재 기준 문서를 하나의 구현용 스키마 관점으로 통합한다.
- 기존 MVP 핵심 루프를 유지한다.
- 한 번에 전체를 갈아엎지 않고 additive migration 방식으로 옮긴다.
- 실제 DB 마이그레이션, API 연결, current user 처리 기준을 한 문서에서 확인할 수 있게 한다.

핵심 원칙:
- 최소 수정 원칙 유지
- additive migration 우선
- 기존 `submit / answer / retry` 흐름 유지
- 기존 MVP의 `AI 질문 1개`, `답변 1회`, `raw_score 1~5`, `FAILED/retry` 정책 유지

---

## 2. 현재 기준 문서 목록

- `docs/product_scoring_policy.md`
- `docs/product_state_transition_policy.md`
- `docs/product_db_schema_draft.md`
- `docs/product_api_contract_draft.md`
- `docs/product_authorization_matrix.md`
- `docs/product_team_project_domain.md`
- `docs/product_auth_session_policy.md`
- `docs/product_visibility_policy.md`

이 문서는 위 문서들의 결정을 구현 준비용 통합 기준으로 접어 넣는 역할을 한다.

---

## 3. 통합 대상 엔티티 목록

제품 1차 기준 통합 엔티티는 아래와 같다.

- `users/profile`
- `teams`
- `team_members`
- `projects`
- `project_members`
- `tasks`
- `task_submissions`
- `task_bonus_logs`
- `task_activity_logs`

역할 요약:
- `users/profile`: 인증 이후 제품 내부 사용자 프로필
- `teams`: 프로젝트 상위 단위
- `team_members`: 사용자-팀 소속 연결
- `projects`: task가 속하는 직접 상위 단위
- `project_members`: 사용자-프로젝트 소속과 역할 연결
- `tasks`: task 메타, 상태, 승인, 점수 잠금
- `task_submissions`: 제출 version, AI 질문/답변, 평가 흐름
- `task_bonus_logs`: 승인 이후 additive bonus 이력
- `task_activity_logs`: 제품 1차 필수 감사 로그

---

## 4. 테이블 간 최종 관계 설명

최종 관계는 아래와 같이 정리한다.

- `users 1 - N team_members`
- `teams 1 - N team_members`
- `teams 1 - N projects`
- `users 1 - N project_members`
- `projects 1 - N project_members`
- `projects 1 - N tasks`
- `tasks 1 - N task_submissions`
- `tasks 1 - N task_bonus_logs`
- `tasks 1 - N task_activity_logs`
- `task_submissions 1 - N task_bonus_logs`는 선택 관계
- `task_submissions 1 - N task_activity_logs`는 선택 관계
- `tasks.parent_task_id -> tasks.id`로 parent/child 관계 표현

핵심 해석:
- 팀이 상위, 프로젝트가 하위다.
- task는 반드시 프로젝트에 속한다.
- 실제 작업 결과물과 평가 흐름은 submission version에 저장한다.
- 점수 잠금과 승인 메타는 task에 저장한다.
- 운영성 상태 전이와 승인 행위는 activity log에 남긴다.

---

## 5. 통합 테이블 구조 요약

## 5.1 `users` 또는 `user_profiles`

최소 필드:
- `id`
- `email`
- `display_name`
- `created_at`
- `last_login_at` optional

역할:
- 앱 내부 사용자 프로필
- 팀/프로젝트 멤버십 연결 기준

## 5.2 `teams`

최소 필드:
- `id`
- `name`
- `created_by`
- `created_at`

## 5.3 `team_members`

최소 필드:
- `id`
- `team_id`
- `user_id`
- `joined_at`

## 5.4 `projects`

최소 필드:
- `id`
- `team_id`
- `name`
- `description`
- `created_by`
- `created_at`

핵심 원칙:
- `team_id` 필수

## 5.5 `project_members`

최소 필드:
- `id`
- `project_id`
- `user_id`
- `role`
- `joined_at`

핵심 원칙:
- `role`은 `owner / manager / member`

## 5.6 `tasks`

핵심 필드:
- `id`
- `project_id`
- `parent_task_id`
- `title`
- `description`
- `task_goal`
- `task_type`
- `task_template_id`
- `difficulty_policy_code`
- `creator_user_id`
- `assignee_user_id`
- `manager_user_id`
- `work_status`
- `score_lock_status`
- `base_points`
- `locked_main_score`
- `total_delta_bonus`
- `approved_version_no`
- `approved_submission_id`
- `approved_by`
- `approved_at`
- `closed_at`
- `canceled_at`
- `created_at`
- `updated_at`

## 5.7 `task_submissions`

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
- `ai_comment`
- `failed_stage`
- `error_message`
- `retry_count`
- `submitted_by`
- `submitted_at`
- `answered_at`
- `scored_at`

## 5.8 `task_bonus_logs`

핵심 필드:
- `id`
- `task_id`
- `submission_id`
- `version_no`
- `bonus_points`
- `reason_code`
- `reason_detail`
- `approved_by`
- `approved_at`

## 5.9 `task_activity_logs`

핵심 필드:
- `id`
- `task_id`
- `submission_id`
- `actor_user_id`
- `action_type`
- `from_work_status`
- `to_work_status`
- `from_score_lock_status`
- `to_score_lock_status`
- `metadata`
- `created_at`

---

## 6. 기존 MVP `tasks` 구조에서 유지 / 추가 / 분리

## 6.1 유지할 것

기존 `tasks` 테이블 자체는 유지한다.

유지 이유:
- 기존 MVP와의 호환성 유지
- 기존 task 중심 API와 UI를 한 번에 깨지 않기 위함

## 6.2 `tasks`에 추가할 것

추가 또는 정비 권장 컬럼:
- `project_id`
- `parent_task_id`
- `task_type`
- `task_template_id`
- `difficulty_policy_code`
- `work_status`
- `score_lock_status`
- `base_points`
- `locked_main_score`
- `total_delta_bonus`
- `approved_version_no`
- `approved_submission_id`
- `approved_by`
- `approved_at`
- `closed_by`
- `closed_at`
- `canceled_by`
- `canceled_at`

## 6.3 `tasks`에서 직접 다루지 않고 분리할 것

아래는 `tasks`의 직접 책임이 아니라 `task_submissions` 또는 로그 테이블로 분리한다.

- 제출 본문
- 제출 메모
- AI 질문
- 사용자 답변
- raw score
- ai factor
- provisional score
- failed stage
- error message
- retry 횟수
- 승인 이후 bonus 상세 이력
- 운영 감사 로그

즉, member의 작업 내용 변경은 task row 수정이 아니라 submission version 추가로 이동한다.

---

## 7. 신규 생성 테이블 목록

통합 기준에서 신규 생성 대상은 아래와 같다.

- `teams`
- `team_members`
- `projects`
- `project_members`
- `task_submissions`
- `task_bonus_logs`
- `task_activity_logs`

선택적으로 후순위 검토 가능한 테이블:
- `task_submission_retry_logs`
- `task_comments`

---

## 8. 마이그레이션 순서 제안

권장 순서는 아래와 같다.

## 8.1 1단계: 기존 `tasks` 확장

목표:
- 기존 task 구조를 깨지 않고 새 상태/점수/프로젝트 기준을 수용

작업:
- `tasks`에 신규 컬럼 추가
- nullable 중심으로 먼저 도입
- 기존 로직이 깨지지 않도록 기본값 설계

## 8.2 2단계: submission / bonus / activity 로그 테이블 생성

목표:
- version 구조, bonus 이력, 감사 로그 구조 도입

작업:
- `task_submissions` 생성
- `task_bonus_logs` 생성
- `task_activity_logs` 생성

## 8.3 3단계: team / project / membership 테이블 생성

목표:
- 제품 레이어의 상위 구조 고정

작업:
- `teams`
- `team_members`
- `projects`
- `project_members`

## 8.4 4단계: 기존 task를 project 기준으로 연결

목표:
- 모든 task가 프로젝트에 속하도록 정합성 확보

작업:
- 기본 프로젝트 생성 또는 기존 데이터 매핑
- `tasks.project_id` 백필

## 8.5 5단계: API 연결 전환

목표:
- 기존 submit/answer/retry를 version 구조에 연결

작업:
- submit 시 `task_submissions` row 생성
- answer/retry는 `task_submissions` 기반으로 처리
- approve/request changes/close/bonus/reopen은 task와 로그 구조에 연결

## 8.6 6단계: auth/session 기반 actor 채우기 전환

목표:
- 클라이언트 입력 user id 제거

작업:
- current user 기준으로 `creator_user_id`, `submitted_by`, `actor_user_id`, `approved_by` 채움

---

## 9. 데이터 무결성 및 FK / 인덱스 우선순위

## 9.1 FK 우선순위

우선 도입할 FK:
- `tasks.project_id -> projects.id`
- `task_submissions.task_id -> tasks.id`
- `task_bonus_logs.task_id -> tasks.id`
- `task_activity_logs.task_id -> tasks.id`
- `project_members.project_id -> projects.id`
- `project_members.user_id -> users.id`

2차로 강화할 FK:
- `tasks.approved_submission_id -> task_submissions.id`
- `task_bonus_logs.submission_id -> task_submissions.id`
- `task_activity_logs.submission_id -> task_submissions.id`
- `teams.created_by -> users.id`
- `projects.created_by -> users.id`

## 9.2 무결성 우선순위

우선 적용 권장:
- `task_submissions (task_id, version_no)` unique
- `raw_score between 1 and 5`
- `retry_count >= 0`
- `project_members (project_id, user_id)` unique
- `team_members (team_id, user_id)` unique

## 9.3 인덱스 우선순위

우선 인덱스:
- `tasks(project_id, work_status)`
- `tasks(assignee_user_id, work_status)`
- `task_submissions(task_id, version_no desc)`
- `task_submissions(task_id, evaluation_status)`
- `task_activity_logs(task_id, created_at desc)`
- `project_members(project_id, role)`

---

## 10. 기존 `submit / answer / retry`와 version 구조 연결

기존 MVP 루프는 유지한다.

연결 원칙:
- `submit`는 기존처럼 task 기준으로 호출되더라도 내부적으로는 `task_submissions` 새 row 생성으로 연결한다.
- `answer`는 최신 또는 지정 submission의 `user_answer`를 채운다.
- `retry`는 기존 원칙대로 동일 task / 동일 submission 기준 복구를 우선한다.

즉, 외부 API 계약은 급격히 깨지지 않고 내부 저장 구조만 version 중심으로 옮겨간다.

실무 해석:
- 기존 MVP 엔드포인트를 폐기하기보다 version-aware wrapper로 유지
- UI도 처음에는 큰 변경 없이 내부 API 구현만 교체 가능

---

## 11. auth/session 기준으로 creator / submitted_by / actor 채우기

현재 사용자 기준 원칙:
- `tasks.creator_user_id`는 세션 사용자 기준으로 채운다.
- `task_submissions.submitted_by`는 세션 사용자 기준으로 채운다.
- `task_activity_logs.actor_user_id`는 세션 사용자 기준으로 채운다.
- `tasks.approved_by`, `task_bonus_logs.approved_by`도 세션 사용자 기준으로 채운다.

즉:
- 클라이언트 요청 body에서 사용자 식별값을 받지 않는다.
- 서버가 현재 로그인 사용자를 기준으로 관련 actor 필드를 채운다.

---

## 12. 최소 수정 원칙과 additive migration 재확인

이 통합 계획은 전면 재설계가 아니다.

핵심 재확인:
- 기존 MVP의 task 중심 구조는 유지한다.
- 기존 submit/answer/retry 흐름은 유지한다.
- 다만 내부 저장 구조와 제품 도메인을 additive하게 확장한다.
- member의 작업 내용은 submission version으로 이동시키되, 기존 UX를 불필요하게 깨지 않는다.
- 제품 레이어인 team/project/membership/auth/visibility는 기존 평가 엔진 레이어 바깥에서 받쳐주는 구조로 붙인다.

---

## 13. 결론

이 문서는 지금까지 분리된 정책 문서를 실제 구현 가능한 통합 스키마와 마이그레이션 순서로 묶는다.

구현의 핵심은 아래 세 가지다.
- `tasks`를 유지한 채 version/bonus/activity log를 분리
- project/team/membership을 상위 제품 구조로 추가
- auth/session 기반 current user 처리로 API의 사용자 식별 방식을 정리
