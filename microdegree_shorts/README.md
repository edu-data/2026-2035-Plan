# 마이크로디그리 웹드라마 쇼츠 — 「데이터는 설레고, 너는 촉촉해」

| 회차 | 강의 | 파일 |
|---|---|---|
| #4 | R 프로그래밍 1 (Posit Cloud를 활용한 데이터 분석 1) | `microdegree_ep04_shorts.mp4` |
| 홍보편 | 마이크로디그리(데이터 과학) 데이터 분석 기초 46강 재생목록 홍보 | `microdegree_promo_shorts.mp4` |
| #5 | 데이터 분석 기초(R 프로그래밍 1)_Posit Cloud를 활용한 데이터 분석 2 | `microdegree_ep05_shorts.mp4` |

## 새 회차 만들기
1. `episodes/ep05.json`을 복사해 `epNN.json`을 만들고 대사·카드 문구를 수정
   - `lines`: 화면 자막(2~3줄) / `tts`: 음성용 문장(발음 보정, 예: Posit → 포짓)
   - 카드 제목에서 코드는 `` `백틱` ``으로 감싸면 코드 폰트로 표시됨
   - `pad_weight`: 남는 시간을 장면에 나눠 주는 비율(인포그래픽은 크게)
2. 실행: `python3 microdegree_shorts/tools/make_short.py microdegree_shorts/episodes/epNN.json [출력.mp4]`
   - 미리보기 프레임만: `PREVIEW=2,20 python3 ...`
3. 요구 사항: ffmpeg, Pillow, numpy, `pip install edge-tts`, `speech.platform.bing.com` 접속 허용

## 구성
- 장면: 누나(고민) → 뭉이(리액션) → 쫑이(해결) → 인포그래픽 3카드 → 3인 분할 엔딩, 총 30초
- `assets/plates/`: 3강 영상에서 추출한 캐릭터 원본 이미지(누나·쫑이·뭉이), `ending_group.png`(엔딩 3인 단체 이미지)
- `assets/cutouts/`: 캐릭터 배경 제거본 — `tools/cutout.mjs`(@imgly/background-removal-node)로 생성
- 엔딩 이미지 재합성: `python3 microdegree_shorts/tools/make_group_ending.py` (배치·크기는 스크립트 안에서 조정)
- `assets/fonts/`: Pretendard, D2Coding (SIL Open Font License)
- 음성: Microsoft Edge TTS(누나·뭉이 SunHi, 쫑이 InJoon) / BGM: 스크립트가 직접 합성
