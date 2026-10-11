# PR #2 Green/Red review — 2026-10-11

검토 대상: `2c21bccb58bc5dc9a967880ebf3494d82d1b44d3`. 이 review 브랜치는 원형 구현을 변경하지 않는다. 독립 LLM 두 팀을 호출한 것이 아니라 옹호·반박 가설을 분리하여 실제 시험으로 판정했다. 실제 자료·가중치·GPU 작업·LAYA는 사용하지 않았다.

## 판정

**P0 연구기반의 방향은 지지한다. 승인용 assert를 명시적 실패 처리로 바꾸고, Snapshot 및 입력 검사 경계를 보강한 뒤 병합하는 것이 적절하다. 실제 기상성능, 외부 NWP 통합과 B200 본학습은 계속 보류한다.**

## 실제 재현

- 원형25파일의 Git blob SHA가 고정 커밋 tree와 모두 일치했다.
- 원형53시험 재통과; 원형 prove도 재학습하여 seconds를 제외한 JSON이 기존 결과와 일치했다.
- 새 감사는 12개 묶음, 25개 회귀시험. **반례 재현도 포함하므로 PASS 수는 기상성능/배포 인증점수가 아니다.**
- Python3.13.5/PyTorch2.10.0+cpu/NumPy2.3.5/SciPy1.17.0, CPU 한 스레드, 주로 FP64. 결과는 `audit_checks.py`로 다시 생성한다.

## Green: 유지할 설계

순수 텐서 예보와 자료 수신·선택·결과 확정을 분리했다. 수정본은 발행시각 이전의 available/received 조건으로 고르고 두 레코드를 같은 읽기 트랜잭션에서 얻는다. 강수는 멤버별 궤적을 먼저 누적한 뒤 분포를 계산한다. D83의 단위계약과 toy의 다른 단위는 구분하며 이전 D83 240h 성능 실패를 숨기지 않는다.

새 3개 seed×1/24/240h 방향시험에서 이산 JVP 대 중앙 유한차분 최대 상대차는 **1.46346e-9**, VJP dot product 최대 상대차는 **2.49118e-15**였다. 수분/단순 열수지의 primal 잔차는 **7.10543e-15**, 그 방향미분 잔차는 **5.55112e-17**이었다. 표본에서 이산 코드의 미분이 이어진다는 근거이며 연속 원시방정식 수반을 검증한 것은 아니다.

두 SQLite 연결의 읽기 개수는 상대 연결 commit 전후 **2→2→3**이었다. 동일 결과 재등록은 False, 충돌 결과는 오류였다. 단일 호스트 WAL snapshot 격리를 지지한다.

## Red: 수정 항목

### R1. 검증 명령의 assert 제거 [P1]

`src/streamingcast/verification.py:69-71,98,151-153`.

테스트 프로세스에서 gradcheck가 False를 반환하도록 통제된 실패를 주입했다. 일반 Python은 exit1, `python -O`는 `gradcheck=false`인 결과와 exit0을 반환했다. 정상 미분이 실패했다는 뜻이 아니라 실패처리의 조건부 결함이다.

수정: 실제 승인 명령에는 `if not condition: raise VerificationError(...)`와 명시적 FAIL 상태를 사용한다. 테스트 코드의 assert와 구분한다. 두 실행모드 모두 동일 실패 주입을 차단해야 한다.

### R2. 공개 Snapshot의 얕은 불변성 [P2]

`src/streamingcast/stream.py:44-69`.

생성자에 list를 전달하면 통과한다. 생성 후 원래 리스트를 발행 뒤 도착한 레코드로 바꾸자 snapshot 내용과 fingerprint가 바뀌고 run_key가 생성되었다. 같은 내용을 새 Snapshot으로 만들면 올바르게 거부된다.

**Ledger.snapshot은 이미 tuple을 쓰므로 정상 내부 경로가 이 문제를 겪었다는 뜻은 아니다.** 공개 생성자는 tuple 복사/원소검증 또는 잘못된 타입의 명시적 거부가 필요하다.

### R3. 시각·외부 수분원·출력영역 검사 [P1, adapter 통합 전]

`physics.py:50-73`, `cli.py:54-59`.

validate_inputs에는 hour 인수가 없고 evaporation은 음수만 거부한다. 현실적이지 않은 계약시험 `E=100000 g/kg/h`가 검사를 통과했다. 3h 후 forward는 유한하지만 FP32/FP64 모두 gradient 5개가 NaN이었다. 시간 NaN도 외부검사에 포함되지 않는다.

수정: 순수 core는 그대로 두고 checked wrapper에서 시간 형상/단위/유한성, 명시적인 시험용 E 범위, 출력영역을 검사한다. 학습층에는 finite-gradient 및 실패기록을 둔다. 예측값이 유한하다는 것만으로 미분 유효성을 승인하지 않는다. 보통 기상자료에서도 이런 큰 E가 발생한다는 주장은 아니다.

### R4. 비관련 미래파일이 과거 inspect를 차단 [P2]

`cli.py:17-24`.

00:15에 유효한 두 파일로 검사한 후, 00:46 수정본을 manifest에 추가하고 그 파일은 없게 했다. 같은 00:15 inspect는 FileNotFoundError, DB의 원래 snapshot은 여전히 정상이다. 이는 누출이 아니라 가용성 결함이다.

ingest-all과 as-of inspect를 분리하고 선택한 파일만 로드한다. 최신 적격 파일이 손상된 경우에는 몰래 옛 수정본으로 바꾸지 말고 명시적인 후퇴 정책을 적용한다.

### R5. 결과 파일과 원장의 분리 [P2, 이미 고지된 한계]

`local.py:49-58`, `stream.py:116-129`.

파일을 다른 바이트로 교체하고 옛 receipt를 재등록하면 DB는 중복으로 False를 반환한다. 불변 hash 경로와 사용 시 hash 재검사, 고아 산출물 복구가 필요하다. 현재 fresh-root demo는 이 overwrite를 직접 일으키지 않는다. 파일+DB 분산 exactly-once를 구현했다고 주장하지 않는 기존 문구는 유지한다.

## 연속 NWP로 확장할 때의 수치 차이

원형 reference_step도 thermal→source→frozen hazard 순서를 동일하게 검증한다. 이는 문서화된 P0 범위다. 감사용으로 수분·가열이 동시에 작용하는 별도 ODE를 정의하고, dt=1에서 원형과 정확히 같은 split을 시간 세분했다.

|dt h|24h theta 오차 K|24h q 오차 g/kg|계수 방향민감도 상대차|
|---:|---:|---:|---:|
|1|0.166839|-0.074923|3.5422%|
|0.5|0.083949|-0.037622|2.0852%|
|0.25|0.042091|-0.018868|1.1158%|
|0.125|0.021073|-0.009449|0.5760%|
|0.0625|0.010543|-0.004729|0.2925%|

이는 **추가로 정의한 동시 결합 ODE**에 대한 1차 시간오차이며 원형의 같은 split 참조시험을 반박하지 않는다. 미분가능 외부 NWP에는 이산식의 JVP 일치와 연속계/고해상도 참조에 대한 민감도 일치를 별도 승인해야 한다. 자료·모델층·스케일 변환과 관측연산까지 chain rule을 이어야 한다.

## 비음수·보존성과 물리적 반응은 다르다

고정 theta_a에서 q'=qa exp(-beta S), S=sigmoid((qa-qs)/1.5)이므로

`dq'/dqa = exp(-beta S)*(1-qa*beta*S*(1-S)/1.5)`.

허용 입력 qa=qs=26, p0=10에서는 q'>0이지만 미분이 **-0.258167**이었다. 고정온도에서 rate를 계속 갱신하는 연속 스칼라 sink의 미분은 **+0.335773**였다. 이 스칼라 비교원리를 전체 결합대기에 그대로 강제하라는 뜻은 아니다.

불포화 q0=4, qs0=8 g/kg, 공급과 태양 가열진폭=0에서 1h 강수 0.03425mm, 240h 강수 **2.02932mm**가 나왔다. 이미 고지된 sigmoid drizzle의 장기 규모다. 실제 무강수 검증은 별도다.

96개의 원래 학습상태 Jacobian은 rank3, 특이값 [6.08875,1.63447,1.47487]이었다. q=E=0이면 rank2, p0 민감도는0이다. 국소 식별가능성은 과정이 충분히 여기된 자료에 의존한다. 가열·바람·강수의 모든 물리법칙이 학습된 것이 아니다.

## 실행

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python audits/pr2_20261011/audit_checks.py --source . --out runs/pr2_audit.json
python -m pytest audits/pr2_20261011/test_review.py -q
```

R1 실패 주입과 나머지 반례는 테스트 프로세스·임시 디렉터리에서만 실행한다. 운영 소스나 실제 자료를 수정하지 않는다. 새 audit 결과의 seconds·임시경로는 실행마다 달라진다.

## 공식 근거

- Python assert/-O: https://docs.python.org/3.13/reference/simple_stmts.html#the-assert-statement
- PyTorch numerical accuracy: https://docs.pytorch.org/docs/2.10/notes/numerical_accuracy.html
- JVP: https://docs.pytorch.org/docs/2.10/generated/torch.func.jvp.html
- Taylor verification: https://dolfin-adjoint.github.io/dolfin-adjoint/documentation/verification.html
- SQLite isolation/WAL: https://www.sqlite.org/isolation.html ; https://www.sqlite.org/wal.html

본 문서는 수정 제안과 검토 판정이다. 원형을 수정하거나 main/PR #2를 병합한 결과가 아니다.
