# TeamBalance Deployment Guide

## 배포 구조
- Backend: Render
- Frontend: Vercel
- Database: Supabase

## Render 백엔드 배포 절차
1. Render에서 `New +` -> `Web Service`를 선택합니다.
2. 저장소를 연결합니다.
3. 아래 값으로 설정합니다.
   Root Directory: `backend`
   Build Command: `pip install -r requirements.txt`
   Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment Variables를 입력합니다.
5. Deploy를 실행합니다.

## Render 환경변수
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `SUPABASE_DB_URL`
- `ALLOWED_ORIGINS`
- `ENABLE_RUNTIME_SCHEMA_INIT`

예시:

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash-lite
SUPABASE_DB_URL=postgresql+psycopg2://postgres:password@host:5432/postgres
ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:3000,http://localhost:3000,https://your-frontend.vercel.app
ENABLE_RUNTIME_SCHEMA_INIT=true
```

## Vercel 프론트 배포 절차
1. Vercel에서 프로젝트를 import 합니다.
2. Frontend 정적 파일 기준으로 배포합니다.
3. 배포 후 프론트가 Render API를 바라보도록 `frontend/api.js`의 런타임 설정 중 하나를 사용합니다.

## Vercel 쪽 API 연결 방법
`frontend/api.js`는 아래 우선순위로 API 주소를 결정합니다.
1. `window.__TEAMBALANCE_CONFIG__.API_BASE_URL`
2. `window.__TEAMBALANCE_API_BASE_URL__`
3. `document.documentElement.dataset.apiBaseUrl`
4. 로컬 호스트면 `http://127.0.0.1:8000`
5. 그 외에는 `https://your-render-backend.onrender.com`

배포 시 권장 방법:
- 실제 배포 전에 `frontend/api.js`의 `DEFAULT_DEPLOY_API_BASE_URL`을 Render 백엔드 주소로 바꿉니다.
- 또는 프론트 HTML에서 `window.__TEAMBALANCE_CONFIG__ = { API_BASE_URL: "https://your-render-backend.onrender.com" }`를 먼저 주입합니다.

## CORS 연결 방법
- Backend는 `ALLOWED_ORIGINS` 환경변수를 쉼표 구분 문자열로 받아 리스트로 해석합니다.
- Vercel 도메인을 반드시 `ALLOWED_ORIGINS`에 추가해야 합니다.
- 로컬 개발용 origin은 기본값으로 유지됩니다.

## 배포 후 검증 체크리스트
1. Render 백엔드 health/API 접속이 되는지 확인
2. Vercel 프론트에서 로그인 요청이 성공하는지 확인
3. 브라우저 콘솔에 CORS 에러가 없는지 확인
4. `projects.html`에서 팀/프로젝트 조회가 되는지 확인
5. `index.html`에서 task list 조회와 제출 흐름이 되는지 확인
6. `dashboard.html`에서 contribution 조회가 되는지 확인
7. 회원가입/로그인/로그아웃/세션 복귀 흐름이 되는지 확인
8. 승인/보완 요청/bonus 후 `my` 화면이 정상 갱신되는지 확인

## 운영 메모
- 첫 배포 시 DB 스키마 보강이 필요하면 `ENABLE_RUNTIME_SCHEMA_INIT=true`로 시작할 수 있습니다.
- 운영이 안정화되면 스키마 변경은 별도 migration 절차로 관리하는 것이 안전합니다.
