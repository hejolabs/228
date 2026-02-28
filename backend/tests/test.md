⏺ 테스트 실행 방법
 
  # 프로젝트 루트에서
  cd backend && .venv/bin/pytest tests/ -v

  # 특정 파일만
  .venv/bin/pytest tests/test_cycle.py -v

  # 특정 테스트 클래스만
  .venv/bin/pytest tests/test_cycle.py::TestNewCycle -v

  # 특정 테스트 하나만
  .venv/bin/pytest tests/test_cycle.py::TestNewCycle::test_new_cycle_after_completion -v

  -v는 verbose 옵션으로, 각 테스트 이름과 PASSED/FAILED를 개별 표시합니다. 없으면 .과 F로만
  나옵니다.

  ---
  테스트 초기화 → 실행 흐름

  JPA 테스트와 비교하면서 설명합니다.

  1단계: conftest.py 로드 (테스트 시작 전 1회)

  os.environ["TESTING"] = "1"  # lifespan에서 시드 데이터 건너뛰기

  Spring으로 치면 @ActiveProfiles("test")로 테스트 프로파일을 활성화하는 것과 같습니다.

  engine = create_engine(
      "sqlite:///:memory:",                    # 메모리 DB (H2 in-memory와 동일)
      connect_args={"check_same_thread": False},
      poolclass=StaticPool,                     # 모든 스레드가 같은 연결 공유
  )

  JPA에서 spring.datasource.url=jdbc:h2:mem:testdb로 메모리 DB를 쓰는 것과 같습니다.

  2단계: 각 테스트 실행 시 fixture 호출

  pytest의 fixture는 JPA의 @BeforeEach / @AfterEach와 비슷합니다.

  테스트 함수 호출
    → seed_student fixture 필요
      → client fixture 필요
        → db fixture 필요

  이렇게 의존성 체인을 따라 아래→위 순서로 실행됩니다.

  db fixture (= @BeforeEach + @AfterEach)

  @pytest.fixture()
  def db():
      Base.metadata.create_all(bind=engine)  # DDL 실행 (테이블 생성)
      session = TestSession()
      try:
          yield session                       # ← 테스트 실행
      finally:
          session.close()
          Base.metadata.drop_all(bind=engine) # 테이블 전체 삭제 (깨끗한 상태 복원)

  JPA로 비유:
  @BeforeEach
  void setup() {
      // CREATE TABLE ... (DDL)
      em = emf.createEntityManager();
  }

  @AfterEach
  void teardown() {
      em.close();
      // DROP TABLE ... (완전 초기화)
  }

  client fixture (= TestRestTemplate)

  @pytest.fixture()
  def client(db):                              # db fixture에 의존
      app.dependency_overrides[get_db] = ...   # 실제 DB 대신 테스트 DB 주입
      with TestClient(app) as c:
          yield c                              # 실제 HTTP 요청 없이 API 호출 가능

  Spring의 @MockBean이나 @TestConfiguration으로 DataSource를 교체하는 것과 동일합니다.

  seed_student fixture (= 테스트 데이터 준비)

  @pytest.fixture()
  def seed_student(client, seed_class_group):  # client, seed_class_group에 의존
      res = client.post("/api/students", json={...})
      return res.json()

  3단계: 실제 테스트 실행 예시

  test_first_attendance_increments_to_1 하나의 전체 흐름:

  1. db fixture
     → CREATE TABLE class_groups, students, cycles, attendance (메모리 DB)
     → Session 생성

  2. client fixture
     → get_db를 테스트 DB session으로 교체
     → TestClient 생성

  3. seed_class_group fixture
     → POST /api/class-groups → 수업반 1개 생성

  4. seed_student fixture
     → POST /api/students → 학생 1명 + 사이클 자동 생성

  5. 테스트 본문 실행
     → POST /api/attendance → 출석 1회
     → assert current_count == 1  ✅

  6. 정리 (역순)
     → TestClient 종료
     → Session 닫기
     → DROP TABLE 전체 (메모리 DB 초기화)

  다음 테스트가 시작되면 1번부터 다시 빈 DB로 시작합니다. 그래서 테스트 간에 데이터가 섞이지 않습니다.

  ---
  요약: JPA 테스트에서 H2 메모리 DB + @Transactional rollback으로 격리하는 것과 거의 같은 패턴입니다. 차이점은 SQLAlchemy는 @Transactional rollback 대신 매번 DROP/CREATE하는 방식이라는
   정도입니다.