# 수학공부방 관리 시스템 - 개발 계획

## 개발 환경 설정

```bash
# 모든 명령은 프로젝트 루트(228/)에서 실행
# Python 환경: pyenv 3.12.12 + uv venv (backend/.venv)

# 백엔드 의존성 설치
uv pip install -r backend/requirements.txt -p backend/.venv/bin/python

# 백엔드 실행
backend/.venv/bin/uvicorn app.main:app --reload --port 8000 --app-dir backend

# 프론트엔드 실행 (Node.js 필요 - 별도 설치)
npm run dev --prefix frontend
```

> **주의**:
> - 모든 명령은 **프로젝트 루트(`228/`)** 기준으로 실행한다. `cd backend/frontend` 하지 않는다.
> - 모든 Python 명령은 반드시 `backend/.venv` 가상환경을 통해 실행한다.
> - `uv`로 생성한 venv이므로 `pip` 대신 `uv pip`을 사용한다.

---

## Context

수학공부방 원장님을 위한 학생/수업/출석/수업료 통합 관리 웹앱을 처음부터 개발한다.
현재 코드가 없는 초기 상태이며, SPEC.md 문서가 준비되어 있다.
핵심 가치는 **8회차 사이클 기반 출석 관리 → 학부모 수업료 안내 메시지 생성** 워크플로우이다.

---

## Phase 의존성 그래프

```
Phase 1 (프로젝트 세팅)
   └──> Phase 2 (수업반 관리)
           └──> Phase 3 (학생 관리)
                   ├──> Phase 4 (출석 + 8회차 사이클) ★ 핵심
                   │       ├──> Phase 5 (수업료 + 메시지)
                   │       │       └──> Phase 5.1 (수업등록 + 스케줄 기반 출석) ★ 핵심 변경
                   │       │               ├──> Phase 5.2 (수업등록 관리 페이지)
                   │       │               └──> Phase 5.3 (수업시작 연동 + 시드 데이터) ← NEW
                   │       └──> Phase 6 (보충수업)
                   └──> Phase 7 (대시보드 + UI 개선)
                           └──> Phase 8 (학습관리 + 현금영수증)
```

---

## Phase 1: 프로젝트 세팅 및 기반 구조

**목표**: 백엔드/프론트엔드 스캐폴딩, 양쪽 개발 서버가 통신 가능한 상태

### 백엔드
- `backend/app/main.py` - FastAPI 앱, CORS 설정, health check
- `backend/app/database.py` - SQLAlchemy 엔진, SessionLocal, Base, get_db
- `backend/app/config.py` - 설정값
- `backend/requirements.txt` - fastapi, uvicorn, sqlalchemy, pydantic

### 프론트엔드
- Vite + React + TypeScript 프로젝트 생성
- Tailwind CSS + shadcn/ui 초기화
- react-router-dom 설치
- `vite.config.ts` - `/api` 프록시 → `localhost:8000`
- `Layout.tsx` + `Sidebar.tsx` - 사이드바 레이아웃
- 빈 `Dashboard.tsx` 페이지

### 완료 기준
- 백엔드 `uvicorn` + 프론트엔드 `npm run dev` 구동
- 브라우저에서 레이아웃 보이고 `/api/health` 호출 정상

---

## Phase 2: 수업반 관리 (CRUD)

**목표**: 수업반 생성/조회/수정/삭제

### DB 모델: `class_groups`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(50) UNIQUE | 수업반명 |
| days_of_week | VARCHAR(20) | JSON 배열: ["mon","wed"] |
| start_time | VARCHAR(5) | "14:30" |
| default_duration_minutes | INTEGER | 기본 수업시간(분) |
| memo | TEXT | |
| is_active | BOOLEAN | soft delete용 |
| created_at / updated_at | DATETIME | |

### API
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/class-groups` | 목록 |
| GET | `/api/class-groups/{id}` | 상세 |
| POST | `/api/class-groups` | 생성 |
| PUT | `/api/class-groups/{id}` | 수정 |
| DELETE | `/api/class-groups/{id}` | 삭제 (soft) |

### 프론트엔드
- `ClassGroups.tsx` - 목록 테이블 + 추가/수정 다이얼로그
- shadcn/ui: Table, Button, Dialog, Input, Select, Badge

### 시드 데이터
5개 반: 월수반A(14:30/90분), 월수반B(16:30/120분), 화목반A(14:30/90분), 화목반B(16:30/120분), 화목반C(20:00/120분)

---

## Phase 3: 학생 관리

**목표**: 학생 CRUD + 학년별 수업료 매핑 + 첫 사이클 자동 생성

### DB 모델: `students`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(20) | 이름 |
| phone | VARCHAR(20) | 학생 연락처 |
| school | VARCHAR(50) | 학교 |
| grade | VARCHAR(10) | elementary/middle1/middle2/middle3/high |
| parent_phone | VARCHAR(20) | 학부모 연락처 |
| class_group_id | FK | 소속 수업반 |
| tuition_amount | INTEGER | 개별 수업료 (NULL→학년 기본) |
| memo, is_active, created_at, updated_at | | |

### DB 모델: `cycles` (테이블만 생성, 로직은 Phase 4)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER PK | |
| student_id | FK | |
| cycle_number | INTEGER | N번째 사이클 |
| current_count | INTEGER | 현재 회차 (0~8) |
| total_count | INTEGER | 기본 8 |
| status | VARCHAR(20) | in_progress / completed |
| started_at / completed_at | DATE | |

### 학년 상수 (`constants.py`)
```
elementary: 90분, 24만 / middle1: 120분, 32만
middle2: 120분, 35만 / middle3: 120분, 35만 / high: 120분, 40만
```

### API
- GET/POST/PUT/DELETE `/api/students` + `/{id}`
- 학생 등록 시 → 첫 Cycle 자동 생성 (트랜잭션)

### 프론트엔드
- `Students.tsx` - 목록/등록/수정, 수업반별 필터, 학년→수업료 자동표시

---

## Phase 4: 출석 관리 + 8회차 사이클 (★ 핵심)

**목표**: 출석 체크 → 회차 자동 차감 → 8회차 도달 알림

### DB 모델: `attendance`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER PK | |
| student_id, cycle_id | FK | |
| date | DATE | 수업 날짜 |
| status | VARCHAR(20) | present/late/early_leave/absent/absent_excused |
| counts_toward_cycle | BOOLEAN | 회차 차감 여부 |
| excuse_reason | VARCHAR(50) | school_event/sick_leave/class_cancelled |
| memo | TEXT | |

### 핵심 비즈니스 로직 (`cycle_service.py`)
```
출석 기록 → counts_toward_cycle=True → current_count += 1
  → 8 도달 → status="completed" → 알림
```

### API
- GET/POST/PUT/DELETE `/api/attendance`
- POST `/api/attendance/bulk` - 수업반 일괄 출석
- GET `/api/attendance/daily/{date}` - 일일 현황
- GET `/api/cycles/alerts` - 완료/임박 알림
- POST `/api/cycles/{id}/new-cycle` - 새 사이클 시작

### 프론트엔드
- `Attendance.tsx` - 날짜 선택 → 요일 기반 수업반 자동 필터 → 학생별 출석 버튼 → 현재 회차(N/8) 표시
- `Dashboard.tsx` 업데이트 - 오늘 수업, 완료 임박(7/8+), 미처리 항목

---

## Phase 5: 수업료 관리 + 학부모 메시지 생성

**목표**: 사이클 완료 → 메시지 생성 → 클립보드 복사 → 입금 확인

### DB 모델: `payments`
- student_id, cycle_id, amount, payment_method, status(pending/paid)
- message_sent, message_sent_at, paid_at, memo

### 핵심 워크플로우
1. 사이클 완료 → Payment 자동 생성 (pending)
2. 메시지 생성 → 클립보드 복사 → 카카오톡 전송
3. 입금 확인 → paid 처리
4. 새 사이클 시작

### 프론트엔드
- `Payments.tsx` - 미납 목록, 메시지 생성/복사, 입금 확인

---

## Phase 5.1: 수업등록 관리 + 스케줄 기반 출석 (★ 핵심 변경)

**목표**: 수업등록 절차 관리 + 선불 수업료 + 스케줄 기반 출석 자동 생성

> Phase 5.1은 기존 Phase 3~5의 워크플로우를 대폭 변경한다.
> - 학생 상태 관리 (문의→레벨테스트→수업중→수업종료)
> - 출석 방식: 수동 체크 → **스케줄 미리 생성 (기본 출석)**
> - 수업료: 후불 → **선불 (납부 확인 후 사이클 시작)**

### A. 수업등록 상태 관리

#### 상태 흐름

```
문의(inquiry) → 레벨테스트(level_test) → 수업중(active) → 수업종료(stopped)
                                            ↑                    │
                                            └────── 재등록 ──────┘
```

| 상태 | 값 | 설명 |
|------|-----|------|
| 문의 | `inquiry` | 학부모 전화 문의, 아직 결정 전 |
| 레벨테스트 | `level_test` | 레벨테스트 진행 중/완료 |
| 수업중 | `active` | 정상 수업 진행 중 (출석/회차 대상) |
| 수업종료 | `stopped` | 수업 중지 또는 종료 (동일 취급) |

**허용 전이**:
- inquiry → level_test, active, stopped
- level_test → active, stopped
- active → stopped
- stopped → active (재등록)

#### DB 변경: Student 모델
- `is_active` (Boolean) → `enrollment_status` (VARCHAR 20, default="inquiry")

#### DB 신규: `enrollment_history` 테이블 (이력 관리)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER PK | |
| student_id | FK → students | |
| from_status | VARCHAR(20), nullable | 이전 상태 (첫 등록 시 NULL) |
| to_status | VARCHAR(20) | 변경된 상태 |
| changed_at | DATETIME | 변경 시점 (문의일자, 레벨테스트일자, 수업시작일자, 수업종료일자) |
| memo | TEXT, nullable | 변경 사유/메모 |

#### API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/students/{id}/status` | 상태 변경 + 이력 자동 기록 |
| GET | `/api/students/{id}/history` | 이력 조회 |

---

### B. 스케줄 기반 출석 (★ 핵심 변경)

> **변경 전**: 출석 날마다 수동으로 출석 버튼 클릭 → Attendance 레코드 생성
> **변경 후**: 사이클 시작 시 수업반 요일 기준 **8회차 Attendance 레코드를 미리 생성** (status=present)

#### 스케줄 생성 예시

월수반 학생, 수업시작일 2026-02-02:
```
1회: 2.2(월) present ✓     5회: 2.16(월) present ✓
2회: 2.4(수) present ✓     6회: 2.18(수) present ✓
3회: 2.9(월) present ✓     7회: 2.23(월) present ✓
4회: 2.11(수) present ✓    8회: 2.25(수) present ✓
```

- 위 8회차 스케줄이 **미리 생성**됨 (기본 status=present)
- 출석 화면에서는 결석/지각 등 **예외만 변경**
- **스케줄 범위 밖의 날짜에는 해당 학생이 출석 화면에 안 보임**
- 출석 UI는 기존 방식 유지 (날짜 선택 → 수업반 → 학생 목록)

#### 결석(미차감) → 스케줄 연장

미차감 결석(absent_excused) 처리 시 → 마지막 스케줄 다음 수업 요일에 1회 추가

```
예: 2.11(수) 미차감 결석 처리
→ 기존 마지막 8회: 2.25(수)
→ 9회차 추가: 3.2(월) present ✓  (다음 도래 수업일)
```

- 제한 없이 미차감 횟수만큼 연장
- cycle.total_count도 그만큼 증가 (8 → 9 → 10 ...)

---

### C. 선불 수업료 + 납부 확인 후 사이클 시작

> **변경 전**: 8회차 완료 → Payment 자동 생성 (후불)
> **변경 후**: 수업료 납부 완료(paid) → 사이클 시작 + 스케줄 생성 (선불)

#### 신규 학생 플로우

```
1. 학생 등록 (enrollment_status=inquiry)
2. 상태 변경: inquiry → level_test → active
3. 첫 수업료 Payment 수동 생성 (pending)
4. 수업료 납부 확인 (paid)
5. "사이클 시작" → Cycle 생성 + 8회차 스케줄 자동 생성
```

#### 기존 학생 플로우 (다음 사이클)

```
1. 현재 8회차 완료 → 다음 사이클 Payment 자동 생성 (pending)
2. 학부모 메시지 생성/발송
3. 수업료 납부 확인 (paid)
4. "다음 사이클 시작" 버튼 → 다음 도래 수업일부터 8회차 스케줄 자동 생성
```

**핵심**: Payment가 **paid** 상태여야 다음 사이클 시작 가능

---

### D. 기존 시스템 변경 영향

| 기존 동작 | 변경 후 |
|-----------|---------|
| 학생 등록 시 Cycle 자동 생성 | 학생 등록 시 Cycle 생성 안 함. active + 납부 확인 후 생성 |
| `is_active` (Boolean) | `enrollment_status` (4가지 상태) |
| 출석 수동 생성 (POST) | 사이클 시작 시 8회차 미리 생성 (기본 출석) |
| 출석 화면: 수업반 전체 학생 | 출석 화면: 해당 날짜에 스케줄 있는 학생만 |
| 수업료 후불 (8회 완료 후 청구) | 수업료 선불 (납부 확인 → 사이클 시작) |
| cycle.current_count += 1 (출석마다) | 미리 생성된 출석의 counts_toward_cycle 기준으로 계산 |

---

## Phase 5.2: 수업등록 관리 페이지

**목표**: 수업등록 절차를 전담하는 별도 페이지 (대시보드와 같은 레벨). Students.tsx는 학생 기본정보 CRUD만 담당하도록 역할 분리.

### 핵심 변경

1. **Enrollment.tsx** (신규) - 탭+테이블 파이프라인 뷰로 수업등록 상태 관리
2. **Students.tsx** 경량화 - 상태변경/이력/사이클시작 제거 → 기본정보 CRUD만
3. **Student 모델** - 레벨테스트 관련 필드 추가
4. **상태별 일자** - EnrollmentHistory의 changed_at에서 계산하여 API 응답에 포함

---

### A. 백엔드 변경

#### Student 모델 필드 추가 (`backend/app/models/student.py`)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| level_test_date | DATE, nullable | 레벨테스트 예정일 |
| level_test_time | VARCHAR(5), nullable | 예정 시간 "14:00" |
| level_test_result | TEXT, nullable | 테스트 결과/메모 |

#### 스키마 변경 (`backend/app/schemas/student.py`)

StudentResponse에 추가:
- `level_test_date`, `level_test_time`, `level_test_result` (레벨테스트 정보)
- `inquiry_date`, `level_test_status_date`, `active_date`, `stopped_date` (상태별 일자, EnrollmentHistory에서 계산)

신규 스키마:
- `LevelTestUpdate`: date, time, result

#### 신규 API

| Method | Path | 설명 |
|--------|------|------|
| PUT | `/api/students/{id}/level-test` | 레벨테스트 일정/결과 업데이트 |

#### `_to_response` 수정

`db` 파라미터 추가 → EnrollmentHistory에서 각 상태별 최초 전환 일자를 조회하여 응답에 포함

---

### B. 프론트엔드 - Enrollment.tsx (신규)

#### UI: 탭 + 테이블 파이프라인 뷰

```
[수업등록 관리]                                    [+ 신규 문의]

[문의(2)] [레벨테스트(1)] [수업중(5)] [종료(3)]

(문의 탭)
이름    학년   수업반   문의일     학부모 연락처      액션
───────────────────────────────────────────────────────────
김민수  중2   월수A    2/25     010-1234-5678    [→레벨테스트] [이력]
정하은  초등  미정     2/27     010-9876-5432    [→레벨테스트] [이력]

(레벨테스트 탭)
이름    학년   수업반   테스트 예정     결과     액션
───────────────────────────────────────────────────────────
박지영  고등   화목A   3/1 14:00    미완료    [일정/결과] [→수업시작] [이력]

(수업중 탭)
이름    학년   수업반   수업시작일   회차    수업료       액션
───────────────────────────────────────────────────────────
이수진  중1   화목A    1/15      5/8   320,000원   [→수업종료] [이력]

(종료 탭)
이름    학년   수업반   수업종료일    액션
───────────────────────────────────────────────────────────
최동현  중3   화목A    1/15       [→재등록] [이력]
```

#### 탭별 고유 컬럼

| 탭 | 고유 컬럼 |
|----|----------|
| 문의 | 문의일, 학부모 연락처 |
| 레벨테스트 | 테스트 예정일시, 결과 |
| 수업중 | 수업시작일, 회차(N/8), 수업료 |
| 종료 | 수업종료일 |

#### 기능
1. **탭 클릭** → 해당 상태 학생 목록 로드
2. **상태 변경 버튼** → 확인 다이얼로그 (메모 입력) → `POST /api/students/{id}/status`
3. **레벨테스트 일정/결과** → 다이얼로그에서 입력 → `PUT /api/students/{id}/level-test`
4. **이력 보기** → EnrollmentHistory 타임라인 다이얼로그
5. **active 전환 시** → 사이클 시작 제안 (기존 Students.tsx 로직 이동)
6. **신규 문의 등록** → 간소화 등록 폼 (이름, 학년, 연락처, 수업반, 메모)

---

### C. 프론트엔드 - Students.tsx 경량화

#### 제거
- 상태 변경 다이얼로그, 이력 다이얼로그, 사이클 시작 다이얼로그
- 상태 필터 드롭다운, 상태 배지 컬럼
- 상태변경/이력/삭제 버튼

#### 유지
- 학생 목록 테이블 (이름, 학교, 학년, 수업반, 연락처, 수업료)
- 수업반 필터
- 학생 등록/수정 다이얼로그 (기본정보 CRUD)
- 기본 조회: `enrollment_status=active` (수업중인 학생 정보 관리)

---

### D. 네비게이션 추가

**Sidebar.tsx** 메뉴 순서:
```
대시보드 → 수업반 관리 → 학생 관리 → 수업등록 → 출석 관리 → 수업료 관리 → 보충수업
```

**App.tsx**: `/enrollment` 라우트 추가

---

### E. 수정할 파일 목록

| 파일 | 작업 |
|------|------|
| `backend/app/models/student.py` | level_test 필드 3개 추가 |
| `backend/app/schemas/student.py` | 스키마 수정 + LevelTestUpdate 추가 |
| `backend/app/routers/students.py` | _to_response 수정 + level-test 엔드포인트 |
| `backend/tests/test_students.py` | 레벨테스트 필드 테스트 추가 |
| `frontend/src/pages/Enrollment.tsx` | **신규** |
| `frontend/src/pages/Students.tsx` | 상태 관련 기능 제거 |
| `frontend/src/components/Sidebar.tsx` | 수업등록 메뉴 추가 |
| `frontend/src/App.tsx` | Enrollment 라우트 추가 |

---

## Phase 5.3: 수업시작 연동 + 시드 데이터 (출석 스케줄 자동 생성)

**목표**: 수업등록 관리에서 "수업시작" 또는 "재등록" 시 수업시작일 입력 → 사이클 + 8회차 출석 스케줄 자동 생성. 시드 데이터도 동일하게 동작.

### 현재 문제점

1. **Enrollment.tsx**: 상태변경(→active) 후 별도 사이클 시작 다이얼로그가 뜨는 2단계 구조 → 수업시작일을 상태변경 다이얼로그에 통합해야 함
2. **재등록(stopped→active)**: 사이클 시작 연동 없음
3. **seed.py**: active 학생 5명이 있지만 Cycle/Attendance 레코드 미생성 → 출석 관리 페이지에 아무 데이터 없음

---

### A. 프론트엔드 - Enrollment.tsx 수정

#### 상태변경 다이얼로그 통합

**현재 흐름** (2단계):
```
[→수업시작] 클릭 → 상태변경 다이얼로그(메모) → 변경 → 사이클 시작 다이얼로그(시작일) → 시작
```

**변경 후** (1단계):
```
[→수업시작] 클릭 → 상태변경 다이얼로그(메모 + 수업시작일) → 변경 + 사이클 자동 시작
```

- `nextStatus === 'active'`일 때 다이얼로그에 **수업시작일 날짜 입력** 필드 추가
- 변경 버튼 클릭 시: 상태변경 API → 사이클 시작 API 순차 호출
- 별도 사이클 시작 다이얼로그 제거

#### 재등록(stopped→active) 처리
- 동일하게 수업시작일 입력 → 상태변경 + 사이클 시작 연동

---

### B. 백엔드 - 상태변경 시 사이클 자동 시작 (선택적)

**방법 1: 프론트에서 순차 호출** (현재 구조 유지)
- 프론트: `POST /status` → `POST /start-cycle` 순차 호출
- 백엔드 변경 없음

**방법 2: 백엔드에서 통합** (추천)
- `POST /api/students/{id}/status` 요청에 `start_date` 옵션 필드 추가
- `active`로 전환 + `start_date` 있으면 → 사이클 자동 시작

```python
class StatusChangeRequest(BaseModel):
    status: str
    memo: str | None = None
    start_date: str | None = None  # active 전환 시 수업시작일
```

- 장점: 원자적 처리 (상태변경 + 사이클 시작이 한 트랜잭션)
- 변경 파일: `schemas/student.py`, `routers/students.py`

---

### C. seed.py - active 학생에 사이클 + 출석 스케줄 생성

현재 seed.py는 active 학생만 등록하고 Cycle/Attendance를 생성하지 않음.

**변경 후**: active 상태 학생에 대해 `cycle_service.start_cycle()` 호출

```python
from app.services.cycle_service import start_cycle
from datetime import date, timedelta

# active 학생에 사이클 + 8회차 출석 스케줄 생성
# 시작일: 현재 주의 첫 수업 요일 (수업반 기준)
for student in db.query(Student).filter(Student.enrollment_status == "active").all():
    start_cycle(db, student.id, 시작일_계산())
```

시작일 계산 로직:
- 수업반의 `days_of_week` 기준
- 오늘 날짜에서 가장 가까운 과거/현재 수업 요일을 시작일로 설정
- 예: 오늘이 수요일이고 월수반이면 → 이번 주 월요일부터 시작

---

### D. 수정할 파일 목록

| 파일 | 작업 |
|------|------|
| `backend/app/schemas/student.py` | StatusChangeRequest에 start_date 추가 |
| `backend/app/routers/students.py` | active 전환 시 사이클 자동 시작 로직 |
| `backend/app/seed.py` | active 학생에 cycle + attendance 생성 |
| `backend/tests/test_enrollment.py` | 상태변경+사이클 통합 테스트 |
| `frontend/src/pages/Enrollment.tsx` | 상태변경 다이얼로그에 수업시작일 통합, 별도 사이클 다이얼로그 제거 |

---

### E. 검증

1. Enrollment에서 level_test → active 전환 시 수업시작일 입력 → 사이클+출석 생성 확인
2. stopped → active 재등록 시 동일 동작 확인
3. 출석 관리 페이지에서 해당 날짜에 스케줄 표시 확인
4. seed.py 실행 후 active 학생 5명의 출석 스케줄이 출석 관리에 표시되는지 확인
5. 기존 테스트 전체 통과

---

## Phase 6: 보충수업 관리

**목표**: 결석 시 보충수업 등록/완료 관리 (회차 복구 없음)

### DB 모델: `makeup_lessons`
- student_id, attendance_id(optional), scheduled_date/time, duration_minutes
- reason, is_completed, completed_at

### 프론트엔드
- `MakeupLessons.tsx` - 미완료 목록, 등록/완료 처리
- 출석 페이지에서 결석 시 보충수업 등록 안내 연동

---

## Phase 7: 대시보드 완성 + UI 개선

**목표**: 원장님이 앱 열면 한눈에 파악 가능한 대시보드

### 대시보드 구성
- 오늘의 수업 (요일 기반)
- 사이클 완료 알림 / 임박(7/8+) 목록
- 미납 현황
- 미완료 보충수업
- 전체 학생 현황

### UI 개선
- 반응형 레이아웃 (모바일 지원)
- 토스트 알림, 로딩 skeleton, 에러 처리 통일

---

## Phase 8: 학습 관리 + 현금영수증 (낮은 우선순위)

핵심 기능 안정화 후 진행. 상세 설계는 해당 시점에 확정.

---

## 주요 설계 결정

1. ~~**Soft Delete** (`is_active`)~~ → **enrollment_status** 상태 관리로 교체 (Phase 5.1)
2. **days_of_week JSON 문자열** - SQLite 배열 미지원 대응
3. **학년→수업료 코드 상수** - 단일 사용자 앱이므로 DB 분리 불필요
4. ~~**학생 등록 시 사이클 자동 생성**~~ → **active + 납부 확인 후 사이클 생성** (Phase 5.1)
5. **Payment 자동 생성** - 사이클 완료 시 다음 사이클 Payment 자동 생성
6. **enrollment_status 도입** - inquiry/level_test/active/stopped 4단계 + 이력 자동 기록 (Phase 5.1)
7. **스케줄 기반 출석** - 사이클 시작 시 8회차 출석 미리 생성, 기본 출석 상태 (Phase 5.1)
8. **선불 수업료** - 납부 확인(paid) 후 사이클 시작 가능 (Phase 5.1)
9. **수업등록 관리 페이지 분리** - Students는 정보 CRUD만, 상태 관리는 Enrollment 전담 (Phase 5.2)
10. **상태별 일자** - EnrollmentHistory.changed_at에서 계산 (별도 필드 불필요) (Phase 5.2)
11. **레벨테스트 일정/결과** - Student 모델에 level_test_date/time/result 필드 추가 (Phase 5.2)
12. **수업시작 시 사이클 자동 시작** - 상태변경 API에 start_date 통합, 원자적 처리 (Phase 5.3)
13. **시드 데이터 완전성** - active 학생은 Cycle + 8회차 Attendance 포함하여 시드 (Phase 5.3)

---

## 검증 방법

각 Phase 완료 시:
1. 백엔드: `uvicorn app.main:app --reload` 구동 확인
2. 프론트엔드: `npm run dev` 구동 확인
3. 해당 Phase의 CRUD가 UI에서 정상 동작하는지 수동 확인
4. API는 FastAPI 자동 문서 (`/docs`)에서 테스트 가능
