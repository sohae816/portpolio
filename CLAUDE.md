# 과일 필드노트 — Claude 작업 안내

과일·청과 MD 포트폴리오용 개인 프로젝트. 마트·편의점·온라인몰 현장 관찰을 기록하고(필드노트),
궁금한 점을 공공 데이터로 분석해 리포트로 공개한다. 사용자는 비개발자라 쉬운 한국어로 설명하고,
코드·용어는 꼭 필요할 때만 쓴다.

- 사이트: https://sohae816.github.io/portpolio/ (GitHub Pages, `main` 브랜치 루트에서 바로 배포)
- 저장소: `sohae816/portpolio` (**공개**) — 커밋되는 모든 것이 공개된다

## 구조

| 경로 | 내용 |
|---|---|
| `index.html` | 사이트 전체 (빌드 없음, 한 파일). 탭: 오늘의 필드 / 분석 리포트 / MD 기본 지식 / 먼슬리 리포트 |
| `reports/index.json` | 리포트 목록 + 각 리포트의 `card`(필드 카드에 연결할 때 보이는 요약) |
| `reports/<id>.json` | 리포트 상세 (질문·답·핵심 숫자·그래프 시리즈·발견·시사점·방법·한계) |
| `reports/<id>-notebook.html` | 전체 분석 노트 (노트북을 HTML로 내보낸 것) |
| `analysis/` | 분석 작업 폴더 (수집 스크립트, 노트북 빌더, 리포트 내보내기) |
| `analysis/.env` | 공공데이터포털 인증키 `DATA_GO_KR_KEY` — **git 제외, 절대 커밋·출력 금지** |
| `analysis/data/raw/` | API로 받은 원본 CSV — git 제외 (스크립트로 다시 받을 수 있음) |

## 필드노트 기록(카드)은 사용자 폰 브라우저에만 있다

카드 데이터는 브라우저 localStorage(`fm_days`, `fm_monthly`, `fm_glossary`)에만 저장되고 서버·저장소에 없다.
카드 내용이 필요하면 사용자에게 **먼슬리 리포트 탭 → 내보내기 텍스트**를 붙여넣어 달라고 한다.
백업 형식의 앱 식별자 `fruit-market-note`는 바꾸지 않는다 (예전 백업 복원이 깨짐).

## 분석 요청이 오면 (표준 흐름)

1. 질문을 가설 한 줄로 정리하고, 쓸 수 있는 공개 데이터를 고른다. 매장 매출은 공개되지 않으므로
   가격·물량·검색량 같은 대리 지표를 쓴다. 쿠팡 등 약관상 크롤링 금지 사이트는 쓰지 않고 공식 API를 쓴다.
2. 수집: `analysis/fetch_retail.py` 같은 스크립트로 `data/raw/`에 CSV 저장 (키는 `.env`에서 읽기만)
3. 분석 노트: `analysis/build_notebook.py` 패턴으로 노트북을 만들고 실행 → HTML 내보내기
4. 사이트용 요약: `analysis/export_report.py` 패턴으로 `reports/<id>.json`, `reports/index.json`(목록에 추가), 노트북 HTML 복사
5. 로컬 미리보기로 사용자에게 보여주고 → 사용자가 "배포"라고 하면 커밋·푸시
6. 사용자는 리포트 상세 하단 **🔗 내 필드 카드에 연결**로 하루 카드에 요약을 직접 붙인다

새 리포트를 만들 때 `reports/index.json`은 **기존 항목을 유지하고 추가**한다 (지금 export 스크립트는 단일 리포트용이라 덮어씀 — 두 번째 리포트부터는 병합하도록 고칠 것).

## 데이터 소스 메모

- 공공데이터포털 「한국농수산식품유통공사_기간별 소매가격 정보 조회」
  - `https://apis.data.go.kr/B552845/periodRetail/price`
  - 파라미터: `serviceKey, pageNo, numOfRows(최대 1000), returnType=JSON, cond[exmn_ymd::GTE], cond[exmn_ymd::LTE]` (날짜는 **YYYYMMDD**), 선택: `cond[item_cd::EQ]` 등
  - 코드: 과일류 400 · 사과 411(후지 05, 홍로 07, 홍옥 01, 아오리 06) · 배 412(신고 01, 원황 04) · 상품 04, 중품 05 — 전체 코드표 `analysis/data/retail_codes.xlsx`
  - 가격은 10개 단위. 조사처는 전통시장(이름 있음)과 익명 유통업체(`X-유통`)만 있고 대형마트·백화점 구분은 이 데이터에 없음
  - 개발계정 트래픽 하루 10,000건, 브라우저 CORS는 사이트 도메인에서 허용됨 (그래도 키를 사이트 코드에 넣지 말 것)
- 후보: 가락시장/전국 도매 경락가·반입량, 네이버 데이터랩·쇼핑 검색 API, 관세청 무역통계, KOSIS 소비자물가

## 보안 규칙 (회사 정책 포함)

- 인증키·토큰·비밀번호는 채팅에 붙여넣게 하지 않는다. 키 저장은 사용자가 **맥 기본 터미널 앱**에서 직접:
  `read -s "K?Paste API key, then Enter: " && printf 'DATA_GO_KR_KEY=%s\n' "$K" > ~/portpolio/analysis/.env && chmod 600 ~/portpolio/analysis/.env && unset K && echo && echo "Saved OK"`
  (Claude Code 대화창의 `!` 실행은 입력을 받지 못해 실패함)
- 키 값은 출력하지 않는다. 확인은 길이만. 배포 전 산출물에 키 문자열이 없는지 검사한다.
- 개인정보(이름·연락처 등)는 저장소·리포트에 넣지 않는다. 보안 문의는 Slack #support-정보보안.

## 작업 방식 (사용자 선호)

- 기능 변경은 먼저 로컬 미리보기(`.claude/launch.json` 없으면 `python3 -m http.server 8765`)로 보여주고, 사용자가 "배포"라고 하면 올린다.
- 배포 = 커밋 → `git push` → Pages 빌드 완료 확인(`gh api repos/sohae816/portpolio/pages/builds/latest`) → 실제 주소에서 반영 확인.
- 폰(아이폰 홈 화면 앱)에서 주로 쓴다. 폰 화면·다크모드에서도 확인한다.

## 다음에 할 일 후보

- 분석 리포트 2: 가락시장 도매가·반입량을 붙여 "원가 하락 vs 소매 행사" 구분
- 사이트 AI 질문 기능: GitHub Pages는 공개라 키를 못 숨김 → Cloudflare Worker 같은 작은 서버에 키를 두고
  Claude API(도구 사용)로 가격 API를 조회하는 구조. 1단계로 GitHub Actions가 매일 데이터를 모아 JSON으로 올리고 사이트에 조회 탭을 만드는 안도 있음.

## 새 노트북에서 이어서 하기

```bash
git clone https://github.com/sohae816/portpolio.git ~/portpolio
cd ~/portpolio/analysis && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
그다음 위 보안 규칙의 명령으로 `analysis/.env`에 인증키를 다시 저장하고, 원본 데이터는 `fetch_retail.py`로 다시 받는다.
