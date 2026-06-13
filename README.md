# Real-Time Neural Network Inference on STM32F407 under FreeRTOS

A quantized neural network classifier deployed on an STM32F407G-DISC1 microcontroller,
running as a real-time task under FreeRTOS with cycle-accurate inference timing measured
using the ARM Cortex-M4 DWT hardware counter.

---

## Hardware

| Component | Detail |
|-----------|--------|
| MCU | STM32F407VGTx — ARM Cortex-M4F @ 168 MHz |
| RAM | 192 KB SRAM |
| Flash | 1 MB |
| FPU | Yes (single-precision) |
| DSP | Yes (SIMD instructions) |
| Board | STM32F407G-DISC1 Discovery Kit |
| Debug interface | ST-LINK/V2-1 (on-board, SWD) |
| Host | MacBook Pro M5 Pro (Apple Silicon, macOS) |

---

## Development Environment

| Tool | Version |
|------|---------|
| STM32CubeIDE | 2.1.1 |
| STM32CubeMX | 6.17.0 |
| X-CUBE-AI | 10.2.0 |
| ST Edge AI Core | 2.2.0 |
| FreeRTOS | 10.3.1 (via CMSIS-RTOS v2) |
| Python | 3.12 |
| TensorFlow | 2.21.0 |

---

## Dataset

**UCI Human Activity Recognition (HAR) Dataset**
- Source: UCI Machine Learning Repository
- 30 subjects, smartphone accelerometer + gyroscope (waist-mounted)
- 6 activity classes: Walking, Walking Upstairs, Walking Downstairs, Sitting, Standing, Laying
- 561 pre-computed time and frequency domain features per sample
- Train split: 7,352 samples — Test split: 2,947 samples
- Features are normalized to [-1, 1]

---

## Model Architecture

A fully-connected feed-forward network, deliberately small to fit within the
MCU's memory constraints:

```
Input:   (561,)          — 561 pre-computed HAR features
Dense:   561 → 64        ReLU activation     35,968 parameters
Dense:   64  → 32        ReLU activation      2,080 parameters
Dense:   32  → 6         Softmax                198 parameters
Output:  (6,)            — class probabilities
─────────────────────────────────────────────────────────────
Total parameters:         38,246
```

Training: Adam optimizer, sparse categorical cross-entropy loss, 15 epochs,
batch size 32, validation on held-out test split.

---

## Quantization

Full integer quantization (INT8) using TensorFlow Lite post-training quantization
with a representative dataset of 100 calibration samples.

- Input type: INT8
- Output type: INT8
- Weight format: symmetric per-channel INT8
- All activations quantized to INT8

| Metric | FP32 Model | INT8 Model |
|--------|-----------|-----------|
| Accuracy | 94.67% | 94.67% |
| Accuracy drop | — | 0.00% |
| Model file size | 479.0 KB | 42.5 KB |
| Size reduction | — | 11.3× |

Zero accuracy degradation after quantization. The representative dataset
calibration correctly captured the activation ranges across all layers.

---

## On-Chip Resource Footprint

Analyzed by ST Edge AI Core (stedgeai) targeting stm32f4:

| Resource | Used | Available | Utilization |
|----------|------|-----------|-------------|
| Flash (weights + runtime) | 51.27 KB | 1,024 KB | 5.0% |
| RAM (activations + buffers) | 4.24 KB | 192 KB | 2.2% |
| MACC operations | 38,336 | — | — |

Breakdown:
- Weights (read-only flash): 37.65 KB
- Runtime library (flash): 13.62 KB
- Activations (RAM): 2.34 KB
- Runtime library (RAM): 1.90 KB

Input and output buffers are allocated within the activations buffer
(--allocate-inputs, --allocate-outputs).

---

## FreeRTOS Architecture

FreeRTOS 10.3.1 via CMSIS-RTOS v2 interface (CMSIS_V2). Three tasks with
distinct priorities create realistic scheduler competition during inference
timing measurement.

### Tasks

| Task | Entry Function | Priority | Stack |
|------|---------------|----------|-------|
| InferenceTask | StartDefaultTask | osPriorityNormal | 128 words |
| SensorTask | StartSensorTask | osPriorityAboveNormal | 128 words |
| LogTask | StartLogTask | osPriorityBelowNormal | 128 words |

### Inter-task Communication

| Object | Type | Configuration |
|--------|------|---------------|
| dataReadySem | Binary semaphore | SensorTask → InferenceTask signaling |
| logQueue | Message queue | 16 items × 4 bytes (uint32_t cycle counts) |

### Task Behaviour

**SensorTask (AboveNormal priority)**
Releases `dataReadySem` every 100 ms via `osDelay(100)`. Simulates a periodic
sensor interrupt — in a production system this would be replaced by a DMA
completion callback or hardware timer ISR feeding real sensor data.

**InferenceTask (Normal priority)**
Blocks on `dataReadySem`. On each release:
1. Reads DWT cycle counter (start)
2. Calls `MX_X_CUBE_AI_Process()` — one full inference pass
3. Reads DWT cycle counter (stop)
4. Computes elapsed cycles
5. Posts cycle count to `logQueue`

**LogTask (BelowNormal priority)**
Receives cycle counts from `logQueue`. Accumulates statistics across 1000
iterations: running min, max, sum (64-bit), and sum-of-squares (64-bit) for
numerically stable variance computation. Sets `stats_ready = 1` on completion,
which was used as the debugger breakpoint target for result extraction.
Also toggles PD12 (green LED) on each inference and PD13 (orange LED) every
100 inferences as a visual heartbeat.

---

## Timing Measurement Method

### DWT Cycle Counter

The ARM Cortex-M4 Data Watchpoint and Trace (DWT) unit provides a 32-bit
free-running CPU cycle counter. Enabled once at startup:

```c
CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
DWT->CYCCNT = 0;
DWT->CTRL   |= DWT_CTRL_CYCCNTENA_Msk;
```

Cycle-to-microsecond conversion: `time_us = cycles / 168.0`

Resolution: ~5.95 ns per cycle at 168 MHz. This provides sub-microsecond
timing precision — significantly better than HAL_GetTick() which has 1 ms
resolution.

### Measurement Conditions

- 1,000 consecutive inference runs
- SensorTask (AboveNormal) active and preempting throughout
- LogTask (BelowNormal) active and consuming queue items throughout
- Results extracted via CubeIDE debugger Expressions panel at breakpoint
  on `stats_ready = 1`

---

## Timing Results

| Metric | Value |
|--------|-------|
| Mean inference latency | 787.05 µs |
| Min inference latency | 787.05 µs |
| Max inference latency (WCET) | 787.07 µs |
| Jitter (σ) | < 0.01 µs |
| Total runs | 1,000 |
| Scheduler load | SensorTask + LogTask active |
| Measurement method | DWT hardware cycle counter |

The inference is fully deterministic: a spread of 3 CPU cycles (~18 ns) across
1000 runs under concurrent FreeRTOS scheduler load. This is consistent with
the absence of cache misses (Cortex-M4 has no data cache — all memory accesses
hit SRAM or tightly-coupled flash in a fixed number of cycles), and the absence
of dynamic memory allocation during inference (all buffers statically allocated).

---

## X-CUBE-AI Desktop Validation

Prior to on-target deployment, the generated C model was validated against the
original TFLite model on the host machine using ST Edge AI Core's inspector:

- Cross-accuracy (reference TFLite vs generated C model): **100.00%**
- Cosine similarity: 0.999998
- RMSE: 0.000713

This confirms the C code generation and INT8 quantization introduced no
additional numerical error beyond what was already present in the TFLite model.

---

## Repository Contents

```
├── train.py                  # Model training script (UCI HAR, FP32)
├── quantize.py               # INT8 post-training quantization script
├── rt_inf_latency.py         # Latency result visualization
├── accuracy_size_chart.py    # FP32 vs INT8 comparison chart
├── model_int8.tflite         # Quantized INT8 model (42.5 KB)
├── latency_histogram.png     # Inference timing visualization
├── accuracy_size_chart.png   # Quantization impact chart
├── f407_ai_rt/               # STM32CubeIDE project
│   ├── Core/Src/main.c       # Task implementations, DWT setup
│   ├── X-CUBE-AI/App/        # Generated AI runtime and app template
│   ├── Middlewares/          # FreeRTOS, HAL drivers
│   └── f407_ai_rt.ioc        # CubeMX configuration
└── README.md
```

Note: `UCI HAR Dataset/` and `model_fp32.h5` are excluded from the repository
(.gitignore). The dataset is available from the UCI ML Repository. The INT8
TFLite model is sufficient to reproduce the on-device results.

---

## Reproducing the Results

### 1. Train and quantize the model

```bash
python train.py        # produces model_fp32.h5
python quantize.py     # produces model_int8.tflite
```

### 2. Deploy to hardware

- Open `f407_ai_rt` in STM32CubeIDE 2.1.1
- Build (hammer icon) → Run (green arrow)
- Board: STM32F407G-DISC1, connected via Mini-USB ST-LINK port

### 3. Read timing results

- In CubeIDE, set a breakpoint on `stats_ready = 1` in `freertos.c`
- Run in debug mode
- After ~100 seconds (1000 × 100 ms), breakpoint fires
- Read `result_mean_us`, `result_min_us`, `result_max_us`, `result_sigma_us`
  from the Expressions panel

---

## Known Limitations and Planned Extensions

**UART output not implemented.** Timing results are currently extracted via
the CubeIDE debugger. A planned extension adds USART2 with retargeted printf,
enabling streaming of per-inference cycle counts to the host for offline
statistical analysis and histogram generation from real on-device data.

**Synthetic input data.** SensorTask feeds a fixed semaphore signal rather
than real sensor data. The inference runs on whatever data happens to be in
the activation buffer. A complete implementation would populate the input
buffer with actual 561-feature HAR windows from a stored test set.

**Image classifier not implemented.** The UCI HAR dataset (Option B) was
selected for its memory efficiency. An image classifier (Option A, 32×32
grayscale, Conv2D architecture) remains a planned extension.