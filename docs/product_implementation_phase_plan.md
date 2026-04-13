# Product Implementation Phase Plan

문서 상태: implementation-ready draft

## 1. 문서 목적

이 문서는 지금까지 정리된 문서를 실제 구현 순서로 접기 위해, 작업을 `1차 / 2차 / 3차`로 나눈 단계별 실행 계획을 정의한다.

목표:
- 한 번에 전체 구현하지 않는다.
- 기존 MVP 핵심 루프를 유지한다.
- additive migration 원칙을 지킨다.
- 단계별 범위, 리스크, 테스트 포인트, 완료 기준을 명확히 한다.

---

## 2. 전체 구현 원칙

- 새로운 제품 방향을 추가하지 않는다.
- 이미 확정된 문서를 구현 가능한 순서로 접는다.
- 평가 엔진 자체보다 제품 레이어 연결과 저장 구조 정리에 집중한다.
- 기존 검증 완료된 `submit / answer / retry`는 가능한 오래 유지한다.

---

## 3. 단계 개요

권장 구현 순서:

1. 1차: `task / submission / approval / score lock / activity log`
2. 2차: `team / project / membership / overview / sensitive review`
3. 3차: `auth / session / current user 기반 처리 및 프론트 연결`

이 순서는 “핵심 평가 흐름 안정화 -> 제품 구조 도입 -> 인증 기준 전환” 순서다.

---

## 4. 1차 구현 계획

## 4.1 범위

1차 범위:
- `tasks` 확장
- `task_submissions`
- `task_bonus_logs`
- `task_activity_logs`
- approve / request changes / close / cancel / reopen / delta bonus의 기본 처리
- score lock 구조 도입

## 4.2 목표

목표:
- 기존 task 중심 MVP를 깨지 않고 version 기반 저장 구조 도입
- approval 이후 main score 잠금
- bonus와 activity log 분리
- 기존 `submit / answer / retry`를 내부적으로 version 구조에 연결

## 4.3 산출물

- DB migration 초안
- task/submission/bonus/activity log 모델
- API 서버 로직의 version 연결
- activity log 저장 로직
- 기본 review 흐름 구현

## 4.4 리스크

- 기존 `tasks`만 전제로 한 로직과 충돌 가능성
- submit/answer/retry 흐름이 version 구조와 맞물리며 회귀 버그 발생 가능
- approve 이후 score lock과 bonus 집계 정합성 문제

## 4.5 테스트 포인트

- submit 시 새 submission version 생성 여부
- answer 시 해당 submission에만 답변 저장되는지
- retry 시 동일 task / 동일 submission 기준 복구되는지
- approve 시 `locked_main_score`와 `approved_version_no`가 정확히 저장되는지
- delta bonus 시 `total_delta_bonus`와 activity log가 함께 기록되는지
- request changes / close / cancel / reopen에 activity log가 남는지

## 4.6 완료 기준(DoD)

- 기존 MVP 핵심 루프가 계속 동작한다.
- task 1개에 여러 submission version을 저장할 수 있다.
- approve 이후 score lock이 반영된다.
- bonus와 activity log가 저장된다.
- 상태/점수/로그가 문서 기준과 일치한다.

## 4.7 지금 하지 말아야 하는 것

- 팀/프로젝트 화면 구조 확장
- 인증 방식 전면 교체
- member/manager UI 대규모 개편
- 소셜 로그인, SSO, 고급 권한 체계

---

## 5. 2차 구현 계획

## 5.1 범위

2차 범위:
- `teams`
- `team_members`
- `projects`
- `project_members`
- `tasks.project_id` 연결
- project overview / sensitive review 조회 계층
- 가시성 정책에 맞는 목록/상세 응답 분리

## 5.2 목표

목표:
- 제품 레이어의 상위 구조를 고정
- task가 프로젝트에 속한다는 기준 구현
- member overview 허용 / sensitive review 제한 구조 구현

## 5.3 산출물

- 팀/프로젝트/멤버십 테이블
- 프로젝트 기준 목록/상세 조회 API
- `view=overview`, `view=my`, `view=sensitive-review` 같은 조회 분기
- 프로젝트 기반 UI 뼈대

## 5.4 리스크

- 기존 task 데이터의 project 연결 백필 필요
- overview와 sensitive review 응답 경계가 애매할 수 있음
- 멤버십 없는 사용자의 접근 차단 처리 누락 가능

## 5.5 테스트 포인트

- 모든 task가 유효한 project에 연결되는지
- project membership 기준으로 task 목록 필터링이 되는지
- member가 overview는 볼 수 있고 sensitive review는 차단되는지
- manager/owner는 sensitive review를 볼 수 있는지
- parent/child task가 같은 project 안에서 해석되는지

## 5.6 완료 기준(DoD)

- team > project > task 구조가 DB/API/UI에 반영된다.
- 프로젝트 멤버십과 역할이 저장된다.
- overview와 sensitive review 조회가 분리된다.
- authorization matrix와 visibility policy의 기준이 API 응답에 반영된다.

## 5.7 지금 하지 말아야 하는 것

- cross-project child task
- 팀 레벨 고급 역할 체계
- 외부 게스트 멤버십
- 대규모 대시보드 리디자인

---

## 6. 3차 구현 계획

## 6.1 범위

3차 범위:
- auth/session 도입
- current user 기반 protected API 처리
- request body에서 user 식별값 제거
- 프론트 로그인/로그아웃/세션 유지 연결
- 현재 사용자 컨텍스트 기반 라우팅

## 6.2 목표

목표:
- 제품 인증 기준점 확정
- 서버가 세션 사용자 기준으로 creator/submitted_by/actor를 채우도록 전환
- 프론트가 로그인 상태와 프로젝트 진입 흐름을 갖도록 연결

## 6.3 산출물

- managed auth 연동
- current user resolver 또는 middleware
- protected API 공통 인증 처리
- 로그인/로그아웃/세션 유지 UI
- 현재 사용자 기반 프로젝트 진입 흐름

## 6.4 리스크

- 기존 프론트가 직접 user id를 전달하던 방식과 충돌 가능
- 세션 만료 처리와 라우팅 예외 처리 누락 가능
- 멤버십 검사와 인증 검사가 섞여 복잡해질 수 있음

## 6.5 테스트 포인트

- 비로그인 사용자가 protected API에 접근 차단되는지
- 로그인 사용자가 본인 권한 범위 프로젝트만 접근 가능한지
- task 생성 시 `creator_user_id`가 세션 사용자로 채워지는지
- submission 생성 시 `submitted_by`가 세션 사용자로 채워지는지
- approve / bonus / reopen 시 actor 계열 필드가 세션 사용자 기준으로 기록되는지
- 로그인 후 첫 진입이 내 작업 또는 프로젝트 선택 흐름으로 연결되는지

## 6.6 완료 기준(DoD)

- protected API가 current user 기준으로 동작한다.
- request body에서 사용자 식별값이 제거된다.
- 멤버십과 역할 검사가 인증 이후에 수행된다.
- 프론트 로그인/로그아웃/세션 흐름이 최소 기능으로 동작한다.

## 6.7 지금 하지 말아야 하는 것

- 소셜 로그인
- 2FA
- 조직 SSO
- 복잡한 조직 계층/외부 초대 플로우

---

## 7. 단계 간 의존성

의존성은 아래 순서를 권장한다.

- 1차는 단독으로 먼저 진행 가능
- 2차는 1차의 task/submission 구조 위에 얹는 것이 안전
- 3차는 2차까지의 프로젝트/멤버십 구조가 있어야 권한 검사가 자연스럽다

즉, 권장 흐름은 `1차 -> 2차 -> 3차`다.

---

## 8. 공통 리스크

모든 단계에 걸친 공통 리스크:
- 기존 MVP와 신규 구조가 일정 기간 혼재할 수 있음
- DB는 확장됐지만 UI/API가 부분 반영 상태일 수 있음
- 권한 정책과 가시성 정책이 구현 중 어긋날 수 있음

대응 원칙:
- 기존 엔드포인트를 가능한 래핑 유지
- activity log를 기준으로 상태 전이 추적
- overview / sensitive review / current user 검사를 분리해서 구현

---

## 9. 공통 테스트 전략

공통 테스트 전략:
- 상태 전이 테스트
- 권한 테스트
- 가시성 테스트
- current user 기반 actor 채움 테스트
- 회귀 테스트: 기존 submit / answer / retry 유지 여부

우선 자동화 권장 범위:
- submit / answer / retry
- approve / request changes / close / cancel / reopen
- project membership 권한 체크
- overview / sensitive review 응답 차이

---

## 10. 최종 메모

이 계획은 전체를 한 번에 구현하는 문서가 아니라, 이미 확정된 설계 문서를 실제 구현 순서로 접기 위한 실행 계획이다.

핵심은 아래 세 줄로 요약된다.
- 1차에서 평가 엔진 바깥의 저장 구조를 먼저 안정화한다.
- 2차에서 팀/프로젝트/가시성 구조를 얹는다.
- 3차에서 인증과 current user 기준으로 제품 레이어를 완성한다.
