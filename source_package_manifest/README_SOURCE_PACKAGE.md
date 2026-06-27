# TAU_CORE_FULL_PACKAGE_001

Ez a csomag a beszélgetésben felépített Tau Core munka teljes, összerendezett változata.

## Fő tartalom

- `docs/TAU_CORE_FULL_THEORY.md`  
  Teljes elméleti levezetés: axiómák, closure, geometriai readout, anyag, GR-határ, kvantum-határ, konstansok, gauge, Standard Modell, hiperszám, generációk, kozmológia, kozmikus web.

- `scripts/`  
  A teljes futtatható Tau-Web pipeline v3 scriptjei.

- `docs/TC-RUNBOOK-003.md`  
  Végigfuttatható DESI + lensing + extra-readout workflow.

- `docs/TC-VALIDATION-AUDIT-001.md`  
  Tudományos guardrail: mikor szabad/nem szabad Tau-kompatibilis állítást tenni.

- `config/TC-PREREG-001.yaml`  
  Előregisztrációs sablon.

- `runs/`  
  A korábbi smoke runok és demo outputok, ahol elérhetők.

## Legfontosabb szabály

\[
\text{galaxy-only filamentarity} \neq \text{Tau-compatible signal}.
\]

Tau-kompatibilis minimum:

\[
\mathcal W^{clean,gal}_{ab}
\parallel
\mathcal W^{clean,lens}_{ab}
\]

plusz z-stabilitás, systematics tisztítás és mock ritkaság.

Strong witness candidate:

\[
\mathcal W^{clean,gal}_{ab}
\parallel
\mathcal W^{clean,lens}_{ab}
\parallel
\mathcal W^{extra}_{ab}.
\]

## Következő lépés

Valós DESI DR1 + Planck/Euclid/Rubin lensing readout futtatás, vak protokollal és hivatalos mockokkal.
