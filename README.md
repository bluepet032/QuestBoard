# QuestBoard

IT·게임 분야의 공모전, 지원사업, 해커톤, 행사, 교육 및 채용 정보를 한 화면에서 찾는 정적 웹사이트입니다. Python 수집 파이프라인이 공개 정보만 읽어 공통 JSON으로 정규화하고, React 사이트가 검색·필터·정렬·개인 상태를 제공합니다.

## 제공 기능

- 공모전·지원사업·해커톤·행사 등 유형별 탭과 현재 조건 기준 건수
- 대학생·인디·AI·NEW·UPDATED·마감임박 빠른 태그
- 검색, 분야·상태 필터, 4가지 정렬, URL로 공유 가능한 조회 상태
- 날짜 미상 및 최근 1년 마감 공고 분리
- 관심·확인·숨김 상태의 브라우저 저장(로그인 없음)
- 출처별 수집 상태와 50~69점 수동 검토 큐
- 밝게/어둡게/시스템 테마와 모바일 카드 레이아웃
- 한 출처가 실패해도 계속 실행되는 13개 수집처 파이프라인

## 저장소 구조

```text
config/                 출처와 분류 키워드
manual/                 수동 추가·수정·제외 YAML
pipeline/               Python 수집·정규화·중복·변경 감지
public/data/            사이트가 읽는 생성 JSON
schemas/                공개 데이터 JSON 스키마
src/                    React + TypeScript 사이트
tests/, e2e/            Python·프론트·브라우저 테스트
.github/workflows/      CI, 차등 수집, Pages 배포
docs/                   배포·운영·수집 정책
```

## 로컬 실행

권장 환경은 Node.js 24 LTS, pnpm 11, Python 3.14입니다. Python 코드는 로컬 편의를 위해 3.12 이상에서도 실행됩니다.

```powershell
corepack enable
corepack prepare pnpm@11 --activate
pnpm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
pnpm dev
```

기업마당은 공개 지원사업·행사 목록을 직접 읽으므로 API 키가 필요하지 않습니다.

사이트만 확인할 때는 API 키가 필요하지 않습니다. 개발 서버가 표시한 `http://localhost:5173` 주소를 엽니다.

### 데이터 수집

```powershell
# 자동화 가능한 모든 출처, 출처별 최대 100건
python -m pipeline.cli --schedule all --limit 100

# 1시간 그룹 또는 6시간 그룹
python -m pipeline.cli --schedule fast
python -m pipeline.cli --schedule slow

# 특정 출처만 진단
python -m pipeline.cli --schedule all --source dev_event --limit 10

# 생성 데이터 계약 검사
python -m pipeline.validate
```

기업마당은 API 키 없이 공개 HTML 검색을 사용합니다. 별도의 키 발급이나 GitHub Secret 등록은 필요하지 않습니다.

### 테스트와 빌드

```powershell
python -m pytest
python -m pipeline.validate
pnpm lint
pnpm test
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e
```

## 분류·표시 원칙

- 관련성 70점 이상은 공개, 50~69점은 검토 큐, 49점 이하는 제외합니다.
- 채용·인턴·상업성 유료 교육은 `확장 기회`로 수집하되 기본 전체 목록에서 숨깁니다.
- 최초 발견 후 72시간은 `NEW`, 중요 정보 변경 후 48시간은 `UPDATED`입니다.
- D-7 이하는 마감임박, D-3 이하는 긴급, 당일은 오늘마감입니다.
- 정확한 마감일이 없으면 날짜 미상 화면으로 이동합니다.
- 원문 본문·포스터·첨부파일은 재배포하지 않고 링크, 추출 요약, 분류 결과와 해시성 식별자만 저장합니다.

키워드 점수는 [config/taxonomy.yml](config/taxonomy.yml), 출처는 [config/sources.yml](config/sources.yml)에서 관리합니다. 상세 수집 정책은 [docs/COLLECTORS.md](docs/COLLECTORS.md)를 참고하세요.

## 수동 관리

모든 YAML 변경은 자동 결과보다 우선합니다.

- `manual/opportunities.yml`: 자동 수집되지 않은 공고 추가
- `manual/overrides.yml`: ID 또는 원문 URL 기준 필드 수정·강제 공개·검토
- `manual/exclusions.yml`: ID 또는 원문 URL 강제 제외

예시는 [운영 안내서](docs/OPERATIONS.md)에 있습니다. 수정 후 `python -m pipeline.cli --schedule all --limit 1`로 다시 생성하고 `python -m pipeline.validate`로 확인합니다.

## GitHub Pages 배포

원격 저장소 생성, Secret, Actions 권한과 Pages 설정은 [배포 안내서](docs/DEPLOYMENT.md)를 순서대로 따르세요. 사이트 코드 변경은 `pages.yml`, 데이터 갱신은 `collect.yml`이 빌드와 Pages 배포를 담당합니다. 자동 데이터 커밋이 다른 워크플로를 다시 발생시키지 않아도 같은 수집 워크플로에서 최신 사이트를 배포합니다.

## 운영상 주의

차단, 로그인, CAPTCHA를 우회하지 않습니다. robots.txt·이용약관·페이지 구조가 바뀌어 허용 여부나 안정성을 확신할 수 없으면 해당 수집처를 비활성화하고 수동 YAML 또는 승인된 대체 출처를 사용하세요. 공개 전 운영자는 출처별 정책을 다시 확인할 책임이 있습니다.

장애, stale 판정, 수집처 교체와 데이터 복구 절차는 [docs/OPERATIONS.md](docs/OPERATIONS.md)에 정리되어 있습니다.
