#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walidacja predkosci fali z CFD (metoda TOA z sond) wzgledem termochemii (Cantera).
Liczy:
  - W   : predkosc fali padajacej (z sond, kierunek +x ku klinowi)
  - D   : predkosc detonacji (z sond, kierunek -x od klina)
  - u_p : predkosc gazu (particle velocity) za fala padajaca (Cantera, szok zamrozony)
  - D_CJ: predkosc detonacji Chapmana-Jougueta (Cantera, rownowagowy Hugoniot)
Zaleznosci: cantera, numpy, scipy.  (SDToolbox NIEpotrzebny.)
"""
import csv
import numpy as np
from scipy.optimize import brentq, minimize_scalar, fsolve
import cantera as ct

# ============================ KONFIGURACJA ============================
CSV    = "p_combined_probes.csv"          # plik z sondami (eksport ParaView)
MECH   = "gri30.yaml"                      # mechanizm (Cantera 3.x -> .yaml!)
X      = "H2:0.15 O2:0.1785 N2:0.6715"     # 15% H2 molowo w powietrzu (O2:N2=0.21:0.79)
T0     = 300.0                             # temperatura napelnienia [K]  <-- POTWIERDZ
P0     = 102423.0                          # cisnienie napelnienia [Pa] (z danych)

# wspolrzedne x sond na osi (y=0.0453) + sonda przy klinie
XPROBE = {1: 1.096, 2: 1.346, 3: 1.594, 4: 1.722, 5: 1.846, 6: 1.92718}
DP_RISE = 30000.0          # prog "pierwszego narastania" [Pa] nad baseline (fala padajaca)

# ============================ TOA z CFD ============================
def load_csv(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f)][1:]
    data = np.array([r for r in rows if r and r[0].strip()], dtype=float)
    return data[:, 0], {i: data[:, i] for i in range(1, data.shape[1])}

def t_first_rise(t, p, dp=DP_RISE):
    base = np.median(p[:200])
    idx = np.where(p >= base + dp)[0]
    return t[idx[0]] if len(idx) else None

def t_peak(t, p):
    return t[np.argmax(p)]

def measure_speeds(t, P):
    # Fala padajaca: pierwsze narastanie, sondy 2->3->4->5 (+x)
    ti = {i: t_first_rise(t, P[i]) for i in (2, 3, 4, 5)}
    W = [ (XPROBE[b]-XPROBE[a])/(ti[b]-ti[a]) for a, b in [(2,3),(3,4),(4,5)] ]
    # Detonacja: czas piku, klin(6)->5->4 (-x)
    tp = {i: t_peak(t, P[i]) for i in (6, 5, 4)}
    D = [ abs(XPROBE[b]-XPROBE[a])/abs(tp[b]-tp[a]) for a, b in [(6,5),(5,4)] ]
    return float(np.mean(W)), W, D

# ============================ CANTERA ============================
def gas(T, P, X):
    g = ct.Solution(MECH); g.TPX = T, P, X; return g

def frozen_postshock(W, T1, P1, X):
    """Stan za fala uderzeniowa (sklad zamrozony) -> P2, T2, u_p."""
    g1 = gas(T1, P1, X); rho1 = g1.density; v1 = 1/rho1; h1 = g1.enthalpy_mass
    mdot = W*rho1; g2 = gas(T1, P1, X)
    def eqs(z):
        T2, v2 = z; P2 = mdot**2*(v1-v2)+P1; g2.TP = T2, P2
        return [g2.density - 1/v2,
                g2.enthalpy_mass + 0.5*(mdot*v2)**2 - h1 - 0.5*(mdot*v1)**2]
    T2, v2 = fsolve(eqs, [T1*1.5, v1*0.6]); P2 = mdot**2*(v1-v2)+P1
    return dict(P2=P2, T2=T2, up=W - mdot*v2, a1=g1.sound_speed, M=W/g1.sound_speed)

def cj_speed(T1, P1, X):
    """Predkosc detonacji CJ = minimum predkosci fali na Hugoniocie rownowagowym."""
    g1 = gas(T1, P1, X); v1 = 1/g1.density; h1 = g1.enthalpy_mass; gw = ct.Solution(MECH)
    def ws(ratio):                                  # ratio = v2/v1
        v2 = v1*ratio
        def hug(T2):                                # Rankine-Hugoniot (forma entalpowa)
            gw.TDX = T2, 1/v2, X; gw.equilibrate("TV")
            return gw.enthalpy_mass - h1 - 0.5*(gw.P - P1)*(v1 + v2)
        T2 = brentq(hug, 300, 6000)
        gw.TDX = T2, 1/v2, X; gw.equilibrate("TV")
        return np.sqrt(v1**2*(gw.P - P1)/(v1 - v2))
    res = minimize_scalar(ws, bounds=(0.45, 0.80), method="bounded", options={"xatol": 1e-5})
    v2 = v1*res.x
    def hug(T2):
        gw.TDX = T2, 1/v2, X; gw.equilibrate("TV")
        return gw.enthalpy_mass - h1 - 0.5*(gw.P - P1)*(v1 + v2)
    T2 = brentq(hug, 300, 6000); gw.TDX = T2, 1/v2, X; gw.equilibrate("TV")
    return res.fun, gw.T, gw.P

# ============================ MAIN ============================
if __name__ == "__main__":
    t, P = load_csv(CSV)
    Wmean, Wlist, Dlist = measure_speeds(t, P)
    ps = frozen_postshock(Wmean, T0, P0, X)
    Dcj0, Tc0, Pc0 = cj_speed(T0, P0, X)                 # CJ przy napelnieniu
    Dcj2, Tc2, Pc2 = cj_speed(ps["T2"], ps["P2"], X)     # CJ w gaz sprezony fala padajaca
    Dlab = Dcj2 - ps["up"]                                # detonacja w ukladzie laboratorium

    print("="*60)
    print(f"15% H2 / powietrze | p0={P0/1e5:.3f} bar  T0={T0:.0f} K")
    print("="*60)
    print(f"\n[CFD]  Fala padajaca W = {Wmean:.0f} m/s   "
          f"(odcinki: {', '.join(f'{w:.0f}' for w in Wlist)} m/s)")
    print(f"[CFD]  Detonacja D     = {', '.join(f'{d:.0f}' for d in Dlist)} m/s "
          f"(klin->5, 5->4)")
    print(f"\n[CAN]  a0 = {ps['a1']:.0f} m/s   M = {ps['M']:.2f}")
    print(f"[CAN]  za fala padajaca:  P2 = {ps['P2']/1e5:.2f} bar   T2 = {ps['T2']:.0f} K")
    print(f"[CAN]  predkosc gazu u_p = {ps['up']:.0f} m/s")
    print(f"\n[CAN]  D_CJ (napelnienie)      = {Dcj0:.0f} m/s  (T_CJ={Tc0:.0f}K, P_CJ={Pc0/1e5:.1f}bar)")
    print(f"[CAN]  D_CJ (gaz sprezony)     = {Dcj2:.0f} m/s  wzgl. gazu")
    print(f"[CAN]  D_lab = D_CJ - u_p      = {Dlab:.0f} m/s  <-- porownaj z CFD")
    print("="*60)

    # eksport do CSV pod LaTeX
    with open("walidacja_wyniki.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["wielkosc", "wartosc", "jednostka", "zrodlo"])
        w.writerow(["W_fala_padajaca", f"{Wmean:.0f}", "m/s", "CFD/TOA"])
        w.writerow(["M_fala_padajaca", f"{ps['M']:.2f}", "-", "Cantera"])
        w.writerow(["P2_za_czolem", f"{ps['P2']/1e5:.2f}", "bar", "Cantera"])
        w.writerow(["T2_za_czolem", f"{ps['T2']:.0f}", "K", "Cantera"])
        w.writerow(["u_p_predkosc_gazu", f"{ps['up']:.0f}", "m/s", "Cantera"])
        w.writerow(["D_CJ_napelnienie", f"{Dcj0:.0f}", "m/s", "Cantera"])
        w.writerow(["D_CJ_gaz_sprezony", f"{Dcj2:.0f}", "m/s", "Cantera"])
        w.writerow(["D_lab_teoria", f"{Dlab:.0f}", "m/s", "Cantera"])
        for i, d in enumerate(Dlist):
            w.writerow([f"D_CFD_odcinek_{i+1}", f"{d:.0f}", "m/s", "CFD/TOA"])
    print("Zapisano: walidacja_wyniki.csv")
