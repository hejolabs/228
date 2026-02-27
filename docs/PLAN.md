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

1. **Soft Delete** (`is_active`) - FK 참조 무결성 보호
2. **days_of_week JSON 문자열** - SQLite 배열 미지원 대응
3. **학년→수업료 코드 상수** - 단일 사용자 앱이므로 DB 분리 불필요
4. **학생 등록 시 사이클 자동 생성** - 트랜잭션으로 묶어 처리
5. **Payment 자동 생성** - 사이클 완료 시 자동

---

## 검증 방법

각 Phase 완료 시:
1. 백엔드: `uvicorn app.main:app --reload` 구동 확인
2. 프론트엔드: `npm run dev` 구동 확인
3. 해당 Phase의 CRUD가 UI에서 정상 동작하는지 수동 확인
4. API는 FastAPI 자동 문서 (`/docs`)에서 테스트 가능
