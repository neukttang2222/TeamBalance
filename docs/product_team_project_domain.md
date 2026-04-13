# Product Team Project Domain

문서 상태: implementation-ready draft
기준 문서:
- `docs/product_scoring_policy.md`
- `docs/product_state_transition_policy.md`
- `docs/product_db_schema_draft.md`
- `docs/product_api_contract_draft.md`
- `docs/product_authorization_matrix.md`

## 1. 문서 목적

이 문서는 평가 엔진 레이어 바깥의 제품 도메인 중 `팀 / 프로젝트 / 멤버십 / task 소속 구조`를 고정하기 위한 기준 문서다.

대원칙:
- 현재 MVP 핵심 루프는 유지한다.
- additive 확장을 우선한다.
- 최소 수정 원칙을 유지한다.
- 아직 구현하지 않는 기능까지 과도하게 넓히지 않는다.

이 문서가 고정하려는 핵심은 다음 한 줄이다.

`팀이 상위이고, 프로젝트가 하위이며, task는 프로젝트에 속한다.`

---

## 2. 도메인 엔티티 정의

## 2.1 User

서비스를 사용하는 기본 사용자 단위.

책임:
- 인증된 사용자 identity 보유
- 하나 이상의 팀에 속할 수 있음
- 하나 이상의 프로젝트에 참여할 수 있음

## 2.2 Team

프로젝트를 묶는 상위 협업 단위.

책임:
- 프로젝트의 상위 소속
- 팀 단위 운영과 멤버 구성의 기준

## 2.3 TeamMember

User와 Team의 연결 엔티티.

책임:
- 어떤 사용자가 어떤 팀에 속하는지 저장
- 팀 단위 역할 또는 소속 상태 저장 가능

## 2.4 Project

실제 task와 리뷰, 진행 현황이 운영되는 작업 단위.

책임:
- 반드시 하나의 팀에 속함
- task의 직접 상위 컨테이너
- 프로젝트 멤버십과 역할 운영의 기준

## 2.5 ProjectMember

User와 Project의 연결 엔티티.

책임:
- 어떤 사용자가 어떤 프로젝트에 참여하는지 저장
- 프로젝트 내 역할인 `owner / manager / member` 저장

## 2.6 Task

프로젝트 안에서 생성되는 업무 단위.

책임:
- 프로젝트에 속하는 단일 업무 범위
- 상태, 승인, 점수 잠금의 기준 단위
- 제출 version은 별도 `task_submissions`로 관리

---

## 3. 관계 규칙

이 제품의 기본 관계는 아래와 같이 고정한다.

- `User : Team = N : M`
- `Team : Project = 1 : N`
- `User : Project = N : M`
- `Project : Task = 1 : N`

해석:
- 한 사용자는 여러 팀에 속할 수 있다.
- 한 팀은 여러 프로젝트를 가질 수 있다.
- 한 사용자는 여러 프로젝트에 참여할 수 있다.
- 하나의 프로젝트에는 여러 task가 속한다.

---

## 4. 역할 체계

프로젝트 레벨 기본 역할은 아래 3개로 고정한다.

- `owner`
- `manager`
- `member`

## 4.1 owner

상위 운영 역할.

책임:
- 팀/프로젝트 상위 운영
- 민감 조회와 운영 예외 처리
- reopen 같은 예외 액션 수행

## 4.2 manager

프로젝트/task 운영 역할.

책임:
- 프로젝트 내 task 생성과 배정
- 제출 검토와 승인
- 보완 요청, bonus 승인, child task 판단

## 4.3 member

실제 수행자 역할.

책임:
- 배정된 task 수행
- submission 생성
- answer 제출
- retry 수행

---

## 5. 운영 책임 정의

역할별 책임을 제품 관점에서 다시 정리하면 아래와 같다.

| 역할 | 운영 책임 |
|---|---|
| `owner` | 팀/프로젝트 상위 운영 |
| `manager` | 프로젝트/task 운영 |
| `member` | 수행자 |

중요 원칙:
- owner는 팀과 프로젝트의 상위 운영 기준점이다.
- manager는 실제 프로젝트 안에서 task를 굴리는 운영자다.
- member는 task 메타를 관리하는 사람이 아니라 작업 결과물을 제출하는 수행자다.

---

## 6. 팀/프로젝트 생성 및 소속 규칙

## 6.1 팀 생성

제품 1차에서는 팀 생성 주체를 owner 또는 운영자 범위로 제한하는 것을 권장한다.

핵심 규칙:
- 프로젝트는 반드시 팀 아래에서 생성된다.
- 팀 없는 프로젝트는 허용하지 않는다.

## 6.2 프로젝트 생성

프로젝트 생성 시 필수 원칙:
- `project.team_id`는 필수다.
- 프로젝트는 정확히 하나의 팀에 속한다.
- owner 또는 manager가 프로젝트를 생성할 수 있다. 단 실제 정책은 팀 운영 방식에 따라 좁힐 수 있다.

## 6.3 팀 소속 규칙

- 사용자는 팀에 먼저 소속될 수 있다.
- 프로젝트 멤버가 되려면 원칙적으로 해당 팀 소속 사용자여야 한다.
- 제품 1차에서는 “프로젝트 멤버는 해당 팀 멤버의 부분집합”을 권장 기본값으로 둔다.

## 6.4 프로젝트 멤버 배정 규칙

- 프로젝트 멤버십은 `project_members`에서 관리한다.
- 프로젝트별 역할은 `owner / manager / member` 중 하나로 둔다.
- 한 사용자는 프로젝트마다 다른 역할을 가질 수 있다.
- task assignee는 원칙적으로 해당 프로젝트의 `member` 또는 `manager` 중에서 선택한다.

---

## 7. Parent Task / Child Task 해석

child task와 parent task는 프로젝트 단위 안에서 해석한다.

기본 원칙:
- parent task와 child task는 기본적으로 같은 프로젝트 안에 속한다.
- child task는 기존 task 범위를 넘는 별도 기여를 분리하기 위한 업무 단위다.
- child task는 별도 task이며 별도 main score 잠금 대상이 될 수 있다.

해석 규칙:
- 같은 task 내부 보완은 `task_submissions` version 증가로 처리한다.
- 범위 확장, 독립 검토 필요, 별도 기여 인정이 필요한 경우 child task로 분리한다.
- parent/child 관계는 점수 중복 방지와 범위 명확화 목적이다.

제품 1차 권장:
- cross-project child task는 허용하지 않는다.
- 즉, `parent_task.project_id = child_task.project_id`를 기본 원칙으로 둔다.

---

## 8. 권장 DB 테이블 초안

제품 레이어 기준 권장 테이블은 아래와 같다.

## 8.1 `teams`

예시 필드:
- `id`
- `name`
- `created_by`
- `created_at`
- `updated_at`

## 8.2 `team_members`

예시 필드:
- `id`
- `team_id`
- `user_id`
- `team_role` optional
- `joined_at`

기본 용도:
- 팀 소속 자체 저장

## 8.3 `projects`

예시 필드:
- `id`
- `team_id`
- `name`
- `description`
- `created_by`
- `created_at`
- `updated_at`

핵심 원칙:
- `team_id`는 필수

## 8.4 `project_members`

예시 필드:
- `id`
- `project_id`
- `user_id`
- `role`
- `joined_at`

핵심 원칙:
- `role`은 `owner / manager / member`

## 8.5 기존 task 관련 테이블과의 연결

기존 초안과 연결:
- `tasks.project_id -> projects.id`
- `task_submissions.task_id -> tasks.id`
- `task_bonus_logs.task_id -> tasks.id`
- `task_activity_logs.task_id -> tasks.id`

---

## 9. 제품 1차 범위

제품 1차에서 고정할 범위:
- 팀이 프로젝트의 상위 단위라는 구조
- 프로젝트별 멤버십과 역할 운영
- task는 프로젝트에 속한다는 원칙
- parent/child task는 같은 프로젝트 안에서 해석
- project overview와 sensitive review 권한의 기반이 프로젝트 멤버십이라는 점

---

## 10. 후순위 범위

후순위 또는 별도 정책으로 미루는 항목:
- 팀 레벨 세부 역할 체계 확장
- 프로젝트 간 task 이동
- cross-project child task
- 외부 협력자/게스트 멤버십
- 다중 팀 관리자 고급 정책

---

## 11. 구현 메모

- UI와 API는 항상 “현재 사용자가 어떤 team / project에 속하는가”를 먼저 기준으로 삼는다.
- 권한 체크는 프로젝트 멤버십을 기준으로 처리한다.
- 팀은 상위 컨테이너이고, 실제 작업/조회/권한 대부분은 프로젝트 단위에서 집행한다.

---

## 12. 연결 문구

이 문서는 아래 문서들과 직접 연결된다.

- `product_db_schema_draft`: `projects.team_id`, `tasks.project_id`, 멤버십 테이블 추가 방향의 기준점이 된다.
- `product_api_contract_draft`: 프로젝트/팀 기준 조회와 task 생성 경로의 상위 도메인 기준이 된다.
- `product_authorization_matrix`: `owner / manager / member` 역할이 프로젝트 멤버십 위에서 해석된다는 전제를 제공한다.
