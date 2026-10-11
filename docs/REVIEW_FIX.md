# PR #2 검토 반영과 미분 연결부 확장 — 2026-10-11

대상 원형: `2c21bccb58bc5dc9a967880ebf3494d82d1b44d3`.
실제 자료는 로컬 처리한다. 이번 변경은 4변수 제조 기둥 모델이며 D83/실제 NWP가 아니다.
원형 1시간 코어는 그대로 두고 검사 계층과 명시적 소시간 간격을 추가한다.

## 1. 검토사항 반영

| 검토사항 | 변경 | 실행 근거 |
|---|---|---|
| `assert`가 `-O`에서 제거됨 | `require`/`VerificationError`, 성공과 실패 JSON 명시 | false gradcheck 주입: 일반 실행과 -O 모두 비정상 종료, 기존 PASS 보고서를 FAIL로 교체 |
| 외부 list가 Snapshot을 변경함 | tuple 복사와 Record 원소 검증 | 원본 list 교체 후 기존 fingerprint 불변 |
| hour/외부수분 영역 누락 | `check_boundary`와 `checked_rollout` | NaN/vector/반시간/범위 초과 시계, 극단 수분원, 중간 비유한 출력 차단 |
| 유한한 출력이어도 NaN gradient 가능 | optimizer 갱신 전에 손실과 gradient 검사 | 비유한/누락 gradient 차단; 0 gradient는 식별성 부족일 수 있어 무조건 거부하지 않음 |
| 무관한 늦은 파일이 과거 inspect를 막음 | 메타데이터 원장과 as-of 파일 읽기 분리 | 발행 이후 missing 파일은 과거 발행에 무관; 적격 최신 파일 손상은 실패, 조용한 fallback 없음 |
| 결과 파일 교체와 receipt 중복의 혼동 | 내용해시 경로, 덮어쓰기 없는 설치, 읽기/등록 때 해시 재검사 | 변조된 기존 파일을 재등록/읽기/재설치할 때 실패; 고아파일 목록 보고 |

`check-catalog`는 의도적으로 모든 manifest 파일을 검증한다. `inspect`는 모든 메타데이터를
검증/등록하되 선택된 두 payload만 읽는다. 잘못된 미래 메타데이터 자체는 여전히 실패시킨다.
원장 등록은 개별 레코드의 원자성이지 manifest 전체의 원자적 트랜잭션이 아니다.

경계검사와 순수 코어를 분리한다. `rollout_substeps`는 JVP/VJP를 위한 저수준 텐서 함수이며
임의 입력에 대한 보호 함수가 아니다. 불신 입력은 먼저 `checked_rollout` 경로를 사용한다.
검사 결과나 선택 자체를 미분하지 않으며, 유효한 후보 텐서는 detach하지 않는다.

시험영역의 추가 한계는 E<=0.5 g/kg/hour, |u|/|v|<=300 m/s, |hour|<=1e6,
경도 +/-2pi rad다. 실제 기상현상의 불가능 판정이 아니라 제조모델의 사용영역이다.

## 2. 로컬 산출물 계약

`ArtifactStore.put_npz`는 같은 파일시스템 안에서 임시파일 fsync 후 hard-link로
`sha256/<prefix>/<digest>.npz`에 없을 때만 설치한다. 같은 주소의 내용이 다르면 덮어쓰지 않는다.
`verify/load/register`는 현재 바이트와 receipt를 다시 비교한다. SQLite에는 작은 메타데이터만 넣는다.
`recovery_report`는 정지된 원장의 고아파일/손상/레거시 레코드를 보고하며 자동 삭제하지 않는다.
파일 설치와 DB 등록 사이의 중단은 여전히 고아파일을 만들 수 있다. 분산 exactly-once가 아니다.
파일 소유자의 악의적 수정이나 부모 디렉터리의 동시 교체를 완전히 방어하는 보안 저장소도 아니다.

`demo/forecast.npz`는 기존 소비자 호환용 복사본이다. 원장이 가리키는 정식 산출물은
내용해시 경로다. 결과 확인 시 `receipt.json`의 `artifact_root`와 `artifact`를 사용한다.
파일 한도는 256 MiB이며 NPZ를 메모리에 읽는다. 운영 규모의 청크 저장은 여전히 후속 구현이다.

## 3. 명시적인 소시간 간격 확장

`substeps=1,2,4,8,16`, dt=1/substeps 시간. 기본값 1은 원형 함수를 그대로 호출한다.
열응답과 코리올리 회전은 구간 dt에 맞춰 계산한다. 외부수분은 시간당 rate이므로 dt*E만 추가한다.
응결은 같은 기존 frozen-hazard 식을 dt에 적용한다. 각 소구간 강수를 합하여 1시간 강수 한 개를 만든다.
매시간의 태양 위상을 초기화하지 않는다. `substeps`는 수치모델 설정과 실행키에 포함해야 한다.

이 분할식은 동시 수분-열 결합 ODE에 대해 약 1차로 수렴한다. 시간간격을 줄이는 것은
계산 정확도-비용의 선택이며, 기존 가중치의 실제 예측력을 자동으로 개선하는 보정은 아니다.

### 실제 연속 참조 비교 (24h, 한 제조 초기상태와 한 계수 방향)

| dt | 온도오차 K | q오차 g/kg | 계수 민감도 상대차 |
|---|---:|---:|---:|
| 1h | 0.166839 | -0.074923 | 3.54217% |
| 30min | 0.083949 | -0.037622 | 2.08522% |
| 15min | 0.042091 | -0.018868 | 1.11583% |
| 7.5min | 0.021073 | -0.009449 | 0.57597% |
| 3.75min | 0.010543 | -0.004729 | 0.29247% |

참조는 독립 SciPy DOP853의 동시 결합 ODE다. 원형 split 정답을 잘못된 것으로 바꿔 부른 것이 아니다.
참조 허용오차 강화에 따른 최대 상태차 2.53e-12, FD 간격 반감에 따른 민감도 변화 1.20e-9.
수렴차수는 0.9914..0.9990이며 전체 기상상태의 전역 수렴정리가 아니다.
CPU 전방 24h 측정 중앙값은 약 2.66/5.17/14.02/39.57/42.78 ms였다. 작은 표본의 잡음 있는
측정이며 B200 추산에 쓰지 않는다. 재실행 수치는 `expansion.json`을 따른다.

## 4. 미분 연결부 E-M-P-H

`coupling.py`는 SI [T K,q kg/kg,u,v m/s] -> [theta=T-280K,q g/kg,u,v] ->
선택한 소시간 간격의 순수 예보 -> SI 복원/강수합 -> 선형 관측가중 행렬을 연결한다.
실제 KIM/WRF/IFS, 지형, 모델층, 구면 보간 또는 D83 어댑터가 아니다.

F=H o P o M o E, DF=DH DP DM DE.
가중 수반은 J*=Wx^-1 J^T Wy이다. 바깥 경계검사를 통과한 고정 입력에서 전이와 단위/관측
연산까지 함께 미분한다. q 변환의 미분계수 1000을 생략하지 않는다.

6h/4-substeps 시험:
- 단위 정규화 JVP/중앙 FD 상대차 5.3703e-10.
- 가중 수반 상대차 7.0961e-16.
- Taylor 잔차 차수 2.00090, 2.00045, 2.00023, 2.00011.
- 독립 단위시험의 전체 체인 gradcheck 통과.

이산 미분 일치와 연속 참조 민감도 정확성은 별도로 보고한다. 양쪽이 자동으로 같은 주장이 아니다.

## 5. 실행 결과와 한계

원형 53시험 재통과. 수정판 107시험 통과(새 54개); 잘못된 입력/반례 보호 시험을 포함한다.
15분 소단계의 checked 240h 전개와 137+103h 재시작은 같은 CPU 환경에서 bitwise 일치했다.
수분수지 잔차는 3.70e-13 mm. 건조 S1/S2 240h 출력은 1h 원형과 최대 7.99e-15 K 차이다.
보존과 정확한 열응답은 코드의 성질이며 실제 대기조석 성능은 아니다.

원형 3계수/3초기화 학습도 재실행하여 기존 승인 기준을 통과했다. 역사 JSON과 완전한 bitwise
일치는 아니며 계수 최대차 2.78e-16 등 작은 반올림 차이를 summary.json에 보존했다.

불포화 q0=4, qs0=8, 공급/가열=0의 기존 240h 강수 2.02932mm는 아직 남는다.
wet/dry 미세물리, 0.25도, D83 장기 실패, 실제 ERA5/관측, LAYA/B200/외부 NWP는 미실행/미해결이다.
저수준 코어의 모든 입력에 대한 유한 gradient, 물리적 단조성, 전역 안정성도 주장하지 않는다.

## 6. 재현과 다음 단계

```bash
python -m pip install -e '.[test]'
python -m pytest -q
streamingcast demo --root local_data/new_demo
streamingcast prove --out runs/review_proof/proof.json
python scripts/prove_expansion.py --out runs/expansion.json
# 실제 파일은 로컬에서만 검사
streamingcast check-catalog --manifest /local/manifest.json --root /local/data --ledger runs/catalog.sqlite
```

`demo`는 새 디렉터리를 사용한다. `prove`는 실패를 FAIL JSON으로 기록하고 비정상 종료한다.
체크포인트와 실제 배열은 Git에 올리지 않는다. `.gitignore`와 로컬 자료 경계는 유지한다.
다음 단계는 wet/dry 과정과 실제 모델 상태/관측변환을 각각 연결하여 같은 미분·수렴시험을 수행하는 것이다.
이번 수정으로 실제 기상성능이나 main 병합을 승인하지 않는다.

## 근거 문서

- Python assert: https://docs.python.org/3.13/reference/simple_stmts.html#the-assert-statement
- PyTorch JVP/VJP: https://docs.pytorch.org/docs/2.10/func.html
- SciPy solve_ivp: https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
- 이번 실행 원자료: ../evidence/review_fix/expansion.json, summary.json, pytest.txt
