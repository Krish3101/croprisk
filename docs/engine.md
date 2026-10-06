# CropRisk Engine Specifications and Golden Vector Derivations

This document describes the pure mathematical formulations implemented in `backend/app/domain/engine.py` and provides step-by-step worked derivations for all 10 automated test vectors.

---

## 1. Mathematical Formulation

The CropRisk engine consumes normalised 3-hour forecast intervals (40 cover 5 days; `weather.fetch_forecast` rejects forecasts with fewer than 8, the engine itself does not check) and computes five hazard stress indices $I \in [0, 100]$:

1. **Extreme Heat ($I_{\text{heat}}$):**
   $$\Delta T_{\text{peak}} = \max(0, \max(T) - T_{\text{crit,heat}})$$
   $$\text{DH} = \sum \max(0, T_i - T_{\text{crit,heat}}) \times 3$$
   $$I_{\text{heat}} = \left[\min\left(1, \frac{\Delta T_{\text{peak}}}{T_{\text{lethal,heat}} - T_{\text{crit,heat}}}\right) \times 70.0\right] + \left[\min\left(1, \frac{\text{DH}}{36.0}\right) \times 30.0\right]$$

2. **Frost Damage ($I_{\text{frost}}$):**
   $$I_{\text{frost}} = \min\left(1, \max\left(0, \frac{T_{\text{crit,frost}} - \min(T)}{T_{\text{crit,frost}} - T_{\text{lethal,frost}}}\right)\right) \times 100.0$$

3. **Excess Precipitation ($I_{\text{precip}}$):**
   Evaluated over an 8-interval sliding rolling 24-hour sum:
   $$R_{24,\max} = \max_k \sum_{j=k}^{k+7} \text{rain}_j$$
   $$I_{\text{precip}} = \min\left(1, \max\left(0, \frac{R_{24,\max} - R_{\text{crit,24h}}}{R_{\text{flood,24h}} - R_{\text{crit,24h}}}\right)\right) \times 100.0$$

4. **Fungal Disease Pressure ($I_{\text{disease}}$):**
   Consecutive hours $L$ meeting $\text{RH} \ge \text{RH}_{\text{crit}}$ and $T_{\text{min,dis}} \le T \le T_{\text{max,dis}}$:
   $$I_{\text{disease}} = \begin{cases} 0 & \text{if } L < 12 \\ \min\left(100.0, 30.0 + \frac{L - 12}{24.0} \times 70.0\right) & \text{if } L \ge 12 \end{cases}$$

5. **Wind Lodging ($I_{\text{wind}}$):**
   $$I_{\text{wind}} = \min\left(1, \max\left(0, \frac{\max(W) - W_{\text{crit,lodge}}}{W_{\text{severe}} - W_{\text{crit,lodge}}}\right)\right) \times 100.0$$

### Score Aggregation

Each hazard produces a weighted contribution $C_h = w_h \times I_h$.
- Weighted sum: $S_{\text{wsum}} = \sum_h C_h$
- Dominant risk: $R_{\text{dom}} = \frac{\max_h C_h}{\max_h w_h}$
- Final score: $\text{Score} = \text{round\_half\_up}(\min(100, \max(S_{\text{wsum}}, R_{\text{dom}})))$

Severity bands:
- $\text{Score} \le 29 \implies \text{LOW}$
- $30 \le \text{Score} \le 65 \implies \text{MODERATE}$
- $\text{Score} \ge 66 \implies \text{HIGH}$

Biological tie-break order for Primary Threat:
$$\text{Frost (5)} > \text{Heat (4)} > \text{Precip (3)} > \text{Wind (2)} > \text{Disease (1)}$$

---

## 2. Worked Golden Vector Derivations

### Vector 1: Lethal Heat during Wheat Anthesis
- **Stage:** `wheat.anthesis` ($T_{\text{crit}}=27^\circ\text{C}, T_{\text{lethal}}=34^\circ\text{C}$, weights: heat 0.35, frost 0.30, precip 0.15, dis 0.15, wind 0.05).
- **Inputs:** $T=38^\circ\text{C}, \text{RH}=40\%, W=5\text{ km/h}, R=0\text{ mm}$.
- **Derivation:** $\Delta T_{\text{peak}} = 38 - 27 = 11 \ge 7 \implies \text{Peak term} = 70.0$. $\text{DH} = 40 \times (11 \times 3) = 1320 \ge 36 \implies \text{Duration term} = 30.0$.
- $I_{\text{heat}} = 100.0$. $C_{\text{heat}} = 0.35 \times 100 = 35.0$. $R_{\text{dom}} = 35.0 / 0.35 = 100.0$.
- **Result:** Score = 100, Severity = HIGH, Primary Threat = Extreme Heat.

### Vector 2: Moderate Frost in Wheat Anthesis
- **Stage:** `wheat.anthesis` ($T_{\text{crit,frost}}=1.0^\circ\text{C}, T_{\text{lethal,frost}}=-2.0^\circ\text{C}$).
- **Inputs:** $T=-1.0^\circ\text{C}, \text{RH}=50\%, W=10, R=0$.
- **Derivation:** $I_{\text{frost}} = \frac{1.0 - (-1.0)}{1.0 - (-2.0)} \times 100 = \frac{2}{3} \times 100 = 66.67\%$.
- $C_{\text{frost}} = 0.30 \times 66.67 = 20.0$. $R_{\text{dom}} = 20.0 / 0.35 = 57.14$.
- **Result:** Score = 57, Severity = MODERATE, Primary Threat = Frost Damage.

### Vector 3: Saturated Rice Tillering Disease Pressure
- **Stage:** `rice.tillering` ($\text{RH}_{\text{crit}}=85\%, T_{\text{min,dis}}=22^\circ\text{C}, T_{\text{max,dis}}=32^\circ\text{C}$).
- **Inputs:** $T=27.0^\circ\text{C}, \text{RH}=90\%, W=10, R=0$.
- **Derivation:** All 40 intervals match disease window $\implies L = 120\text{ h}$.
- $I_{\text{disease}} = 30.0 + \frac{120 - 12}{24} \times 70 = 30 + 315 \implies 100.0$.
- $C_{\text{disease}} = 0.35 \times 100 = 35.0$. $R_{\text{dom}} = 35.0 / 0.35 = 100.0$.
- **Result:** Score = 100, Severity = HIGH, Primary Threat = Fungal Disease Pressure.

### Vector 4: Ideal Conditions (Zero Risk)
- **Stage:** `wheat.anthesis`.
- **Inputs:** $T=20^\circ\text{C}, \text{RH}=50\%, W=10, R=0$.
- **Derivation:** All parameters inside benign zone. All $I_h = 0.0$.
- **Result:** Score = 0, Severity = LOW, Primary Threat = None.

### Vector 5: Ripening Wheat Heat Tolerance
- **Stage:** `wheat.ripening` ($T_{\text{crit}}=35^\circ\text{C}, T_{\text{lethal}}=42^\circ\text{C}$, heat weight 0.10, max weight 0.35).
- **Inputs:** $T=38^\circ\text{C}, \text{RH}=40\%, W=5, R=0$.
- **Derivation:** $\Delta T_{\text{peak}} = 38 - 35 = 3$. $\text{Peak term} = (3/7) \times 70 = 30.0$. $\text{DH} = 40 \times (3 \times 3) = 360 \ge 36 \implies \text{Duration term} = 30.0$.
- $I_{\text{heat}} = 60.0$. $C_{\text{heat}} = 0.10 \times 60.0 = 6.0$. $R_{\text{dom}} = 6.0 / 0.35 = 17.14$.
- **Result:** Score = 17, Severity = LOW, Primary Threat = Extreme Heat.

### Vector 6: Cotton Harvest Rain vs Wind Tie-Break
- **Stage:** `cotton.harvest` ($R_{\text{crit}}=20, R_{\text{flood}}=40, W_{\text{crit}}=30, W_{\text{severe}}=50$, weights: precip 0.50, wind 0.25).
- **Inputs:** $T=25^\circ\text{C}, \text{RH}=90\%, W=55, R=3.75\text{ mm/block} \implies R_{24,\max} = 30\text{ mm}$.
- **Derivation:** $I_{\text{precip}} = \frac{30 - 20}{40 - 20} \times 100 = 50.0$. $C_{\text{precip}} = 0.50 \times 50.0 = 25.0$.
- $I_{\text{wind}} = 100.0 \implies C_{\text{wind}} = 0.25 \times 100 = 25.0$.
- Tie-break: Precip (3) beats Wind (2) $\implies$ Primary Threat = Excess Precipitation.
- $S_{\text{wsum}} = 25.0 + 25.0 + 15.0 = 65.0$. $R_{\text{dom}} = 25.0 / 0.50 = 50.0$.
- **Result:** Score = 65, Severity = MODERATE, Primary Threat = Excess Precipitation.

### Vector 7: Time-Varying 24h Rain Burst
- **Stage:** `wheat.anthesis` ($R_{\text{crit}}=35, R_{\text{flood}}=75$, precip weight 0.15, max weight 0.35).
- **Inputs:** 40 intervals. Rain burst in intervals 12–19 (8 intervals $\times$ 7 mm = 56.0 mm). Total 5-day rain = 80 mm.
- **Derivation:** $R_{24,\max} = 56.0\text{ mm}$. $I_{\text{precip}} = \frac{56.0 - 35.0}{75.0 - 35.0} \times 100 = 52.5$.
- $C_{\text{precip}} = 0.15 \times 52.5 = 7.875$. $R_{\text{dom}} = 7.875 / 0.35 = 22.5$.
- **Result:** Score = 23, Severity = LOW, Primary Threat = Excess Precipitation.

### Vector 8: Interrupted Humidity Infection Run
- **Stage:** `wheat.anthesis` ($\text{RH}_{\text{crit}}=80\%$).
- **Inputs:** 3 intervals at 85% RH (9h), 1 dry interval at 65% RH, 6 intervals at 85% RH (18h).
- **Derivation:** The dry gap resets the counter. Longest continuous run is 18h.
- $I_{\text{disease}} = 30.0 + \frac{18 - 12}{24} \times 70.0 = 47.5$.
- $C_{\text{disease}} = 0.15 \times 47.5 = 7.125$. $R_{\text{dom}} = 7.125 / 0.35 = 20.36$.
- **Result:** Score = 20, Severity = LOW, Primary Threat = Fungal Disease Pressure.

### Vector 9: Diurnal Thermal Heat Stress
- **Stage:** `maize.silking` ($T_{\text{crit}}=34^\circ\text{C}, T_{\text{lethal}}=39^\circ\text{C}$, heat weight 0.40).
- **Inputs:** 4 afternoon blocks at 36°C (+2°C over crit), remainder 28°C.
- **Derivation:** $\Delta T_{\text{peak}} = 2^\circ\text{C} \implies \text{Peak term} = (2/5) \times 70 = 28.0$.
- $\text{DH} = 4 \times (2 \times 3) = 24\text{ degree-hours} \implies \text{Duration term} = (24/36) \times 30 = 20.0$.
- $I_{\text{heat}} = 48.0$. $C_{\text{heat}} = 0.40 \times 48.0 = 19.2$. $R_{\text{dom}} = 19.2 / 0.40 = 48.0$.
- **Result:** Score = 48, Severity = MODERATE, Primary Threat = Extreme Heat.

### Vector 10: Score 29 Boundary Pinning
- **Stage:** `mustard.flowering` ($T_{\text{crit,frost}}=2.0^\circ\text{C}, T_{\text{lethal,frost}}=-2.0^\circ\text{C}$, frost weight 0.35).
- **Inputs:** Single cold morning dipping to $0.84^\circ\text{C}$.
- **Derivation:** $I_{\text{frost}} = \frac{2.0 - 0.84}{4.0} \times 100 = 29.0$.
- $C_{\text{frost}} = 0.35 \times 29.0 = 10.15$. $R_{\text{dom}} = 10.15 / 0.35 = 29.0$.
- **Result:** Score = 29, Severity = LOW (upper edge of LOW band), Primary Threat = Frost Damage.
