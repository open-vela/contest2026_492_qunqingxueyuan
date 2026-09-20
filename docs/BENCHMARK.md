# Benchmark

## What is measured

The danger input is already available before timing begins.

- reflex_compute: immediately before encoder/engine through engine output;
- end_to_end: event receipt through Safety Arbiter final command.

CLOCK_MONOTONIC is used. Each iteration resets engine state. The input is deterministic and forces the danger path. Sorting and reporting happen after all measurements.

## Host reference result

Measured on the local WSL host reference build on 2026-09-18. This is not openvela and not an MCU result.

| Path | Iterations | Min ns | Mean ns | Median ns | P95 ns | P99 ns | Max ns |
|---|---:|---:|---:|---:|---:|---:|---:|
| reflex_compute | 1000 | 10 | 18 | 20 | 20 | 21 | 60 |
| end_to_end | 1000 | 30 | 36 | 40 | 40 | 41 | 90 |

These sub-microsecond host numbers mainly show that the core is tiny; timer-call overhead and host optimization dominate.

## openvela simulator result

Measured on the openvela goldfish ARM64 simulator on 2026-09-18. This is simulator latency, not MCU latency.

| Path | Iterations | Min ns | Mean ns | Median ns | P95 ns | P99 ns | Max ns |
|---|---:|---:|---:|---:|---:|---:|---:|
| reflex_compute | 1000 | 1,152 | 1,400 | 1,200 | 2,144 | 9,776 | 17,552 |
| end_to_end | 1000 | 2,080 | 2,565 | 2,144 | 3,904 | 12,848 | 57,872 |

Exact NSH output:

    FlyReflex benchmark (measured locally with CLOCK_MONOTONIC)
    environment=openvela simulator/target iterations=1000 units=ns
    path,min,mean,median,p95,p99,max
    reflex_compute,1152,1400,1200,2144,9776,17552
    end_to_end,2080,2565,2144,3904,12848,57872

## Release candidate rerun

The subsequent 1000-iteration openvela ARM64 simulator measurement is recorded
in `evidence/target-runtime.txt`. It is a candidate-build measurement, not yet
bound to a frozen release commit.

| Path | Min ns | Mean ns | Median ns | P95 ns | P99 ns | Max ns |
|---|---:|---:|---:|---:|---:|---:|
| reflex_compute | 1232 | 1518 | 1264 | 1296 | 2528 | 112512 |
| event_to_arbiter (`end_to_end`) | 2224 | 2791 | 2256 | 2304 | 5296 | 179120 |

Neither measurement includes camera capture, network, browser rendering or
motor response. A UI frame is one sample under a different workload; its value
need not equal the benchmark median. Scheduling and simulator load can affect
outliers. Guard snapshot publication is outside the measured core interval.

## AI latency

2026-09-19 独立工作区候选固件（未冻结）补测：
`evidence/fresh-target-runtime.txt`，1000 次，reflex_compute
median/P95/P99=1152/1200/2096 ns；event_to_arbiter=2208/2272/4096 ns。
这是修复 Agent shell 错误分支及退出状态配置前的固件，不替代修复后回归。

The comparison uses a simulated AI command delay. It is not an LLM timing model.
The separate host-side MiMo connectivity probe took 1.935 seconds and 255 tokens;
see `evidence/mimo-connectivity.json`. This single short request does not measure
Agent planning performance or enter the reflex statistics.
