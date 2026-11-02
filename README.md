# QuestBoard

공모전·지원사업·해커톤 등 포트폴리오를 쌓을 기회를 찾는 사람을 위한 공고 모음 웹사이트입니다. 여러 사이트의 공개 공고를 모아 분야와 참가 조건으로 검색하고, 관심 공고와 일정을 관리할 수 있습니다.

IT·게임을 기본 분야로 제공하며 디자인·영상, 문학·예술, 기획·아이디어, 창업·비즈니스도 별도 탭으로 탐색할 수 있습니다. Python이 수집·가공한 JSON을 React 웹사이트에서 읽는 구조이며, 로그인 기반 개인 기능에는 Firebase를 사용합니다.

## 제작 배경

관심 있는 공모전이 여러 사이트에 흩어져 있어 한눈에 살펴보기 어려웠습니다. 공모전·지원사업·해커톤에 참여하며 포트폴리오를 쌓고 싶은 사람들이 여러 사이트를 오가며 찾는 수고를 줄일 수 있도록 만들었습니다.

## 핵심 기능

- **공고 탐색**: 5개 분야 탭과 공모전·지원사업·해커톤 등 유형별 분류, 대학생·인디·AI·마감임박 등 빠른 필터를 제공합니다.
- **검색·상세 조건**: 초성·동의어·오타 허용 검색과 참가 대상·지역·온오프라인·참가비·상금 필터를 지원합니다. 상세 정보가 없는 공고는 제외 건수를 안내하고 함께 표시할 수 있습니다. 마감순·신규순·수정순·관련도순·상금순 정렬과 조회 조건의 URL 공유도 지원합니다.
- **일정 확인**: 이번 주·다음 주 마감과 최근 7일 새 공고를 주간 요약으로 보여주고, 날짜 미상 공고와 최근 3개월 마감 공고를 분리합니다.
- **개인 공고 관리**: Google 로그인 후 찜·메모·발표일·관심 키워드·알림함을 같은 계정의 다른 기기에서 동기화합니다. 사이트 접속 시 일정 알림과 키워드에 맞는 공고를 확인하고, 찜한 일정은 ICS 파일로 내보낼 수 있습니다. 확인·숨김 상태는 브라우저에 저장합니다.
- **수집·운영 상태**: 출처별 수집 결과와 검토 큐, 출처 유형에 따른 신뢰도 배지를 제공합니다. 현재 설정에서 11개 출처가 활성화되어 있으며, 한 출처가 실패해도 나머지 수집을 계속합니다. 온오프믹스·한국콘텐츠진흥원은 robots.txt 정책을 이유로 비활성화되어 있습니다.
- **화면·구독**: 밝게·어둡게·시스템 테마, 모바일 카드 레이아웃, 전체·분야별 RSS 피드를 제공합니다.

## 사용 기술

| 기술 | 사용 용도 |
| --- | --- |
| React 19 · TypeScript | 공고 목록·상세·주간 요약·개인 관리 화면과 데이터 타입 정의 |
| React Router 7 | 정적 호스팅에서 동작하는 해시 기반 페이지 라우팅 |
| Vite 7 · pnpm | 개발 서버, 프런트엔드 빌드와 패키지 관리 |
| Python · 표준 라이브러리 | HTTP 수집, HTML·Markdown 파싱, 날짜·URL 정규화, 중복 병합, 변경 이력 및 JSON·RSS 생성 |
| PyYAML | 출처·분류 규칙과 수동 추가·수정·제외 설정 로딩 |
| Firebase Authentication · Cloud Firestore | Google 로그인과 사용자별 찜·키워드·알림 데이터 저장·동기화 |
| GitHub Actions · GitHub Pages | 정기 수집, 데이터 검증·커밋, 사이트 빌드와 정적 배포 |
| pytest · Vitest · Testing Library · Playwright | 수집 파이프라인, 프런트엔드 로직·컴포넌트, 브라우저 동작 테스트 |

## 핵심 동작 구조

```text
공개 공고(HTML·Markdown)
  → 출처별 수집기
  → 날짜·URL·참가 조건 정규화와 키워드 규칙 기반 분류
  → 수동 공고 추가 → 중복 병합 → 수동 수정·제외 반영 → 신규·변경 이력 비교
  → public/data/의 JSON·RSS 생성
  → React에서 검색·필터·정렬·일정 표시

Google 로그인 → Firestore의 사용자별 개인 데이터 저장·구독
```

공고 데이터는 브라우저가 각 출처에 직접 요청하지 않고 생성된 정적 JSON에서 읽습니다. 일부 출처 수집에 실패하면 이전 데이터를 유지하며, 화면에서는 현재 날짜에 맞춰 접수 상태와 D-day를 다시 계산합니다. 알림은 사이트 접속 시 생성·확인하는 방식입니다.

## 저장소 구조

```text
config/                 출처와 분류 키워드
manual/                 수동 추가·수정·제외 YAML
pipeline/               Python 수집·정규화·중복·변경 감지
public/data/            사이트가 읽는 생성 JSON
schemas/                공개 데이터 JSON 스키마
src/                    React + TypeScript 사이트
tests/, e2e/            Python·프론트·브라우저 테스트
.github/workflows/      CI, 매일 수집, Pages 배포
docs/                   배포·운영·수집 정책
firestore.rules         UID별 개인 데이터 접근 규칙
```

## 로컬 실행

Node.js 24.x와 pnpm 11을 사용합니다. Python은 3.12 이상을 지원하며, CI와 자동 수집은 3.14를 사용합니다.

```powershell
corepack enable
corepack prepare pnpm@11 --activate
pnpm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pnpm dev
```

공고 조회만 할 때는 API 키가 필요하지 않습니다. 저장소의 `public/data/`를 사용하며, 개발 서버가 표시한 주소(기본 `http://localhost:5173`)를 엽니다.

로그인과 개인 기능을 사용하려면 `.env.example`을 `.env.local`로 복사해 Firebase 웹 앱 설정을 채우고, Google 로그인·승인 도메인·Firestore 접근 규칙을 설정해야 합니다. 절차는 [배포 안내서](docs/DEPLOYMENT.md)를 참고하세요. 환경 파일이나 서비스 계정 키·관리자 자격 증명을 커밋하지 마세요.

### 데이터 수집

```powershell
# 자동화 가능한 모든 출처(출처별 최대 건수는 sources.yml의 limit, 없으면 150건)
python -m pipeline.cli --schedule all

# 출처 일부 그룹만(sources.yml의 schedule 값 기준)
python -m pipeline.cli --schedule fast
python -m pipeline.cli --schedule slow

# 특정 출처만 진단: 공개 데이터(public/data)를 덮어쓰지 않도록 임시 폴더에 씁니다
python -m pipeline.cli --schedule all --source dev_event --limit 10 --output "$env:TEMP\questboard-check"

# 생성 데이터 계약 검사
python -m pipeline.validate
```

기업마당은 API 키 없이 공개 HTML 검색을 사용합니다. 별도의 키 발급이나 GitHub Secret 등록은 필요하지 않습니다.

### 테스트와 빌드

```powershell
python -m pytest
python -m pipeline.validate
python -m ruff check pipeline tests
pnpm lint
pnpm test
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e
```

## 분류·표시 원칙

- IT·게임 관련성 70점 이상은 IT·게임 탭에 공개합니다. 70점 미만이어도 제목이나 원본 분류가 다른 분야 주제어(영상, 문학, 아이디어, 창업 등)에 맞으면 해당 분야 탭에 공개합니다.
- 원본 분류에 IT와 사진·영상 등 여러 분야가 섞여 있으면 제목의 명확한 분야를 우선합니다. 제목에 AI·게임·ERP·XR 등 기술 근거가 있거나 게임 형태 출품이 명시된 공고는 IT·게임에 유지합니다. 다른 분야를 정할 때도 제목 주제어를 먼저 사용하고, 제목에 근거가 없을 때 원본 분류를 사용합니다.
- 어느 분야에도 맞지 않으면 50~69점은 검토 큐, 49점 이하는 제외합니다. 입찰·용역·경품 이벤트 같은 제외 문구는 어느 탭에도 공개하지 않습니다.
- 채용·인턴·상업성 유료 교육은 `확장 기회`로 수집하되 기본 전체 목록에서 숨깁니다.
- 최초 발견 후 72시간은 `NEW`, 중요 정보 변경 후 48시간은 `UPDATED`입니다.
- D-7 이하는 마감임박, D-3 이하는 긴급, 당일은 오늘마감입니다.
- 정확한 마감일이 없으면 날짜 미상 화면으로 이동합니다.
- 원문 본문·포스터·첨부파일은 재배포하지 않고 링크, 추출 요약, 분류 결과와 해시성 식별자만 저장합니다.

키워드 점수와 분야 탭 주제어는 [config/taxonomy.yml](config/taxonomy.yml)(`fields`, `weak_title_keywords`, `domains`), 출처는 [config/sources.yml](config/sources.yml)에서 관리합니다. 상세 수집 정책은 [docs/COLLECTORS.md](docs/COLLECTORS.md)를 참고하세요.

## 수동 관리

모든 YAML 변경은 자동 결과보다 우선합니다.

- `manual/opportunities.yml`: 자동 수집되지 않은 공고 추가
- `manual/overrides.yml`: ID 또는 원문 URL 기준 필드 수정·강제 공개·검토
- `manual/exclusions.yml`: ID 또는 원문 URL 강제 제외

예시는 [운영 안내서](docs/OPERATIONS.md)에 있습니다. 수정 후 `python -m pipeline.cli --schedule all`로 다시 생성하고 `python -m pipeline.validate`로 확인합니다.

## GitHub Pages 배포

Pages·Actions 권한과 Firebase 웹 앱 설정을 전달할 저장소 Variables는 [배포 안내서](docs/DEPLOYMENT.md)를 참고하세요.

- `pages.yml`: `main`에 코드가 푸시되거나 수동 실행하면 사이트를 빌드·배포합니다. `public/data/`만 바뀐 푸시는 제외합니다.
- `collect.yml`: 매일 한국시간 03:11(UTC 18:11)에 전체 활성 출처의 수집·검증·데이터 커밋·빌드·배포를 실행하도록 설정되어 있습니다. 예약 실행은 지연될 수 있습니다. 데이터 커밋이 다른 워크플로를 발생시키지 않아도 같은 워크플로에서 배포합니다.

바로 갱신하려면 [수동 갱신 절차](docs/DEPLOYMENT.md#수동-갱신)를 따르세요. 소량 진단은 위의 `--output` 예시처럼 별도 폴더에서 실행해야 공개 데이터가 일부 수집 결과로 바뀌는 일을 피할 수 있습니다.

## 운영상 주의

공고는 자동 추출·분류한 정보이므로 신청 전 주최기관 원문에서 참가 조건과 일정을 확인하세요. 실시간 갱신이 아니며, 원문에 없는 날짜·조건은 비어 있을 수 있습니다.

차단, 로그인, CAPTCHA를 우회하지 않습니다. robots.txt·이용약관·페이지 구조가 바뀌어 허용 여부나 안정성을 확신할 수 없으면 해당 수집처를 비활성화하고 수동 YAML 또는 승인된 대체 출처를 사용하세요. 공개 전 운영자는 출처별 정책을 다시 확인할 책임이 있습니다.

장애, stale 판정, 수집처 교체와 데이터 복구 절차는 [docs/OPERATIONS.md](docs/OPERATIONS.md)에 정리되어 있습니다.
