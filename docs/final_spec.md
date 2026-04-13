# Final Spec

## 1. Project Overview
프로젝트명: AI 기반 팀 프로젝트 실질 기여도 평가 및 어뷰징 검증 솔루션

목표:
팀 프로젝트에서 각 팀원의 실질 기여도를 정량적으로 평가한다.
사용자가 task 결과물을 텍스트로 제출하면,
AI가 역질문 1개를 생성하고,
사용자가 답변하면,
AI가 1~5점으로 채점하여 기여도를 계산한다.

## 2. MVP Goal
이번 MVP의 핵심은 아래 단일 루프를 끊김 없이 구현하는 것이다.

Task 생성
-> 결과물 제출
-> AI 역질문 1개 생성
-> 사용자 답변 제출
-> AI 채점
-> 기여도 점수 반영
-> 대시보드 표시

## 3. Tech Stack
- Backend: FastAPI
- Database: Supabase (PostgreSQL)
- AI: Gemini 무료 티어 (`gemini-2.5-flash-lite`)
- Frontend: HTML / CSS / JavaScript
- Deployment: 후순위 (로컬 개발 우선)

## 4. Scope Rules

### 포함
- 텍스트 기반 task 생성
- 텍스트 기반 결과물 제출
- AI 질문 생성
- AI 답변 채점
- 팀원별 기여도 집계
- 대시보드 표 표시

### 제외
- 파일 업로드
- 링크 분석
- 다중 질문-답변 루프
- 고급 인증/권한 관리
- 실시간 동기화 고도화
- 차트 우선 구현
- 관리자 기능 고도화

## 5. Core User Flow
1. 사용자가 프로젝트 안에서 task를 생성한다.
2. 사용자가 task 결과물을 텍스트로 제출한다.
3. 시스템은 AI에게 질문 생성을 요청한다.
4. AI가 역질문 1개를 생성한다.
5. 사용자는 질문에 답변한다.
6. 시스템은 AI에게 채점을 요청한다.
7. AI가 raw_score와 comment를 반환한다.
8. 시스템은 weighted_score를 계산한다.
9. 대시보드에 팀원별 점수를 반영한다.

## 6. Status Flow
기본 상태 흐름:

TODO
-> GENERATING_Q
-> AWAITING_A
-> SCORING
-> DONE

실패 시:
FAILED

## 7. Status Action Rules
- TODO 에서만 submit 가능
- AWAITING_A 에서만 answer 가능
- FAILED 에서만 retry 가능
- DONE 은 수정 불가

## 8. Input Policy
- 파일 업로드 금지
- 링크 입력 금지
- 텍스트 복사-붙여넣기만 허용

## 9. Scoring Policy
- `raw_score`: AI가 부여하는 1~5 정수 점수
- `task_weight`: 1 / 2 / 3 만 허용
- `weighted_score = raw_score * task_weight`

가중치 의미:
- 1 = 하
- 2 = 중
- 3 = 상

## 10. AI Policy
- 모델: `gemini-1.5-flash`
- 질문 생성: 정확히 1개
- 질문 생성 temperature = 0.2
- 채점 temperature = 0.0
- 구조화 출력(JSON) 강제
- 질문 생성 실패 시 fallback 질문 허용
- 채점 실패 시 fallback 없이 FAILED 처리
- 1초 대기 후 1회 재시도

## 11. AI Output Contract

### Question generation
```json
{"question":"..."}
```

### Answer scoring
```json
{"raw_score":3,"comment":"..."}
```

## 12. Database Tables

### users
- id
- email
- name
- created_at

### projects
- id
- title
- owner_id
- created_at

### project_members
- id
- project_id
- user_id
- joined_at

### tasks
- id
- project_id
- user_id
- title
- task_type
- task_goal
- task_weight
- content
- ai_question
- user_answer
- raw_score
- weighted_score
- ai_comment
- status
- failed_stage
- error_message
- created_at
- updated_at
- submitted_at
- scored_at

## 13. API Contracts
- POST `/tasks`
- POST `/tasks/{task_id}/submit`
- POST `/tasks/{task_id}/answer`
- POST `/tasks/{task_id}/retry`
- GET `/projects/{project_id}/contribution`

## 14. Frontend Rules

### Screens
- Task Workspace
- Project Dashboard

### TaskCreator form
- `project_id`: 자동 주입 또는 select
- `title`: text input
- `task_type`: text 또는 select
- `task_goal`: textarea
- `task_weight`: select(1/2/3)

### TaskDetailView states
- TODO: 결과물 제출 폼
- GENERATING_Q: 질문 생성 중 로딩
- AWAITING_A: 질문 표시 + 답변 입력
- SCORING: 채점 중 로딩
- DONE: `raw_score`, `weighted_score`, `ai_comment` 표시
- FAILED: 에러 메시지 + retry 버튼

### Dashboard
- 우선 표 형태
- 표시 컬럼:
  - 이름
  - completed_tasks
  - total_weighted_score
- 차트는 backlog

## 15. Definition of Done
이번 MVP에서 완료로 보는 기준은 다음과 같다.

- Task 생성 가능
- 결과물 제출 가능
- 질문 생성 가능
- 답변 제출 가능
- 점수 계산 가능
- 대시보드 반영 가능
- 실패 시 retry 가능