# GitHub Pages 배포 안내서

이 문서는 별도 도메인 없이 `https://사용자명.github.io/저장소명/`으로 QuestBoard를 공개하는 절차입니다.

## 1. 공개 저장소 만들기

GitHub에서 비어 있는 공개 저장소를 만든 뒤 로컬 프로젝트에서 다음을 실행합니다. `YOUR_NAME`과 `YOUR_REPOSITORY`를 실제 값으로 바꾸세요.

```powershell
git add .
git commit -m "feat: initialize QuestBoard"
git remote add origin https://github.com/YOUR_NAME/YOUR_REPOSITORY.git
git push -u origin main
```

공개 저장소에는 `.env`, API 키, 로그인 쿠키, 원문 본문이나 개인정보를 올리지 마세요. `.gitignore`가 `.env`를 제외하는지 커밋 전에 `git status`로 확인합니다.

## 2. Actions 권한 설정

저장소의 **Settings → Actions → General → Workflow permissions**에서 `Read and write permissions`를 선택하고 저장합니다. 이는 수집 워크플로가 `public/data` 변경을 커밋하는 데 필요합니다.

조직 정책으로 쓰기 권한을 허용할 수 없다면 자동 커밋 단계는 실패합니다. 그 경우 관리자의 허용이 필요하며, 토큰 우회나 개인 토큰 하드코딩은 하지 않습니다.

## 3. 기업마당 설정

기업마당은 공개 지원사업·행사 목록을 HTML로 읽으므로 API 키나 GitHub Secret을 등록할 필요가 없습니다.

## 4. Pages 활성화

1. **Settings → Pages**로 이동합니다.
2. **Build and deployment → Source**를 `GitHub Actions`로 선택합니다.
3. **Actions** 탭에서 `Deploy site`를 수동 실행합니다.
4. 작업의 `Deploy GitHub Pages` 단계가 끝나면 표시된 URL을 엽니다.

Vite의 상대 경로 빌드를 사용하므로 저장소명이 무엇이든 기본 Pages 하위 경로에서 동작합니다.

## 5. 자동 수집 일정

`Collect data and deploy` 워크플로는 GitHub cron의 UTC 기준으로 실행됩니다.

- 빠른 출처: 매시간 17분
- 느린 출처: 6시간마다 43분
- 전체 정합성 재생성: 매일 한국시간 약 03:11

GitHub의 부하에 따라 예약 실행이 지연될 수 있습니다. **Run workflow**에서 그룹, 특정 출처 ID, 최대 수집 건수를 정해 수동 실행할 수도 있습니다.

## 6. 첫 배포 확인표

- `CI`의 Python, 데이터 검증, lint, 단위 테스트, 빌드, 브라우저 테스트가 모두 통과했는가
- Pages 첫 화면에서 `data/*.json`이 404 없이 로드되는가
- `수집 상태`에서 키가 필요한 출처와 실패 사유가 예상대로 보이는가
- 원문 링크가 새 탭에서 열리고 도메인이 맞는가
- 모바일·다크 테마와 새로고침 후 URL 필터 복원이 동작하는가
- 저장소 검색에서 실제 API 키 문자열이 발견되지 않는가

## 배포 장애 복구

1. Actions 실패 작업의 첫 실패 단계를 확인합니다.
2. 데이터 검증 실패면 해당 `public/data` 자동 커밋을 되돌리기보다, 원인 수집기/수동 YAML을 고쳐 전체 수집을 다시 실행합니다.
3. Pages 아티팩트 실패면 로컬에서 `pnpm install --frozen-lockfile && pnpm build`를 재현합니다.
4. 자동 커밋 push 거부면 Workflow permissions와 브랜치 보호 규칙을 확인합니다.
5. 수집처 하나의 실패는 사이트 전체 장애가 아닙니다. 마지막 정상 데이터가 유지되는지 확인하고 [운영 안내서](OPERATIONS.md)에 따라 조치합니다.
