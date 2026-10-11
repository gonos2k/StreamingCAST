# 외부 벤치마크 확보와 StreamingCAST 개발 지표

작성 2026-10-11. 적용할 자료계획은 [ERA5_ALIGNED_PLAN.md](ERA5_ALIGNED_PLAN.md)다.
목표는 유명 모델의 논문 우위 비율을 나열하는 것이 아니라 **수치·조건·출처를 저장하고 같은 조건의 개선을 검사**하는 것이다.

## 1. 확보 상태를 세 단계로 분리한다

1. **외부 논문 수치 — 확보:** primary paper의 표/본문에서 60개 RMSE와 3개 ROCSS를 전사했다.
   원 논문의 반올림 자릿수를 유지한다. 그림 OCR/곡선 digitization으로 숫자를 만들지 않았다.
2. **공개 결과파일 — 위치 확보:** 공식 WeatherBench guide의 `gs://weatherbench2/benchmark_results`,
   INRIA/geoarches의 GenCast 0.25°/1° NetCDF 경로와 blob ID를 확인했다.
   이번 GCS 접근/런타임 네트워크는 실패했다. GenCast 파일의 base64 응답도 완전한 로컬 decode·해시검증·점수 추출을 완료하지 못했다.
   따라서 그 파일들의 값을 얻었다거나 최신 WeatherBench 전체 점수표를 가져왔다고 보고하지 않는다.
3. **StreamingCAST와 공통 재예측 — NOT_RUN:** 사용자 로컬에서 실제 예측장·가중치·샘플을 준비한 뒤 수행한다.

[reference_scores.json](../benchmarks/reference_scores.json)에 출처·위치·연도·단위·한계·null을 함께 저장한다.
정규화 RMSE, 논문의 '90% 항목 우위', CRPS, ROCSS를 같은 성능률로 섞지 않는다.

## 2. 확보한 24시간 수치의 대표값

출처: Couairon et al., *ArchesWeatherGen*, Science Advances (2026), Table 1.
DOI: `10.1126/sciadv.adx2372`.
https://pmc.ncbi.nlm.nih.gov/articles/PMC13101865/

논문 기준: 2020, 00/12 UTC 초기화, 전지구, 1.5° 평가, 24h lead.
고해상도 모델의 native resolution이 평가격자라는 뜻은 아니다.
모델별 원래 checkpoint·sample hash·mask/aggregation lineage를 여기서 재확인한 것은 아니다.
Stormer의 다중 pass와 NeuralGCM 등의 버전은 로컬 비교 전에 고정한다.

| 모델 | Phi500 RMSE (m²/s²) | T850 (K) | q700 (g/kg) | T2m (K) | u10 (m/s) | v10 (m/s) |
|---|---:|---:|---:|---:|---:|---:|
| IFS HRES | 42.30 | 0.625 | 0.556 | 0.513 | 0.833 | 0.872 |
| Pangu-Weather | 44.31 | 0.620 | 0.538 | 0.570 | 0.728 | 0.759 |
| GraphCast | 39.78 | 0.519 | 0.474 | 0.511 | 0.655 | 0.683 |
| FuXi | 40.08 | 0.548 | 미제공 | 0.532 | 0.660 | 0.688 |
| NeuralGCM | 37.94 | 0.547 | 0.488 | 미제공 | 미제공 | 미제공 |
| Stormer | 45.12 | 0.607 | 0.527 | 0.570 | 0.726 | 0.760 |
| ArchesWeather-S | 48.92 | 0.650 | 0.542 | 0.562 | 0.833 | 0.873 |
| ArchesWeather-M | 44.96 | 0.615 | 0.527 | 0.539 | 0.783 | 0.819 |

레지스트리에는 u850/v850도 포함한다. **Phi500은 지오포텐셜이며 m 단위 지위고도가 아니다.**
q700은 kg/kg 입력을 평가 시 g/kg로 명시적으로 변환한다.
원 표의 SP 열은 표기와 본문의 mean-sea-level-pressure 간 의미를 확인하기 전까지 이관하지 않는다.
현재 본 프로젝트가 특히 필요로 하는 지면기압 sp의 조석 점수로 바꾸어 쓰지 않는다.
표의 훈련 GPU-day 환산값도 B200 비용으로 가져오지 않는다.

## 3. 강수 벤치마크는 평균 대기장과 별도다

출처: Zhao et al., GMD 18, 5781–5799 (2025), section 6.
https://gmd.copernicus.org/articles/18/5781/2025/gmd-18-5781-2025.html

2020, 전지구 1.5°, 00/12 UTC, 5일 lead의 24h 누적강수 상위10% 사건 ROCSS:

| 모델 | ROCSS (클수록 좋음) |
|---|---:|
| GraphCast | 0.46 |
| GraphCast operational | 0.50 |
| IFS HRES | 0.43 |

ROCSS=2×AUROC−1이며 0.50이 50% 적중률이라는 뜻은 아니다.
이 점수는 원시 연속 강수량을 순위화한 연속예측 점수가 아니다. 먼저 강수 예측을 `I(TP24h > q)` 사건으로
변환한다. 결정론 예측은 0/1이 되고, 앙상블은 임계값을 넘은 멤버 비율을 Weibull plotting position
`count(TP24h > q)/(M+1)`로 확률화한다. ROCSS는 그 사건 예측의 모든 확률 임계값에서의 분별력을 요약한다.
따라서 RMSE 같은 연속장 점수와 한 지표로 섞지 않는다.

논문은 격자별 ROCSS를 계산한 다음 전지구 점수에 면적 가중을 적용한다. 모든 격자와 시공간 사례를 한
혼동행렬로 합쳐 계산한 pooled-sample ROCSS와 다르다. 이 차이를 유지해야 격자별 면적 가중 결과를
같은 평가라고 부를 수 있다.

강수 사건 판정은 엄격한 `TP24h > q` 비교이며, 임계값과 같은 값은 비사건이다. 임계값은 각 격자에서
따로 추정한 2020년 ERA5 목표자료의 90분위수다. 이 연구는 **2020 검증자료에서 90분위 임계값을 계산**했다. 역사논문 재현과 달리, 개발/운영 성능 승인은
훈련·보정기간의 임계값을 동결하여 사용한다. 그러면 다른 프로토콜이므로 위 수치와 직접 등가 비교하지 않는다.
ERA5 강수가 검증자료인 한계도 유지하고 독립 우량계/레이더 등으로 추가 검증한다.
논문 코드 저장소는 Zenodo DOI `10.5281/zenodo.15067282` (v0.3.0)을 가리키고 README는
`Threshold_tp24h_150_2020_era5.nc` 파일을 열거한다. 이 배열은 Zenodo `10.5281/zenodo.15066898`의
`Thresholds.tar.gz`에서 취득했다. Zenodo에 등록된 archive MD5와 다운로드 파일의 MD5가 일치하며,
추출한 121×240 NetCDF 배열의 SHA-256은
`4c931d296cac13d6d83316a1d203ec34633f37ce944e36d5fb09120be6127667`이다. 파일에는 80, 85, 90, 93,
95, 96, 97, 98, 99분위 임계값이 있고 이 레코드는 90분위수를 가리킨다. 다만 코드 저장소는 논문의
표에 쓰인 정확한 코드 revision을 고정하지 않는다.
논문과 현재 확보한 README만으로는 한 격자에 관측 사건 또는 비사건 한쪽만 있는 경우의 ROCSS 처리도
확인할 수 없다. 따라서 임계값 배열과 해시는 확인했지만, 단일 클래스 격자 처리와 정확한 코드 revision,
예측 및 표본 lineage를 확인할 때까지 로컬 점수와의 비교는 막아 둔다. 원시 예측장·정확한 endpoint·sample lineage가 확보되지 않은 현재
상태에서 위 3개 수치는 외부 역사 참고값으로만 쓴다.

Pangu 등 강수 출력이 없는 기준모델의 강수 점수를 0으로 채우지 않는다. 다른 버전의 강수모듈을 붙였다면 별도 모델 ID다.

## 4. 모든 비교모델의 역할을 분리한다

- **GraphCast:** 기존 캐시와 공통 5층/지상변수 점수를 비교하는 6h 기준이다. 부족한 입력을 0으로 채워 공식 가중치를 실행하지 않는다.
- **Pangu-Weather:** 공개 `pangu_weather_1.onnx`는 진짜 1h 상태예측 비교 후보다. 13층 입력이 필요하므로 현재 5층 캐시만으로 실행하지 않는다. 이번 수치표는 24h이며 1h 점수가 아니다. 공식 구현: https://github.com/198808xc/Pangu-Weather
- **FuXi/Stormer/ArchesWeather:** 긴 rollout과 낮은 해상도의 계산–정확도 trade-off를 비교한다. 논문에서 쓴 checkpoint·반복/평균 방식을 확인한다.
- **NeuralGCM:** 미분가능 물리–AI 결합의 과학적 비교군이다. 예측점수가 좋다는 것과 본 프로젝트 E-M-P-H의 수반이 정확하다는 것은 별도다.
- **AIFS Single/ENS v2:** 운영 초기조건 적응의 기준이다. ECMWF는 2026-05-12 v2 운영 갱신을 명시한다. 2020의 역사 점수를 v2 점수로 재명명하지 않는다. https://www.ecmwf.int/en/forecasts/datasets/aifs-machine-learning-data
- **GenCast/FourCastNet 3:** 확률·스펙트럼·rollout 기준이다. 각각의 시간간격, 멤버 수, CRPS/fCRPS 정의를 고정한다. 이번에는 점수를 새로 계산하지 않았다. https://arxiv.org/abs/2312.15796 ; https://arxiv.org/abs/2507.12144

## 5. 승인 가능한 공통 평가 계약

외부 숫자만으로 PASS를 만들지 않는다. 다음 항목을 두 모델에서 일치시킨다.

`protocol ID / 초기시각 표본 hash / 검증자료 hash / 초기분석장 /
격자·면적·마스크 hash / 변수·단위·층 / lead / 구간 통계 /
결정론적값·ensemble mean 등 출력 통계 / 멤버 수 / 기후값·집계 방식`

모델 ID와 가중치 hash는 서로 다를 수 있지만 모두 기록한다. 사전학습·미세조정·모델선택의 시험자료 중복을 확인한다.
초기조건이 다르면 결과를 end-to-end system 비교로 표시하고, architecture-only 성능향상이라고 해석하지 않는다.
스키마/메타데이터 검사만으로 제출자의 실제 학습이력을 증명하지는 못한다.

**공통 평가격자:** 공개 표 대응은 1.5° 240×121 with-poles를 별도로 생성한다.
모델과 정답을 모두 같은 검증된 conservative overlap 연산자로 변환한다.
1°와 0.25° native 점수는 별도 표로 유지한다. 날카로운 구조는 native 스펙트럼·객체 평가도 수행한다.

**공통 lead:** 6,12,24,48,72,120,168,240h. 없는 표 점수를 시간보간해 채우지 않는다.
**현재 확보된 외부 숫자:** 24h RMSE와 120h 강수 ROCSS만이다. 72/168/240h 전체 점수는 로컬 재평가 또는 upstream 파일 decode 뒤 추가한다.

공식 WeatherBench-X 재현 안내: https://weatherbench-x.readthedocs.io/en/latest/benchmark.html
데이터/재격자화 설명: https://weatherbench2.readthedocs.io/en/latest/data-guide.html
upstream의 실제 코드 revision과 파일 목록을 확보한 뒤 평가환경을 고정한다. 문서 링크만으로 재현 완료를 선언하지 않는다.

## 6. 수학적 지표와 단계별 목표

고정 검증영역에서 초기시각 i의 면적 MSE를 e_i라 하면

`RMSE = sqrt(mean_i(e_i))`

를 사용한다. `mean_i(sqrt(e_i))`로 바꾸지 않는다. 공식 WB2도 평균 후 제곱근 규약을 설명한다.
https://weatherbench2.readthedocs.io/en/latest/evaluation.html

새 `case_area_mse()`는 이 로컬 규약의 작은 구현이다. 전체 WB-X 점수와 bitwise 같음을 증명한 것은 아니다.
유효한 검증영역의 NaN 예측은 오류로 처리한다. 예측을 보고 mask/평가 사례를 바꾸지 않는다.

낮을수록 좋은 점수의 상대 개선은 `1-S_model/S_baseline`로 보고한다. 서로 단위가 다른 지표를 먼저 평균하지 않는다.
ROCSS는 원점수 차이 등 방향에 맞는 비교를 사용한다. 평가기간 평균 점수 하나만으로 paired bootstrap을 만들 수 없다.

### 단계별 개발 목표

1. **로컬 실행 기준:** persistence, train-only climatology, 간단한 통계/비공유 모델을 동일 사례에서 넘어선다.
2. **6h 중기 기준:** HRES/GraphCast 등 공통 재평가와 24/72/120/240h의 상대오차를 비교한다.
3. **1h 목표:** Pangu 1h 등 실제 시간별 기준과 모든 시간의 오차, 24h/12h 위상·진폭·검증 불확실성을 비교한다.
4. **확률·비용:** 동일한 멤버 수/분포 의미에서 CRPS·Brier·신뢰도와 계산비용을 비교한다.

초기 비열등성 margin 2%는 제안값이다. 동결된 모델·독립 사례에서 시간 블록을 먼저 정하고 paired CI를 계산한다.
`paired_rmse_check()`는 후보와 기준의 **같은 사례** MSE를 block bootstrap하여 단일 지표만 판정한다.
10개 미만 블록은 거부하지만, 10개 이상이 자동으로 충분한 검정력을 뜻하지 않는다.
개선 지표가 나와도 강수·주기·고주파·물리·수치 gate가 별도로 통과하기 전에는 전체 모델을 승인하지 않는다.

## 7. 본 프로젝트의 차별화 지표는 별도로 유지한다

- 일/반일주기: 모든 시간 곡선, 복소계수, 최대시각, phase 공분산과 실제 유효 신호.
- 강수: tp1h/tp6h/tp24h 구간 일치; 평균과 분위수의 구분; 누적 멤버를 먼저 만들고 누적분포를 계산.
- 고주파: 멤버별 진폭과 공간 위상·이동·극값을 함께 평가. 단순 선명화나 mean-field의 강제 선명화 금지.
- 미분가능 NWP: E-M-P-H 전체 JVP/VJP, weighted-adjoint/Taylor, 연속/고해상도 참조 민감도, 보존과 wet/dry 경계.
- 스트리밍: valid/available/received/issue, 불변 snapshot, 실패 재시작, 내용해시. 추론속도와 발행 latency를 분리.
- 비용: 동일 정확도에서 GPU-seconds·메모리·실제 walltime·읽기/쓰기. 논문의 다른 하드웨어 속도를 B200 실측처럼 사용하지 않음.

WeatherBench 스펙트럼 페이지도 일부 AI 예측의 lead별 평활화와 최신 모델의 스펙트럼 미갱신 상태를 별도로 명시한다.
https://sites.research.google/gr/weatherbench/spectra/

## 8. 재현과 현재 한계

```bash
python -m pip install -e '.[test]'
python -m pytest tests/test_benchmark_contract.py -q
python scripts/check_benchmarks.py --out runs/benchmark-plan.json
```

새 시험은 수치 전사 레지스트리, 비교조건 충돌 차단, mask/NaN, RMSE 집계, 제조 paired CI,
계절 달력/저장량, 6h 표본의 반일 식별 반례를 검사한다.
**실제 ERA5 배열과 외부 예측모델은 실행하지 않는다.** 가중치·GPU·네트워크가 없어도 실행된다.
현재 공개 수치를 로컬 예보성능으로 오인하여 `forecast_skill_approved=true`를 만들 수 없도록 한다.
