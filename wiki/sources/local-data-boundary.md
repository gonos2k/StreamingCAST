---
title: "Local Data Boundary"
instance_of: Source
page_kind: source-page
date_ingested: "2026-10-11"
provenance:
  sources: ["docs/LOCAL_DATA.md"]
  source_sha256: "34c27f85a78a9a9b8de3da9ab072098cbc4dc74da142ce50107f0bf699a213f3"
relations: []
---
# Local Data Boundary

## Summary
The local-data contract keeps raw and large arrays on the user’s machine and describes a bounded NPZ contract for tests. It distinguishes D83 units and channels from the four-variable toy and limits the SQLite ledger guarantees to a single local database; neither metadata hashes nor contract checks certify physical preprocessing or observation truth.

## Claims
- Real arrays stay local; the documented NPZ loader reads one file into memory and is not a production Zarr streaming loader. (["docs/LOCAL_DATA.md"](../../docs/LOCAL_DATA.md)) Evidence/location: “NPZ는 P0 계약시험용이다. 이 로더는 한 파일의 바이트를 메모리에 읽으므로 production Zarr 스트리밍 로더가 아니다.” (LOCAL_DATA.md, “배열”).
- D83 q uses kg/kg while toy q uses g/kg, so the contract does not silently convert between them. (["docs/LOCAL_DATA.md"](../../docs/LOCAL_DATA.md)) Evidence/location: “D83의 q [kg/kg]와 toy의 q [g/kg]는 의도적으로 다르다. 암묵적 단위변환은 없다.” (LOCAL_DATA.md, “배열”).
- Metadata and SHA-256 checks do not establish truthful availability or correct physical preprocessing. (["docs/LOCAL_DATA.md"](../../docs/LOCAL_DATA.md)) Evidence/location: “SHA-256도 내용 불변성이지 관측 진실의 증명이 아니다.” (LOCAL_DATA.md, “manifest.json”).
- Exactly-once claims are limited to the single SQLite ledger; there is no distributed transaction across arrays and the ledger. (["docs/LOCAL_DATA.md"](../../docs/LOCAL_DATA.md)) Evidence/location: “이는 단일 SQLite 실행원장의 원자성/멱등성이다. 여러 서버·외부 저장소를 아우르는 exactly-once를 주장하지 않는다.” (LOCAL_DATA.md, “발행과 중복”).

## Related
- [[entities/streamingcast]]
- [[entities/d83-schema]]
