# PR #6 후속 실증과 평가기 경계 수정

작성: 2026-10-12. 기준: `a43342d4e20548702dba408ed71b5728d9ba8cea`.
후속 브랜치: `work/benchmark-followup-20261012`.

## 수행 범위

요청 착수 시 PR #6에 PR #4 검토사항과 PR #5의 지식관리 통합이 이미 구현되어 있었다.
그 변경을 중복 구현하거나 자신의 신규 작업으로 집계하지 않았다. PR #6의 소스·스크립트·
시험·벤치마크 JSON·Python 설정 25개 파일을 Git blob 해시로 대조하여 실행본을 구성했다.
네트워크 DNS 오류로 일반 git clone은 실패했으며, GitHub 연결 도구로 읽은 내용과 첨부
코드의 동일성을 해시로 확인했다. 위키/그래프 전체 checkout 및 전수 검증은 아니다.

기존 181개 시험을 재실행한 뒤, 새 반례를 실패시험으로 추가하고 작은 평가기 수정만 수행했다.
실제 ERA5 payload, 외부 모델 추론, 새로운 기상모델 학습, LAYA, GPU 작업은 수행하지 않았다.
기존 시험에는 제조문제의 미분/재시작 및 로컬 임시파일 실행이 포함된다.

## PR #6에서 이미 해결된 항목

- 등압면, 분위수 수준, 누적 시작/끝, 면적가중치가 비교 계약에 포함된다.
- 개별 사례의 MSE=0을 허용한다. 상대비의 기준 평균이 0이면 null과 이유를 반환한다.
- 큰 면적과 큰 MSE는 공통 스케일을 이용해 계산한다.
- 공개 레지스트리의 변수/단위/등압면/예측시간을 출처와 맞춘다.
- ROCSS 이진화/임계값/공간 집계를 기록하고 미해결 전처리 항목을 표시한다.
- 위키와 Graphify를 main 기반의 검토 브랜치에 통합한다. 실제 main 병합은 별도다.

이 문서는 이러한 선행 변경의 회귀확인과 아래 추가 수정의 근거다.

## 추가 발견과 수정

| 입력/계약 | PR #6 기준 동작 | 후속 동작 |
|---|---|---|
| 양쪽 모두 t2m 단위를 hPa로 선언 | IMPROVED | 거부 |
| 양쪽 모두 미등록 변수로 선언 | IMPROVED | 거부 |
| 양쪽 모두 aggregation=mean_rmse | IMPROVED | RMSE gate에서 거부 |
| 순간 기온을 누적 K, 강수를 순간 mm로 선언 | 계약 통과 | 거부 |
| 0+100j 예측을 실수 정답과 비교 | 허수부 경고 후 MSE=0 | 변환 전 거부 |
| 비영 오차 1e-200의 FP64 제곱 | MSE=0 | underflow 예외 |

서로 같은 정의인지와 각각 올바른 정의인지는 다르다. `LOCAL_VARIABLES`는 로컬 평가의
변수/단위/연직좌표/시간 통계를 명시한다. 공개 논문의 특정 등압면과는 분리하므로 로컬
평가를 원 논문의 500/700/850hPa로 한정하지 않는다. 지원되지 않는 변수는 등록 후 사용한다.
기온/기압/바람은 현재 instantaneous, 총강수 tp는 accumulation 계약이다. 시간평균
기온 등 새로운 제품은 관측연산과 계약을 추가하기 전에는 묵인하지 않는다.

비습 g kg-1와 kg kg-1, 기압 Pa와 hPa, 강수 mm와 m는 명시적으로 지원하되 후보와 기준의
단위 문자열은 같아야 한다. 평가기는 어떤 단위도 자동 변환하지 않는다. 로컬 처리기의
변환과 실제 물리 단위가 맞다는 사실은 해시/문자열만으로 증명되지 않는다.

`paired_rmse_check`는 다음 집계만 구현한다.

```text
RMSE = sqrt(mean(case_area_mse))
aggregation = mean_case_area_mse_then_sqrt
```

mean(case RMSE) 등 다른 집계명을 붙인 값을 같은 코드로 계산하지 않는다. 이 gate는
시간별 원자료를 받지 않으므로 호출자가 case MSE 자체를 사실대로 전달해야 한다.
블록 길이, 표본 독립성, 다중지표 선택은 별도의 과학적 프로토콜이다.

`_real_array`는 실수 부동소수점/정수 배열만 받는다. complex/object/bool/문자열을 자동으로
실수 관측으로 바꾸지 않는다. 복소 조화계수를 평가하려면 별도로 정의한 복소 노름이 필요하다.
그것을 위해 물리장 MSE 함수에서 허수부를 임의로 버리지는 않는다.

underflow 보호는 보수적이다. 최종 합이 표현 가능한 subnormal이어도 개별 비영 항이
제곱/가중 과정에서 0으로 바뀌면 거부한다. 이 경우 명시적 단위 재조정이나 별도 고정밀
평가기 사용을 요구한다. 실제 ERA5 오차가 이러한 크기였다는 의미는 아니다. 정확한 0,
고정 mask 밖 NaN, 유효한 큰 면적은 계속 허용한다.

## 실행 결과

| 실행 | 결과 |
|---|---|
| PR #6 소스의 기존 전체 pytest | 181 passed, 기존 경고 18개, subtest 2개 |
| 같은 원형에 새 28개 시험 적용 | 21 failed, 7 passed (의도한 Red 재현) |
| 수정 후 기존 66 + 새 28개 벤치마크 시험 | 94 passed |
| 수정 후 전체 pytest | 209 passed, 기존 경고 18개, subtest 2개 |
| check_benchmarks | RMSE 60 + ROCSS 3, 값/자료기간/용량 계산 유지 |

환경: Python 3.13.5 / NumPy 2.3.5 / SciPy 1.17.0 / torch 2.10.0+cpu / pytest 9.0.2.
검증은 현재 저장소의 `src/`, `scripts/`, `tests/`, 벤치마크 JSON과 Python 설정 전체에
대해 수행했다. Graphify 재생성, 전체 위키 schema/lint 및 원시 자료 품질검사는 수행하지 않았다.
과거 graphify-out/validation.json은 이전 스냅숏의 기록이며 이번 변경을 인증하지 않는다.

수정 전후 숫자는 [실행 근거](../evidence/benchmarks/followup.json)에 기록한다.
21개 실패는 기상모델 실패율이 아니라 새 오류주입 시험의 재현 개수다. 209개 통과 역시
실제 예측력의 인증점수가 아니다. 예보 본체·학습률·물리 시간간격·LAYA 설정을 바꾸지 않았다.

## 재현

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python -m pytest tests/test_benchmark_contract.py tests/test_benchmark_followup.py -q
python scripts/check_benchmarks.py --out runs/benchmark-followup.json
```

변경은 PR #6의 브랜치 위에 쌓은 후속 PR로 검토한다. PR #6 → 후속 PR 순서로 통합한다.
PR #6 병합 후에는 후속 PR의 base를 main으로 다시 확인하고 재시험해야 한다.
이번 작업에서 main/PR #6를 수정·병합하거나 지식그래프를 최신으로 표시하지 않았다.

다음은 로컬 R0 자료 수용검사다. P6h 누적구간·단위·실제 자료 시각, sp/정적장/지하 마스크와
학습/시험 사용이력을 먼저 확인한다. 사용자의 원자료는 로컬에 유지하며, 수용 근거 전에는
R1 지속예보/기후값 점수나 진짜 1시간 D83 성능을 생성한 것으로 표시하지 않는다.

수치 처리 문서: https://numpy.org/doc/stable/reference/generated/numpy.errstate.html
