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

---

## 검증 방법

각 Phase 완료 시:
1. 백엔드: `uvicorn app.main:app --reload` 구동 확인
2. 프론트엔드: `npm run dev` 구동 확인
3. 해당 Phase의 CRUD가 UI에서 정상 동작하는지 수동 확인
4. API는 FastAPI 자동 문서 (`/docs`)에서 테스트 가능
