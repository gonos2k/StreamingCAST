---
title: StreamingCAST project overview
type: meta
date_modified: 2026-10-12
---
# StreamingCAST project overview

StreamingCAST implements streaming contracts, frozen issue-time snapshots and a
differentiable four-variable manufactured model. A global weather forecaster,
ERA5-to-model adapter and real-weather evaluation remain unimplemented. Prior
D83 240-hour failure remains unresolved. See [[entities/streamingcast]] and the
current [project status](../docs/PROJECT_STATUS.md).

The recorded global ERA5 cache has 44 annual stores (1979–2022), 5.48 TB, 0.25 degree,
six-hour cadence, five pressure levels and 30 channels: 29 instantaneous fields
plus six-hour rain. Coordinate/chunk checks and two t2m samples do not prove full
payload quality. Regional archives have missing dates/GRIB; regional 83 model
levels are not D83 channels. See [[entities/global-era5-cache]] and
[[sources/era5-readiness]].

The revised roadmap first verifies local data contracts (R0), then scores
six-hour persistence and train-only climatology (R1), tests regional hourly
connections (R2), obtains actual global hourly pilot inputs (R3) and expands
only after independent scientific gates (R4). The final D83+P1h objective remains:
83 instantaneous channels and separate hourly rain. Missing global hourly samples,
eight pressure levels, omega/sp and actual hourly precipitation are still gaps.
See [[sources/staged-roadmap]], [[entities/d83-schema]] and [[hot]].

The registry contains 60 published 24h RMSE values and three 120h precipitation
ROCSS values. These are historical references, not StreamingCAST forecasts or a
same-condition model ranking. Comparison contracts reject mismatched evaluation
conditions; forecast skill, precipitation, phase, differentiation and stability
have separate gates. See [[sources/published-score-register]] and
[[sources/comparison-acceptance]].

The proposed historical split is train1979–2017, select2018, calibrate2019,
test2020 (00/12 UTC), with targets through 2021-01-10 12 UTC for 240h forecasts.
Audit prior tuning/pretraining, including regional2020 data, before declaring
independence. The separate 2025 final evaluation still lacks targets through
2026-01-10 18 UTC.

GitHub on 2026-10-12 shows PR #3 and PR #4 merged to main. PR #5 merged to the data
branch; this new review branch carries KG integration forward. Historical test
records retain their scope: inventory115 versus PR #4's 107+40 subset147 excluding
the eight inventory tests. The pre-fix combined checkout passed 155 engineering tests
([receipt](../evidence/knowledge/integration_check.json)), with no real weather arrays read.
[[sources/execution-scope]] is not a weather approval. Post-merge comparison
hardening passes 66 contract tests (26 additional cases) and 181 combined
regression tests ([receipt](../evidence/knowledge/review_fix_check.json)); see
[[sources/comparison-hardening]]. ROCSS threshold bytes/hash are verified, but
single-class handling and exact scoring/forecast lineage remain unresolved.

The pinned kg v1 wiki and Graphify graph support navigation. Verify graph → wiki
→ original source and source revision. Original Source pages remain historical
snapshots when files evolve. Follow [[procedures/project-knowledge-cycle]].
