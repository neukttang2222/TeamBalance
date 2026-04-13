# Product State Transition Policy v1
문서 상태: 초안 고정안
적용 대상: 제품화 1차 설계
목적: 작업 진행 상태와 AI 평가 상태를 분리하여 공정성과 운영 안정성을 확보한다

---

## 1. 문서 목적

현재 MVP는 아래 AI 평가 흐름을 기준으로 동작한다.

`TODO -> GENERATING_Q -> AWAITING_A -> SCORING -> DONE`
실패 시 `FAILED`

또한 상태별 허용 액션은 아래와 같다.

- TODO 에서만 submit 가능
- AWAITING_A 에서만 answer 가능
- FAILED 에서만 retry 가능
- DONE 수정 불가

제품화에서는 이 엔진 상태를 유지하되,
실제 협업/운영에 필요한 `작업 상태(work status)`를 별도로 둔다.

핵심 원칙:
- AI 평가 상태와 작업 상태를 분리한다
- AI 평가 엔진 상태는 버전(version) 단위로 관리한다
- 작업의 승인/보완/종료는 task 단위로 관리한다

---

## 2. 상태 모델 개요

제품화 상태 모델은 아래 3개 층으로 구성한다.

### 2.1 Task Work Status
프로젝트 업무 자체의 진행 상태

### 2.2 Evaluation Status
각 제출 버전에 대한 AI 평가 상태

### 2.3 Score Lock Status
점수 확정 여부

---

## 3. Task Work Status 정의

### 3.1 DRAFT
- task가 생성되었으나 아직 배정 또는 승인 전 상태
- 자기 생성 task를 허용하더라도, 점수 대상은 아님

허용 액션:
- 수정
- 담당자 지정
- 승인 요청
- 취소

### 3.2 ASSIGNED
- 담당자가 지정되었고 작업 시작 전 상태

허용 액션:
- 작업 시작
- task 상세 조회
- 취소

### 3.3 IN_PROGRESS
- 작업자가 실제 업무를 진행 중인 상태

허용 액션:
- 임시 저장
- 제출 준비
- 추가 메모 작성

### 3.4 SUBMITTED_FOR_REVIEW
- 작업자가 현재 버전을 제출했고 manager 검토 대기 중인 상태

허용 액션:
- manager 검토
- AI 평가 진행
- 보완 요청
- 승인 대기

### 3.5 CHANGES_REQUESTED
- manager가 보완 요청을 내린 상태
- 같은 task 안에서 새 버전 제출 가능

허용 액션:
- 보완 제출
- 추가 자료 반영
- 재검토 요청

### 3.6 APPROVED
- task의 핵심 산출물이 승인된 상태
- 최초 승인 시 본점수 잠금 가능

허용 액션:
- 읽기
- 예외적 addendum 등록
- child task 생성 검토

### 3.7 CLOSED
- 해당 task에 대한 본업무와 평가가 모두 마감된 상태

허용 액션:
- 조회만 가능

### 3.8 CANCELED
- 중복, 무효, 범위 변경 등으로 더 이상 유효하지 않은 상태

허용 액션:
- 조회만 가능

---

## 4. Evaluation Status 정의

Evaluation Status는 각 `submission version` 단위로 관리한다.
기존 MVP의 평가 엔진 상태를 유지한다.

### 4.1 TODO
- 해당 버전에 대한 AI 평가가 시작되기 전 상태

허용 액션:
- submit

### 4.2 GENERATING_Q
- AI 질문 생성 중

허용 액션:
- 대기

### 4.3 AWAITING_A
- AI 질문 생성 완료
- 사용자 답변 대기 중

허용 액션:
- answer

### 4.4 SCORING
- 사용자 답변 기반 AI 채점 중

허용 액션:
- 대기

### 4.5 DONE
- 해당 버전에 대한 AI 채점 완료
- raw_score / comment 확보 상태
- 아직 task 최종 승인 전일 수 있음

허용 액션:
- manager 검토
- 보완 요청
- 승인

### 4.6 FAILED
- 질문 생성 또는 채점 실패 상태

허용 액션:
- retry

---

## 5. Score Lock Status 정의

### 5.1 UNLOCKED
- 본점수가 아직 확정되지 않은 상태
- 임시 검증 결과만 존재

### 5.2 LOCKED
- manager 승인에 따라 본점수가 확정된 상태
- 대시보드 본점수 집계 대상

### 5.3 LOCKED_WITH_BONUS
- 본점수 잠금 이후 추가기여점수가 반영된 상태

---

## 6. 버전(version) 원칙

### 6.1 동일 task의 보완은 새 version으로 처리한다
예:
- Task A / v1 제출
- 보완 요청
- Task A / v2 제출

### 6.2 version마다 Evaluation Status를 가진다
예:
- v1: DONE
- v2: DONE
- v3: FAILED

### 6.3 version 점수는 모두 이력으로 저장한다
- 이전 버전 결과를 덮어쓰지 않는다
- 대시보드에는 잠금된 점수만 반영한다

---

## 7. 상태 전이 규칙

## 7.1 Task Work Status 흐름

### 기본 흐름
`DRAFT -> ASSIGNED -> IN_PROGRESS -> SUBMITTED_FOR_REVIEW -> APPROVED -> CLOSED`

### 보완 흐름
`SUBMITTED_FOR_REVIEW -> CHANGES_REQUESTED -> IN_PROGRESS -> SUBMITTED_FOR_REVIEW`

### 취소 흐름
`DRAFT -> CANCELED`
`ASSIGNED -> CANCELED`
`IN_PROGRESS -> CANCELED`

### 운영 원칙
- APPROVED 이후 동일 task의 본점수는 잠금 가능
- APPROVED 이후 추가 범위는 addendum 또는 child task로 분리 검토
- CLOSED는 사실상 최종 종료 상태

---

## 7.2 Evaluation Status 흐름

각 버전에 대해 아래 흐름을 따른다.

`TODO -> GENERATING_Q -> AWAITING_A -> SCORING -> DONE`
실패 시:
`FAILED`

retry 규칙:
`FAILED -> retry -> 직전 재개 가능 상태로 복구`

권장 구현:
- 질문 생성 실패 시 `TODO` 또는 `GENERATING_Q` 재개
- 채점 실패 시 `AWAITING_A` 또는 `SCORING` 재개
- 세부 실패 단계는 `failed_stage`로 저장

---

## 7.3 Score Lock Status 흐름

### 본점수 확정 전
`UNLOCKED`

### manager 승인 시
`UNLOCKED -> LOCKED`

### 승인 후 추가기여 반영 시
`LOCKED -> LOCKED_WITH_BONUS`

예외 reopen:
- 매우 제한적으로만 허용
- reopen 하더라도 기존 잠금 점수는 이력으로 보존

---

## 8. 상태별 허용 액션 매트릭스

### 8.1 Worker 기준

#### DRAFT
- 본인 초안 수정 가능
- 제출 불가
- 점수 없음

#### ASSIGNED
- 작업 시작 가능

#### IN_PROGRESS
- 작업 내용 작성/수정 가능
- 제출 가능

#### SUBMITTED_FOR_REVIEW
- 직접 수정 불가
- manager 결정 대기
- 필요 시 코멘트 확인

#### CHANGES_REQUESTED
- 보완 후 새 version 제출 가능

#### APPROVED
- 일반 수정 불가
- addendum 요청 가능

#### CLOSED / CANCELED
- 조회만 가능

### 8.2 Manager 기준

#### DRAFT
- 승인/배정/취소 가능

#### ASSIGNED
- 담당자 변경 가능
- 취소 가능

#### IN_PROGRESS
- 진행 확인 가능

#### SUBMITTED_FOR_REVIEW
- 보완 요청 가능
- 승인 가능
- child task 전환 검토 가능

#### CHANGES_REQUESTED
- 추가 안내 가능

#### APPROVED
- 본점수 잠금
- delta bonus 승인
- child task 생성 승인

#### CLOSED
- 조회만 가능

#### CANCELED
- 조회만 가능

### 8.3 System 기준

#### TODO
- 질문 생성 시작

#### GENERATING_Q
- 질문 JSON 반환
- 실패 시 FAILED

#### AWAITING_A
- 답변 수신 대기

#### SCORING
- 점수 계산
- 실패 시 FAILED

#### DONE
- raw_score / comment 저장
- provisional score 계산

#### FAILED
- retry 대기

---

## 9. 점수 잠금 규칙

### 9.1 DONE은 곧바로 최종점수가 아니다
- DONE은 해당 버전의 AI 채점 완료 상태일 뿐
- manager 승인 전까지는 `임시 검증 결과`다

### 9.2 APPROVED 시점에 잠금한다
- manager가 해당 version을 승인하면
  - 해당 version의 provisional score를 main score로 잠금
  - approved_version_no 기록
  - score_locked_at 기록

### 9.3 잠금 이후 수정 처리
- 잠금 이후 보완은 본점수 재산정이 아니라
  - delta bonus
  - addendum
  - child task
  중 하나로 처리한다

---

## 10. 보완 요청과 child task 분기 기준

### 10.1 보완 요청으로 처리하는 경우
- 기존 task_goal 범위 안의 보강
- 추가 자료 첨부
- 설명 보완
- 누락 항목 정리

처리:
- 같은 task의 새 version
- main score 재지급 없음
- 필요 시 delta bonus

### 10.2 child task로 처리하는 경우
- 기존 범위를 넘어서는 조사/구현
- 새 산출물이 독립 검토 대상
- manager가 별도 기여로 판단

처리:
- 새 task 생성
- 독립 상태 흐름
- 별도 main score 가능

---

## 11. 실패 및 복구 정책

### 11.1 평가 실패
- 기존 MVP 정책 유지
- FAILED 상태에서만 retry 가능

### 11.2 retry 원칙
- 동일 task / 동일 version 기준 복구 우선
- 새 row 복제 방식 지양
- 실패 단계 기록 유지

### 11.3 사용자 가시성
- FAILED 원인은 사용자용 메시지와 운영용 메시지를 구분한다
- 사용자에게는 재시도 가능 여부를 함께 표시한다

---

## 12. 권장 저장 필드

### Task 단위
- work_status
- score_lock_status
- base_points
- locked_main_score
- total_delta_bonus
- approved_version_no
- approved_by
- approved_at
- closed_at

### Submission Version 단위
- task_id
- version_no
- content
- evaluation_status
- ai_question
- user_answer
- raw_score
- ai_factor
- provisional_score
- ai_comment
- failed_stage
- error_message
- submitted_at
- scored_at

### Bonus Log 단위
- task_id
- version_no
- delta_bonus
- reason
- approved_by
- approved_at

---

## 13. UI 반영 원칙

### 내 작업 화면
- Task Work Status 중심 표시
- 본인 진행 업무 우선 노출

### 프로젝트 전체 화면
- 담당자
- work_status
- 승인 여부
- 제출 여부
- 본점수/추가기여점수 요약 표시

### task 상세 화면
- version 이력 표시
- 현재 임시 점수와 잠금 점수 구분 표시
- 보완 요청 코멘트 표시
- FAILED 시 retry 노출

---

## 14. 최종 정책 한 줄 요약

작업 상태와 AI 평가 상태를 분리하고,
AI 채점 완료(DONE)는 임시 결과로 보며,
manager 승인 시에만 점수를 잠금한다.