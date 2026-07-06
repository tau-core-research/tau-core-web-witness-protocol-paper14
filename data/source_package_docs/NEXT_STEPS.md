# TAU CORE — Mivel kell folytatni?

## 1. Rövid távú, konkrét mérési folytatás

### 1.1 DESI DR1 LRG/ELG/QSO futás saját gépen

A sandboxban a DESI DNS nem volt elérhető, ezért ezt saját gépen kell futtatni:

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir tau_web_run/data/desi \
  --download \
  --prepare-csv \
  --max-rows 200000
```

Első próba után full-run `--max-rows` nélkül.

### 1.2 Lensing readout

Első praktikus választás:

- Planck CMB-lensing HEALPix kappa map,
- vagy nyilvános Euclid/Rubin/egyéb kappa proxy.

A pipeline-ban:

```bash
python tc_lensing_connector.py \
  --mode healpix-kappa \
  --input kappa_map.fits \
  --out lensing_reduced.csv \
  --redshift-proxy 2.0
```

### 1.3 Full v3 pipeline

```bash
./run_tau_web_desi_v3.sh
```

---

## 2. Tudományos kontrollok

1. Official survey randoms.
2. Official mocks.
3. Lens/mass-map covariance.
4. Blind galaxy-to-lensing axis test.
5. Redshift stability.
6. Third readout: velocity vagy CMB-lensing/ISW.

---

## 3. Elméleti blokkolók

### B1 — \(U_g\) matematikai bizonyítása

Bizonyítani kell, hogy a Tau-Laplacian spektrális readoutja sima Lorentz-geometriát ad.

### B2 — GR-határ

A spektrális akcióból formálisan ki kell vezetni az Einstein-Hilbert tagot.

### B3 — Anyag-readout

Meg kell mutatni, hogy a closure-stabil maradék standard mezőket ad.

### B4 — Kvantum-határ

A frissített Tau Core státusz szerint a kvantumhatár nem általános
closure-állításként kezelendő.  Finite toy szinten a megfelelő source-oldali
út:

\[
Q\text{-PHASE-TRACE-SKELETON}_\tau(d)
\Rightarrow
Q\text{-COMPLEX-SEED-SOURCE}_\tau(d)
\Rightarrow
\text{finite Hilbert/Born toy packet}.
\]

Ehhez endpoint-blind source adatok kellenek: védett primitív frame, lapos
ciklikus fázistorzor, reverzibilis rank-2 kontrasztmozgások, invariáns
trace/effektus párosítás és közös null policy.  A teljes Hilbert-tér,
no-signalling, collapse, QFT és tensor product egyértelműség továbbra is nyitott.

### B5 — Gauge és Standard Modell

Ki kell hozni belülről:

\[
U(1)\times SU(2)\times SU(3),
\]

a reprezentációkat, anomáliamentességet és három generációt.

### B6 — Numerikus predikció

A \(\Delta^\tau_{ab}\)-nak számolható, előre rögzített predikciókat kell adnia, nem utólagos illesztést.

---

## 4. Legjobb következő projekt

\[
\boxed{
\text{DESI DR1 LRG}
+
\text{Planck CMB-lensing kappa}
}
\]

első cross-readout próbának.

Ez nem végleges bizonyítás, de gyorsan megmondja, hogy van-e bármi iránykoherens jel, amit érdemes mélyebben vizsgálni.

---

## 5. Publikálható állapot feltétele

Csak akkor érdemes paper/preprint irányba menni, ha:

1. valós DESI futás sikeres,
2. lensing cross-readout vakon átmegy,
3. mock covariance ritkaságot mutat,
4. systematics nem dominál,
5. z-stabilitás megvan,
6. legalább egy független extra readout megerősít.

Addig a helyes státusz:

\[
\boxed{
\text{formal research framework + runnable pipeline scaffold}.
}
\]
