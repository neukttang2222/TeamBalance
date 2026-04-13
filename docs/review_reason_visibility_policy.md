# Review Reason Visibility Policy

## 당사자 검토 사유 공개 정책
- task 담당자는 `my(내 작업)` 화면에서 자신의 task에 대한 최근 검토 결과를 읽기 전용으로 확인할 수 있어야 한다.
- 공개 대상은 최근 `보완 요청` 또는 `승인` 검토 결과다.
- 노출 위치는 `index.html`의 task detail 내부이며, 입력 UI가 아니라 읽기 전용 피드백 박스로 표시한다.

## 보완 요청 사유 우선 공개 이유
- `보완 요청`은 담당자가 다음 작업을 진행하기 위해 반드시 알아야 하는 운영 피드백이다.
- 따라서 `REQUEST_CHANGES` 로그의 사유는 담당자에게 반드시 노출한다.
- 표시 형태는 `검토 상태: 보완 요청`과 `검토 의견` 본문으로 구성한다.

## 승인 사유 공개 정책
- 승인 처리 시 입력한 사유가 있으면 담당자에게 읽기 전용으로 공개한다.
- 승인 사유가 비어 있으면 `검토 상태: 승인 완료`만 보여주고, 의견 본문 박스는 숨길 수 있다.

## 화면별 공개 범위
- `my`
  최근 승인/보완 요청 검토 사유를 읽기 전용으로 공개한다.
- `overview`
  검토 사유를 기본 노출하지 않는다.
- `검토`
  manager/owner 입력 UI와 내부 상세는 기존대로 유지한다.

## 데이터 소스
- 검토 사유는 task activity log metadata를 사용한다.
- 승인 사유:
  `APPROVE` 로그의 `metadata.comment`
- 보완 요청 사유:
  `REQUEST_CHANGES` 로그의 `metadata.reason`
- 화면에는 task 기준 가장 최근 review action 하나만 표시한다.

## 수동 테스트 체크리스트
- 보완 요청된 task를 담당자가 `my` 화면에서 열면 사유가 보이는지 확인
- 승인된 task를 담당자가 `my` 화면에서 열면 승인 사유가 보이는지 확인
- 승인 사유가 비어 있을 때 상태만 자연스럽게 보이는지 확인
- `overview`에서는 검토 사유가 계속 보이지 않는지 확인
- manager/owner 검토 입력 UI가 그대로 유지되는지 확인
- task A의 검토 사유가 task B로 이동했을 때 남지 않는지 확인
- submit / answer / approve / request changes 흐름에 회귀가 없는지 확인

## 남은 리스크
- 현재는 최근 `APPROVE` 또는 `REQUEST_CHANGES` 로그 하나만 표시하므로, 여러 차례 검토 이력이 있는 task의 과거 의견 히스토리는 따로 보여주지 않는다.
- activity log metadata 형식이 바뀌면 프론트 파싱도 함께 맞춰야 한다.
