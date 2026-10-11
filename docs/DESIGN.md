# Mathematical / meteorological / numerical boundary

## Scope

P0는 기존 전지구 LoopCast의 재학습이 아니라, 미분가능 수치예보와 연결할 순수 텐서 API의 실증이다.
유효시각/도착시각/발행시각, 파일, 재시도와 LAYA 판단은 계산 그래프 바깥에 둔다.
`ForecastStep`은 `(state, parameters, hour, longitude, latitude, evaporation) -> (state_next, rain_1h)`다.
실제 모델은 canonical D83에서 native control/state로 변환하는 adapter와 새 단위/미분 시험이 필요하다.
외부 Fortran/JAX/수치모델을 이미 연결했다는 주장은 없다. 커스텀 연산은 JVP/VJP 구현과 독립 검증을 요구한다.

## Toy equations: what is imposed, what is learned

시간 단위는 h, theta는 280K 기준 온도편차, q는 g/kg다. 단층 질량은 1000 kg/m2로 고정하여
q 감소 1 g/kg를 강수 물당량 1 mm와 대응시킨다. 외부 수분원 E는 g/kg/h다.

1. `d theta / dt = -r theta + a1 cos(omega t+lon) + a2 cos(2omega t+2lon)`의 정확한 1h 전이로 theta_a를 계산한다.
   r=1/48 h^-1, omega=2pi/24 h^-1. 복소 표현의 forcing factor는 `(exp(iw)-exp(-r))/(r+iw)`이다.
2. q_a=q+E. q_s=8 exp(0.06 theta_a).
3. beta=0.02+0.28 sigmoid(p0), h=beta sigmoid((q_a-q_s)/1.5).
4. C=q_a[1-exp(-h)], theta'=theta_a+2.5C, q'=q_a-C, P=C.
5. u/v는 위도별 f=2 Omega sin(lat)의 정확한 1h 회전행렬을 적용한다.

학습 파라미터는 p0,a1,a2 3개다. 수송/압력경도/연직역학은 없다. 수분원이 주어진 독립 컬럼이며
sigmoid는 포화 아래에서도 작은 응결을 만들므로 실제 미세물리나 무강수 확률모델이 아니다.
기본 q>=0,E>=0과 유한한 허용 입력에서 0<=C<=q_a, q'+P=q+E,
theta'+2.5q'=theta_a+2.5q_a, u'^2+v'^2=u^2+v^2가 성립한다.
보존관계는 코드로 넣었으며 신경망이 발견한 것이 아니다. 지구 전체 질량/에너지를 보존한다는 의미도 아니다.

## Numerical differentiation

JVP는 Jv, VJP는 J^T u다. 상태·계수를 함께 미분하며 6h rollout에서 확인한다.
양의 diagonal metric Wx, Wy에서 weighted adjoint는 `J*=Wx^-1 J^T Wy`다.
`<Jv,u>_Wy=<v,J*u>_Wx`를 검사한다. 단위가 다른 변수의 scale과 셀가중치를 명시한다.
이 dot-product 검사는 forward/reverse 계산의 일관성을 보여줄 뿐 둘이 동일한 잘못된 모델을 미분할
가능성을 없애지 않는다. 독립 중앙 유한차분과 `J(m+hv)-J(m)-h grad J.v=O(h^2)` Taylor 시험을 함께 수행한다.

현재 proof는 smooth toy 및 FP64에서의 표본/방향 검사다. clipping/limiter/응결 경계가 있는 외부 NWP에서는
미분 불능점, active set, 불연속 결정과 전역 오차를 다시 검사해야 한다. 전체 대기의 수축성을 강제하지 않는다.

## Diurnal / semidiurnal

시계는 절대시간에서 계산하고, 재시작이나 내부 반복 때문에 0으로 리셋하지 않는다.
건조 선형 thermal_step은 알려진 24h/12h forcing과 감쇠를 정확히 적분한다. 240h 진폭/위상을 검증한다.
이 phase 정확도는 강한 수학적 prior의 결과이며 실제 대기조석, Hough 구조, 관측 기압 위상의 검증이 아니다.
24h endpoint만 평가하면 sin(2pi t/24)+0.5sin(2pi t/12)의 큰 시간별 오차를 놓친다.

## Training / reference / leakage

고정 방정식의 96개 제조 초기상태에서 one-step 상태와 강수를 표적으로 3개 파라미터를 학습한다.
이동/가열/습윤 순서를 동일하게 정의하되 참조는 별도의 NumPy/SciPy DOP853 코드로 계산한다.
그 독립성은 구현/적분 경로의 독립성이지 실물 대기 정답의 독립성이 아니다.
별도 seed의 12개 초기조건을 240h 전개하며, 신경망 없이 사전 설계한 3개 상수를 복구하는 작은 역문제다.
L-BFGS의 일반적 전역수렴을 주장하지 않는다. 3개 초기화를 모두 보고하며 시험 결과로 기준을 낮추지 않는다.

## Sources consulted (2026-10-11)

- PyTorch JVP: https://docs.pytorch.org/docs/2.10/generated/torch.func.jvp.html
- PyTorch VJP: https://docs.pytorch.org/docs/2.10/generated/torch.func.vjp.html
- Taylor verification: https://dolfin-adjoint.github.io/dolfin-adjoint/documentation/verification.html
- Local source migration: evidence/source_provenance.json

실측 시간은 CPU의 이 작은 코드에만 적용한다. B200 학습기간이나 실자료 예측력으로 외삽하지 않는다.
