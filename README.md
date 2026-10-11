# StreamingCAST

전지구 실제 1시간 예측과 미분가능 수치예보 연결을 위한 연구 저장소다.
코드·설계·시험·검토의 기준은 이 저장소이며, 실제 자료는 사용자의 로컬에서 별도 처리한다.

## 현재 구현: P0 streaming + differentiable adapter

- 발행시각에 고정한 두 입력의 스냅숏, 도착 지연/수정본/중복 처리, SQLite 실행 원장.
- D83 채널·단위 계약과 로컬 NPZ 검사. 원자료 다운로드나 서버 전송은 없다.
- 1시간 순수 텐서 물리 부분모델, 입력/계수 JVP·VJP·가중 수반·Taylor 시험.
- 일주기/반일주기의 정확한 선형 강제응답, 열/수분 항등식, 240시간 재시작.
- 이전 v0.1.1의 시간·강수 계약 두 파일을 원본 그대로 이관했다. 해시는 `evidence/source_provenance.json`에 있다.

**현재 실행모델은 4변수 독립 단층 제조문제다. D83 예보모델, 구면 신경망, 실제 대기조석 또는 운영 강수모델이 아니다.**
이전 D83의 240시간 합성예측이 지속예보보다 나빴던 실패를 해결했다고 표시하지 않는다.
실제 ERA5/관측 검증, LAYA 가중치 추론, B200 학습과 외부 NWP 통합은 아직 미실행이다.

## 시작

Python 3.11 이상. 실제 검증은 Python 3.13.5, torch 2.10.0+cpu, NumPy 2.3.5, SciPy 1.17.0에서 수행했다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q

# 새 로컬 폴더 생성 -> 자료 계약 검사 -> 240h toy 예측 -> 실행원장 중복검사
streamingcast demo --root local_data/demo

# 실제 계수학습 3개 seed + 독립 참조 + 미분/조석/재시작 실증
streamingcast prove --out runs/proof/proof.json
```

`demo`는 이미 존재하는 폴더를 덮어쓰지 않는다. `prove`는 지정 출력에 결과를 쓴다.
가중치/배열/SQLite/로컬 자료는 Git에서 제외한다. `evidence/`에는 작은 합성 지표만 기록한다.

## 실제 자료는 로컬에서

로컬 처리기가 원자료를 계약에 맞게 변환하고 `manifest.json`을 만든다. `demo`가 실행 가능한 예를 생성한다.

```bash
streamingcast inspect --manifest /absolute/local/manifest.json \
  --root /absolute/local/data --ledger runs/local.sqlite \
  --source YOUR_SOURCE --initialization 2026-01-02T00:00:00Z \
  --issue 2026-01-02T00:40:10Z
```

이 명령은 로컬 자료의 계약과 선택만 검사한다. **D83 자료를 4변수 toy에 넣어 예측하지 않는다.**
다운로드·ERA5 변환·재격자·정규화·실제 시각 가용성 검증은 로컬 처리기에서 담당한다.
상세 규격은 [LOCAL_DATA.md](docs/LOCAL_DATA.md)를 따른다.

## 로컬 ERA5 자료 준비

[ERA5 자료 현황과 입력 요건](docs/ERA5_READINESS.md)에 전지구 1979–2022년 Zarr
44개(5.48 TB), 지역 자료와 누락 현황을 기록했다. 전지구 캐시는 6시간·30채널이므로
1시간·D83 계약에 필요한 자료를 추가로 준비해야 한다.

```bash
python scripts/inspect_era5_cache.py --root "$HOME/MyThos/data/era5_raw" \
  --check-chunks --out runs/era5/cache-inventory.json
```

이 도구는 로컬 메타데이터와 청크 경로/크기만 점검한다. 원자료 다운로드, 변환,
실제 예측은 수행하지 않는다.

## 연결 구조

`로컬 처리기 -> Record/ledger -> 고정 Snapshot -> adapter -> 순수 텐서 step -> 결과검사 -> 실행원장`

외부 NWP는 [DESIGN.md](docs/DESIGN.md)의 `ForecastStep` 계약에 맞춰 교체한다.
미분경로 안에 파일 읽기, NumPy 변환, detach, 데이터 선택, LAYA 결정은 넣지 않는다.

## 검증 범위

[검증기록](docs/VERIFICATION.md), [프로젝트 상태](docs/PROJECT_STATUS.md),
[수학/공학 계약](docs/DESIGN.md), [실측 결과](evidence/proof.json)를 구분하여 읽는다.
현재 시험 통과는 실제 기상성능이나 전지구 장기 안정성을 인증하지 않는다.
작업 브랜치와 PR로 검토한다. 무거운 CI나 자동 병합은 추가하지 않았다.


## PR #2 검토 반영 및 P0.1 확장

[수정·확장 기록](docs/REVIEW_FIX.md)에 변경점과 실제 시험 범위를 명시한다.
107개 회귀시험, `-O` 실패 차단, 불변 snapshot, 발행별 파일 검사, 내용해시 산출물 경로를 추가했다.
`inspect`는 메타데이터를 등록한 뒤 선택된 파일만 읽고, `check-catalog`는 모든 파일을 검사한다.
현재 demo의 `forecast.npz`는 편의용 복사본이며 원장에는 `artifacts/sha256/...` 경로를 등록한다.
새 SI/native/관측 연결부와 내부 dt 세분은 4변수 제조계만 대상으로 한다.

```bash
python scripts/prove_expansion.py --out runs/expansion.json
```

기존 `evidence/proof.json`, `evidence/source_files.json`은 초기 P0의 역사적 기록이다.
현재 실행·소스 해시는 `evidence/review_fix/`를 확인한다. 실제 기상성능과 B200 승인은 보류한다.
