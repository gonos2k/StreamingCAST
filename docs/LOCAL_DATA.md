# Local data boundary v1

## 관리 책임

원자료와 대용량 배열은 로컬에 둔다. Git에는 코드, 단위/채널 계약, 공개 가능한 작은 지표만 둔다.
`demo`는 합성 NPZ와 manifest만 생성한다. 실제 자료의 로컬 인벤토리는
[ERA5_READINESS.md](ERA5_READINESS.md)에 기록했다. 해당 점검은 메타데이터·청크·일부 표본 확인이며,
실제 자료의 D83 변환이나 예측 실행은 아직 수행하지 않았다.

NPZ는 P0 계약시험용이다. 이 로더는 한 파일의 바이트를 메모리에 읽으므로 production Zarr 스트리밍 로더가 아니다.
기본 파일/해제 크기 한도는 256 MiB다. 실규모 자료는 로컬 처리 단계에서 분할/교체 어댑터를 설계해야 한다.
그 교체 후 동일한 시간·단위·해시·미분 시험을 다시 수행한다.

## 배열

- `state`: 부동소수점 `[point, channel]`, 시각 하나.
- `mask`: 같은 크기의 bool. 결측을 무강수/물리값 0으로 대체하지 않는다.
- `channels`, `units`: Unicode 문자열 배열. `streamingcast.schema.SCHEMAS`와 순서/단위가 정확히 같아야 한다.
- pickle/object 배열, Inf, 유효영역 NaN, 비어 있는 채널은 거부한다.
- d83-v1: T/Phi/u/v/omega/q 13층 + t2m/msl/u10/v10/sp, 83개.
- toy-column-v1: theta [K anomaly from 280 K], q [g/kg], u/v [m/s], 4개.
- D83의 q [kg/kg]와 toy의 q [g/kg]는 의도적으로 다르다. 암묵적 단위변환은 없다.

D83 계약 검사는 자료 변환의 기상학적 정확성을 인증하지 않는다. 압력축·구면 풍속기저·sp 마스크·
통계 추정·관측연산·품질관리는 별도 실증이 필요하다. toy 실행은 mask가 모두 참인 경우만 허용한다.

## manifest.json

각 레코드는 다음 필드를 정확히 제공한다.

```json
[{"event_id":"unique-local-event","source":"YOUR_SOURCE","revision":0,
  "valid_time":"2026-01-02T00:00:00Z",
  "available_time":"2026-01-02T00:20:00Z","received_time":"2026-01-02T00:25:10Z",
  "path":"states/sample.npz","sha256":"<actual file SHA-256>",
  "schema":"d83-v1","schema_sha256":"<schema_hash('d83-v1')>",
  "grid_sha256":"<hash of canonical local geometry>"}]
```

현재 레코드는 분석장용이다. `valid <= available <= received`이며 valid_time만 정시를 요구한다.
예측값/천문 강제력/정답표적을 분석 레코드에 혼합하지 않는다. future ephemeris는 별도 알려진 강제력이다.
`received_time`은 신뢰할 수 있는 로컬 수집기가 실제 수신 시각으로 기록해야 한다. 메타데이터를
임의로 과거로 바꾸면 이 코드가 사실을 알아낼 수 없다. SHA-256도 내용 불변성이지 관측 진실의 증명이 아니다.

`path`는 root 아래로 제한하고 symlink 해석 후 범위를 검사한다. 로드한 바이트의 해시를 검사한 뒤
바로 그 바이트를 역직렬화한다. snapshot 뒤 파일이 바뀌면 다시 읽을 때 실패한다.
두 입력은 같은 source/schema/grid여야 한다. grid hash는 로컬 처리기의 기하 선언으로,
현재 NPZ 로더가 원본 지형/경위도를 자동 비교하는 것은 아니다.

## 발행과 중복

Snapshot은 initialization-1h, initialization의 두 시각에서 issue 이전에 available/received된
최신 revision만 선택한다. 늦게 도착한 수정본은 새 발행에만 반영된다. 기존 Snapshot은 변경하지 않는다.
두 시각은 같은 SQLite read transaction에서 선택한다. 동시 수정 중의 혼합 조회를 피한다.

동일 event_id 재전송은 완전히 같은 내용일 때만 멱등적이다. 같은 버전의 서로 다른 이벤트/내용은 거부한다.
실행키에는 snapshot, 모델 digest, 설정을 넣는다. 같은 키의 다른 결과는 거부한다.
이는 단일 SQLite 실행원장의 원자성/멱등성이다. 여러 서버·외부 저장소를 아우르는 exactly-once를 주장하지 않는다.
배열 파일과 실행원장의 분산 트랜잭션은 아직 없다. 중단 시 고아 산출물이 남을 수 있다.

## 강수

시간별 총강수는 (start,end]의 mm다. 입력 강수의 모델 자동학습은 아직 없다.
이관한 products.py는 시간별 quantile을 합하지 못하게 한다.
멤버 궤적을 먼저 합한 뒤 누적분포의 분위수/초과확률을 계산한다. 결측시간/실패멤버를 버리지 않는다.
2025년 하루4회 240h 평가는 표적을 2026-01-10 18 UTC까지 필요로 한다. 이는 로컬 자료 취득과 별개의 계약이다.
