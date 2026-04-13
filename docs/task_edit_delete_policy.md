# Task Edit/Delete Policy

## 편집/삭제 허용 상태

- 편집 가능: `status == TODO`
- 삭제 가능: `status == TODO`
- 편집/삭제 불가: `GENERATING_Q`, `AWAITING_A`, `SCORING`, `DONE`, `FAILED`

`AWAITING_A` 이후 상태에서는 제출/평가/검토 이력이 연결될 수 있으므로 수정/삭제를 허용하지 않습니다.

## 권한 기준

- 허용 role: `owner`, `manager`
- 비허용 role: `member`

backend와 frontend 모두 `owner / manager + TODO` 조건을 함께 만족할 때만 편집/삭제를 허용합니다.

## 수정 가능한 필드

- `task title`
- `task type`
- `task goal`
- `assignee`
- `task weight`

기존 제출/평가/검토 흐름과 연결되는 필드는 이번 턴에서 변경하지 않습니다.

## Assignee 정책

- assignee는 현재 프로젝트 멤버여야 합니다.
- frontend 편집 팝업에서도 기존 생성 팝업과 동일하게 현재 프로젝트 멤버만 검색/선택합니다.
- 단일 assignee 선택 정책을 유지합니다.
- backend는 `assignee must be a project member` 검증으로 최종 방어합니다.

## 삭제 제한 이유

- 제출 이후 task는 평가/검토 이력 보존이 필요합니다.
- 따라서 `TODO` 상태 task만 삭제할 수 있습니다.
- 이번 구현은 `TODO` 상태에서만 삭제를 허용해 연결 이력 정합성 리스크를 최소화합니다.

## 수동 테스트 체크리스트

1. owner/manager가 `TODO` task에서 `편집` 버튼을 볼 수 있는지 확인
2. member는 `TODO` task여도 `편집` 버튼이 보이지 않는지 확인
3. `TODO` task 편집 팝업이 열리는지 확인
4. `title/type/goal/assignee/weight` 수정 후 저장이 정상 동작하는지 확인
5. 프로젝트 멤버가 아닌 assignee로 저장 시 backend에서 차단되는지 확인
6. `TODO` task 삭제 confirm 후 삭제가 정상 동작하는지 확인
7. 삭제 후 task 리스트와 상세 영역이 자연스럽게 갱신되는지 확인
8. `AWAITING_A` 이후 상태 task에서 편집/삭제 버튼이 보이지 않는지 확인
9. 기존 `submit / answer / review` 흐름 회귀가 없는지 확인

## 남은 리스크

- 자동화 테스트가 아직 없어 role/status 조합 회귀는 수동 확인 비중이 높습니다.
- frontend는 기존 생성 모달을 재사용하므로, 이후 모달 문구나 구조가 바뀌면 생성/편집 모드 모두 함께 점검해야 합니다.
- `TODO` 상태인데도 비정상 데이터가 남아 있는 예외 케이스는 backend의 상태 검증과 최신 submission 확인으로만 제한적으로 방어합니다.
