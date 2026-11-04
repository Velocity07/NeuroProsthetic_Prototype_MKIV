# AP-102 Kinematics, Dynamics & Structural Mechanics Specification

This document details the mathematical framework, kinematic chains, actuator torque dynamics, and structural stress analyses for the AP-102 Mk-IV transhumeral cybernetic prosthesis.

---

## 1. Coordinate Frames & Denavit-Hartenberg (DH) Model

The limb is modeled as a 7-Degree-of-Freedom (DoF) serial manipulator (excluding independent underactuated digits):
* Shoulder attachment (Osteointegrated Anchor / Socket) to Elbow: $\text{Link } 1$
* Elbow Flexion/Extension ($0^\circ \text{ to } 135^\circ$): $\text{Joint } 1$
* Forearm Pronation/Supination (Wrist Roll $180^\circ$): $\text{Joint } 2$
* Wrist Pitch (Flexion/Extension $-90^\circ \text{ to } +90^\circ$): $\text{Joint } 3$
* 5 $\times$ Independent Digits (MCP, PIP, DIP joints)

### Modified DH Parameter Table

| Link $i$ | Joint Variable $\theta_i$ | Link Twist $\alpha_{i-1}$ | Link Length $a_{i-1}$ (mm) | Joint Offset $d_i$ (mm) | ROM Envelope |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1 (Elbow)** | $\theta_1$ | $0^\circ$ | $0$ | $310.0$ | $0^\circ \le \theta_1 \le 135^\circ$ |
| **2 (Forearm)** | $\theta_2$ | $90^\circ$ | $0$ | $260.0$ | $-90^\circ \le \theta_2 \le +90^\circ$ |
| **3 (Wrist Pitch)** | $\theta_3$ | $-90^\circ$ | $0$ | $0$ | $-90^\circ \le \theta_3 \le +90^\circ$ |
| **4 (Hand Palm)** | $0$ (Fixed) | $0^\circ$ | $45.0$ | $155.0$ | Fixed Base |

### Forward Kinematics Transformation Matrix
The homogeneous transformation matrix $T_i^{i-1}$ between consecutive joint frames is defined as:

$$T_i^{i-1} = \begin{bmatrix}
\cos\theta_i & -\sin\theta_i\cos\alpha_i & \sin\theta_i\sin\alpha_i & a_i\cos\theta_i \\
\sin\theta_i & \cos\theta_i\cos\alpha_i & -\cos\theta_i\sin\alpha_i & a_i\sin\theta_i \\
0 & \sin\alpha_i & \cos\alpha_i & d_i \\
0 & 0 & 0 & 1
\end{bmatrix}$$

---

## 2. Elbow Actuation & Torque Budgeting

### Mass Distribution
* **Forearm Mass ($m_f$):** $1.05 \text{ kg}$
* **Hand Assembly Mass ($m_h$):** $0.52 \text{ kg}$
* **Rated Terminal Payload ($m_L$):** $3.50 \text{ kg}$
* **Forearm Center of Mass ($r_{cm,f}$):** $0.14 \text{ m}$
* **Effective Load Radius ($r_L$):** $0.35 \text{ m}$

### Static Torque Equilibrium at Peak Moment ($\theta_1 = 90^\circ$)
The static torque $T_{\text{static}}$ acting on the elbow joint axis under horizontal cantilever extension:

$$T_{\text{static}} = g \cdot \left( m_f \cdot r_{cm,f} + m_h \cdot r_L + m_L \cdot r_L \right)$$

$$T_{\text{static}} = 9.81 \cdot \left( (1.05 \cdot 0.14) + (0.52 \cdot 0.35) + (3.50 \cdot 0.35) \right)$$

$$T_{\text{static}} = 9.81 \cdot (0.147 + 0.182 + 1.225) = 9.81 \cdot 1.554 = 15.25 \text{ Nm}$$

### Dynamic Sizing & Safety Margin
Accounting for an angular acceleration $\alpha_{\text{elbow}} = 4.5 \text{ rad/s}^2$ and safety factor $SF = 2.5$:

$$I_{\text{total}} \approx m_f r_{cm,f}^2 + (m_h + m_L)r_L^2 = (1.05 \cdot 0.14^2) + (4.02 \cdot 0.35^2) \approx 0.513 \text{ kg}\cdot\text{m}^2$$

$$T_{\text{dynamic}} = I_{\text{total}} \cdot \alpha = 0.513 \cdot 4.5 = 2.31 \text{ Nm}$$

$$T_{\text{peak}} = SF \cdot (T_{\text{static}} + T_{\text{dynamic}}) = 2.5 \cdot (15.25 + 2.31) = 43.9 \text{ Nm}$$

**Actuator Selection Verification:** The installed brushless DC motor coupled to the 100:1 harmonic drive delivers **$65.0 \text{ Nm}$ continuous rated output**, satisfying peak requirements with a $1.48\times$ operational reserve.

---

## 3. Finger Joint Kinematics & Tendon Routing

The digits employ an underactuated tendon-driven routing canal system ($\varnothing 1.2 \text{ mm}$ UHMWPE Dyneema cord) counteracted by return torsion springs.

### Tendon Capstan Friction Losses (Euler-Eytelwein Relation)
Tension drop through internal sleeve routing is governed by:

$$F_{\text{distal}} = F_{\text{proximal}} \cdot e^{-\mu \sum \phi_j}$$

Where:
* $\mu = 0.08$ (Low-friction PTFE sleeve against braided Dyneema)
* $\sum \phi_j = \text{Cumulative bending angle in radians} \approx 135^\circ = 2.356 \text{ rad}$

$$F_{\text{distal}} = F_{\text{proximal}} \cdot e^{-(0.08 \cdot 2.356)} = F_{\text{proximal}} \cdot e^{-0.1885} \approx 0.828 \cdot F_{\text{proximal}}$$

### Peak Grip Force Calculation
To deliver a nominal fingertip normal force $F_{\text{contact}} = 22 \text{ N}$ ($110 \text{ N}$ across 5 digits):
* Moment arm at distal phalanx ($r_d$): $12.0 \text{ mm}$
* Torsion spring return torque ($k = 0.45 \text{ Nm/rad}$ at $\Delta\theta = 1.2 \text{ rad}$): $\tau_{\text{spring}} = 0.54 \text{ Nm}$

$$F_{\text{tendon}} = \frac{F_{\text{contact}} \cdot r_{\text{lever}} + \tau_{\text{spring}}}{r_d \cdot e^{-\mu \phi}} = \frac{(22 \cdot 0.035) + 0.54}{0.012 \cdot 0.828} = \frac{1.31}{0.009936} \approx 131.8 \text{ N}$$

The $\varnothing 0.6 \text{ mm}$ braided Dyneema core holds an ultimate tensile limit of $\ge 392 \text{ N}$ ($40 \text{ kg}$ rating), achieving an operational safety factor of $2.97$.

---

## 4. Structural Stress & Anchor Mechanics

### Osteointegrated Bone Anchor Analysis
The grade-5 titanium (`Ti-6Al-4V`) transhumeral anchor is rated for a peak axial/bending load $P_{\text{max}} = 2,200 \text{ N}$.

* Outer core diameter ($d_{\text{anchor}}$): $24.0 \text{ mm}$
* Cross-sectional Area ($A$):
  $$A = \frac{\pi \cdot d^2}{4} = \frac{\pi \cdot (0.024)^2}{4} = 4.524 \times 10^{-4} \text{ m}^2$$
* Pure Axial Stress ($\sigma_{\text{axial}}$):
  $$\sigma = \frac{P}{A} = \frac{2200 \text{ N}}{4.524 \times 10^{-4} \text{ m}^2} = 4.86 \text{ MPa}$$
* Yield Strength ($\sigma_y$) of Ti-6Al-4V: $\ge 880 \text{ MPa}$
* Safety Margin: $\frac{880}{4.86} \gg 100$ (Load failure is governed by bone-matrix remodeling thresholds, not titanium shear failure).