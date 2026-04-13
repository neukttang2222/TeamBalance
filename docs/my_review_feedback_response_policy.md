# My Review Feedback Response Policy

## 문제 현상
- `my(내 작업)` 화면에 검토 의견 박스를 추가했더라도, 실제 브라우저에서는 박스가 보이지 않았다.
- 원인은 프론트가 읽을 수 있는 당사자용 최신 검토 사유 필드가 `my` 응답에 없었기 때문이다.
- 기존에는 프론트가 `activity_logs`를 추정 파싱해야 했지만, `my` 응답에는 그 데이터가 안정적으로 포함되지 않았다.

## backend 응답 보강 방식
- `backend/app/services/project_service_phase2.py`의 `my` serializer에서 최신 review action을 직접 가공한다.
- task 기준 최근 review action 중 아래 두 종류만 본다.
  - `REQUEST_CHANGES`
  - `APPROVE`
- 가장 최근 1개의 action을 선택해 당사자용 review feedback 필드로 응답한다.

## 신규 응답 필드 정의
- `latest_review_feedback_type`
  - `changes_requested`
  - `approved`
  - `null`
- `latest_review_feedback_reason`
  - review reason 문자열 또는 `null`
- `latest_review_feedback_at`
  - 최신 review action 생성 시각 ISO datetime 또는 `null`

## backend 데이터 소스
- review reason은 task activity log metadata에서 읽는다.
- `REQUEST_CHANGES`
  - `metadata.reason`
- `APPROVE`
  - `metadata.comment`

## frontend 표시 조건
- `index.html`의 `my` 화면에서만 표시한다.
- `latest_review_feedback_type` 또는 `latest_review_feedback_reason`가 있을 때 읽기 전용 `검토 의견` 박스를 노출한다.
- 사유가 없으면 상태만 보여주고, 본문 박스는 숨길 수 있다.
- task 전환 시 현재 선택 task 기준으로 내용을 다시 렌더링한다.

## 화면별 공개 범위
- `my`
  - 당사자용 최신 검토 결과 공개
- `overview`
  - 검토 의견 비노출
- `검토`
  - manager/owner 입력 UI와 내부 상세 유지

## 수동 테스트 체크리스트
- 보완 요청된 task를 담당자가 `my` 화면에서 열면 검토 의견 박스가 보이는지 확인
- 그 안에 보완 요청 사유가 실제로 표시되는지 확인
- 승인된 task를 담당자가 `my` 화면에서 열면 승인 사유가 표시되는지 확인
- review action이 없는 task는 검토 의견 박스가 숨겨지는지 확인
- `overview`에서는 검토 의견 박스가 보이지 않는지 확인
- task A의 검토 의견이 task B로 이동했을 때 남지 않는지 확인
- submit / answer / approve / request changes / bonus 흐름에 회귀가 없는지 확인

## 남은 리스크
- 현재는 최신 review action 1개만 공개하므로, 과거 review history 전체는 별도 제공하지 않는다.
- activity log metadata 키가 바뀌면 backend 가공 로직도 함께 수정해야 한다.
