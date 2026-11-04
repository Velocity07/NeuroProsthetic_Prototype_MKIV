# AP-102 Bio-Neural Signal Processing & Decoding Pipeline Specification

This document defines the mathematical, architectural, and embedded requirements for the AP-102 Mk-IV neural signal conditioning chain, feature extraction engine, discrete state-space intent decoding, and closed-loop sensory feedback loop.

---

## 1. Bio-Signal Acquisition & Analog Front-End (AFE)

The signal path interfaces with either sub-dermal peripheral nerve cuff electrodes (Radial, Median, Ulnar bundles) or high-density surface electromyography (HD-sEMG) arrays across the residual limb musculature.

```
       [ Nerve Cuff / sEMG Electrodes ]
                      │
                      ▼
 ┌──────────────────────────────────────────┐
 │ Instrumental Pre-Amplification Stage     │
 │ - Gain: Av = 1000x (60 dB)               │[cite: 11]
 │ - CMRR: > 115 dB @ 50 Hz                 │
 │ - Input Impedance: Zin > 10 GΩ           │
 │ - Ground Return / Wilson Central Point   │
 └────────────────────┬─────────────────────┘
                      │
                      ▼
 ┌──────────────────────────────────────────┐
 │ Analog Anti-Aliasing Conditioning        │
 │ - 2nd-Order Sallen-Key Lowpass (fc=1 kHz)│
 │ - High-Pass DC Decoupling (fc = 10 Hz)   │[cite: 11]
 └────────────────────┬─────────────────────┘
                      │
                      ▼
 ┌──────────────────────────────────────────┐
 │ Simultaneous Sampling ADC Array          │
 │ - Resolution: 24-bit Delta-Sigma (ADS1299│
 │ - Sampling Rate (fs): 2000 Samples/sec   │
 │ - Interface: SPI @ 10 MHz Bus Speed      │[cite: 11]
 └──────────────────────────────────────────┘

```

### Front-End Electrical Tolerances

* **Bandwidth:** $10\text{ Hz}$ to $5\text{ kHz}$ primary bio-potential passband.


* **Input-Referred Noise:** $< 1.2\,\mu\text{V}_{\text{RMS}}$ across $10\text{ Hz} - 500\text{ Hz}$.
* **Electrode Impedance Range:** Nominal $Z \approx 50\,\Omega$ contact threshold with Pt/Ir sensor arrays; fault threshold flagged at $Z > 10\text{ k}\Omega$.



---

## 2. Digital Signal Processing (DSP) Conditioning Chain

Raw digital streams ingested via SPI are routed through deterministic, zero-latency phase-compensated digital filters running on the embedded telemetry processor.

```
  Raw ADC Stream (fs = 2000 Hz)
               │
               ▼
┌──────────────────────────────┐
│  4th-Order Butterworth BP    │
│  (Passband: 20 Hz – 450 Hz)  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  50 Hz IIR Comb/Notch Filter │  ◄── Eliminates mains coupling
│  (Q = 35, Rejection > 40 dB) │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Rectification / Normalizing │
│  (Z-Score standardization)   │
└──────────────┬───────────────┘
               │
               ▼
     Conditioned EMG Stream

```

### 2.1 Bandpass Filter Formulation (4th-Order Butterworth)

The continuous analog Butterworth filter transfer function:

$$\vert{}H(j\omega)\vert{}^2 = \frac{1}{1 + \left(\frac{\omega}{\omega_c}\right)^{2N}}, \quad N = 4$$

Transformed to the discrete domain via the Bilinear Transform $s = \frac{2}{T_s} \frac{1 - z^{-1}}{1 + z^{-1}}$, yielding cascaded Second-Order Sections (Biquads) to prevent numerical instability:

$$y[n] = \frac{b_0 x[n] + b_1 x[n-1] + b_2 x[n-2] - a_1 y[n-1] - a_2 y[n-2]}{a_0}$$

### 2.2 Powerline Notch Filter (50 Hz Rejection)

Implemented as a 2nd-order IIR notch filter with pole contraction factor $r = 0.95$:

$$H(z) = b_0 \frac{1 - 2\cos(\omega_0)z^{-1} + z^{-2}}{1 - 2r\cos(\omega_0)z^{-1} + r^2 z^{-2}}$$

Where $\omega_0 = \frac{2\pi \cdot 50}{f_s} = \frac{100\pi}{2000} = 0.05\pi\text{ rad/sample}$.

---

## 3. Windowing & Feature Space Extraction

Feature extraction operates over a sliding temporal window of $W = 150\text{ ms}$ ($N_w = 300\text{ samples}$ at $f_s = 2000\text{ Hz}$) with a continuous advance step of $\Delta t = 30\text{ ms}$ ($60\text{ samples}$), generating fresh inference vectors every $30\text{ ms}$.

```
Temporal Window Buffer:
|─────────────────── 150 ms (Window W) ───────────────────|
[ x[n-299], x[n-298], ... , x[n-1], x[n] ]
      │◄── 30 ms Stride ──►│

```

For each channel $c \in \{1, \dots, C\}$, the vector extraction pipeline computes six time-domain primitives:

### 3.1 Mean Absolute Value (MAV)

Reflects muscle contraction amplitude and aggregate motor-unit recruitment:

$$\text{MAV}_c = \frac{1}{N_w} \sum_{i=1}^{N_w} \vert{}x_c[i]\vert{}$$

### 3.2 Root Mean Square (RMS)

Direct proxy for electrical signal power and motor unit activity:

$$\text{RMS}_c = \sqrt{\frac{1}{N_w} \sum_{i=1}^{N_w} x_c[i]^2}$$

### 3.3 Waveform Length (WL)

Cumulative measure of signal complexity and temporal variability:

$$\text{WL}_c = \sum_{i=1}^{N_w - 1} \vert{}x_c[i+1] - x_c[i]\vert{}$$

### 3.4 Zero Crossing Count (ZC)

Frequency-domain proxy counting signal sign transitions beyond a noise deadband $\epsilon$:

$$\text{ZC}_c = \sum_{i=1}^{N_w - 1} \mathbf{1}\Big( \big(x_c[i] \cdot x_c[i+1] < 0\big) \land \big(\vert{}x_c[i] - x_c[i+1]\vert{} \ge \epsilon\big) \Big)$$

Where $\epsilon = 3 \times \sigma_{\text{baseline noise}}$.

### 3.5 Slope Sign Changes (SSC)

Tracks local signal inflection count to capture firing-rate shifts:

$$\text{SSC}_c = \sum_{i=2}^{N_w - 1} \mathbf{1}\Big( \big(x_c[i] - x_c[i-1]\big) \cdot \big(x_c[i] - x_c[i+1]\big) > 0 \land \text{inflection} \ge \epsilon \Big)$$

### 3.6 Willison Amplitude (WAMP)

Counts occurrences where the absolute differential between adjacent samples surpasses threshold $\alpha$:

$$\text{WAMP}_c = \sum_{i=1}^{N_w - 1} f\big(\vert{}x_c[i] - x_c[i+1]\vert{}\big), \quad f(u) = \begin{cases} 1, & u \ge \alpha \\ 0, & u < \alpha \end{cases}$$

---

## 4. Real-Time Neural Intent Decoding Engine

The feature vectors $\mathbf{f}_t \in \mathbb{R}^{C \times 6}$ feed an edge-quantized Structured State-Space Model (S4 / Mamba-based sequence operator) to track continuous intended joint trajectories alongside discrete grasp states.

```
       Extracted Feature Tensor: f_t ∈ R^(Channels × 6)
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  Linear Input Projection (d_model = 64)   │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  Continuous-Time Structured State-Space   │
        │  Layer (SSM Block):                       │
        │    h'[t] = A h[t] + B x[t]                │
        │    y[t]  = C h[t] + D x[t]                │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  Recurrent State Discretization (Zero-    │
        │  Order Hold):                             │
        │    A_bar = exp(Δ · A)                     │
        │    B_bar = (Δ · A)^(-1) (exp(Δ · A) - I)B │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  Dual Prediction Heads:                   │
        │  1. Softmax Grasp Classifier (7 Classes)  │
        │  2. Proportional Regressor (Joint Angles) │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
           Actuator Trajectory Vector (PWM / CAN)

```

### 4.1 State-Space Advantage on Edge Hardware

Unlike standard Recurrent Neural Networks (RNNs) which suffer from exploding/vanishing gradients, or Transformers that demand $\mathcal{O}(L^2)$ attention memory, discretized State-Space Models maintain an $\mathcal{O}(1)$ step inference complexity with constant RAM consumption during deployment on embedded targets (e.g., ARM Cortex-M4 / ESP32-S3):

$$h_t = \mathbf{\bar{A}} h_{t-1} + \mathbf{\bar{B}} x_t$$

$$y_t = \mathbf{\bar{C}} h_t + \mathbf{\bar{D}} x_t$$

### 4.2 Grasp Classification Classes

1. **Neutral / Rest** (Tendon relaxation state)
2. **Cylindrical Power Grasp** (Full 5-finger closure, $F_{\text{grip}} \le 110\text{ N}$)


3. **Precision Pinch** (Thumb opposition against Index/Middle digit)
4. **Index Point / Trigger** (Isolation of phalanx actuator 1)
5. **Lateral / Key Pinch** (Thumb flexion against lateral margin of index)
6. **Hand Open / Extension** (Active agonist-antagonist tendon stretch)
7. **Wrist Pronation / Supination** ($180^\circ$ continuous roll)



---

## 5. Closed-Loop Afferent Sensory Feedback

To restore proprioception and tactile perception, piezoresistive fingertip sensors close the loop back to the peripheral nerve cuff:

```
  Contact Surface Force F_grip (0 – 110 N)[cite: 7, 9, 10]
                     │
                     ▼
  Piezoresistive Resistive Divider Array
                     │
                     ▼
  Analog-to-Digital Converter (12-bit ADC)
                     │
                     ▼
  Feedback Micro-Stimulation Modulator
  - Amplitude: I_stim = 10 μA – 50 μA[cite: 11]
  - Frequency Modulation: 20 Hz – 120 Hz[cite: 12]
  - Charge-Balanced Biphasic Pulse (Phase Width: 200 μs)
                     │
                     ▼
  Optocoupled Galvanic Isolation Barrier (Safety Limit)[cite: 11]
                     │
                     ▼
  Platinum-Iridium Nerve Cuff Interconnect (Afferent)[cite: 11, 12]

```

### Charge-Balanced Safety Equation

To prevent tissue electrolysis and electrode degradation at the neural interface, net injected DC charge per phase must integrate to zero:

$$Q_{\text{net}} = \int_0^{T_{\text{cathodic}}} I_{\text{stim}}(t)\,dt + \int_{T_{\text{cathodic}}}^{T_{\text{anodic}}} I_{\text{stim}}(t)\,dt = 0$$

Where maximum charge injection per phase $Q_{\text{inj}} \le 4\,\text{nC/phase}$, well within the water window of platinum-iridium interfaces.

---

## 6. End-to-End Latency & Timing Budget

| Processing Phase | Method / Hardware Execution | Latency Allocation |
| --- | --- | --- |
| **Data Acquisition** | ADS1299 ADC conversion + SPI DMA transfer

 | $0.50\text{ ms}$ |
| **Digital Filtering** | 4th-Order Bandpass + 50 Hz Notch (ARM CMSIS-DSP) | $0.45\text{ ms}$ |
| **Feature Extraction** | Rolling window metrics (RMS, MAV, WL, ZC, SSC) | $0.65\text{ ms}$ |
| **Model Inference** | Quantized INT8 SSM execution (Edge NPU/DSP) | $1.80\text{ ms}$ |
| **Actuator Bus Dispatch** | CAN-FD / PWM generation to motor drivers

 | $0.35\text{ ms}$ |
| **Total Algorithmic Latency** | Ingestion to driver gate output

 | **$\mathbf{3.75\text{ ms}}$** |
| *Engineering Margin* | Target threshold: $< 4.8\text{ ms}$

 | *Pass ($1.05\text{ ms}$ headroom)* |

---

