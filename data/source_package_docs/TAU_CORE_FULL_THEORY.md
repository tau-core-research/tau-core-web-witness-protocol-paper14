# Tau Core teljes elméleti csomag — TC-FULL-THEORY-001

**Állapot:** kutatási váz / formalizált hipotézisrendszer  
**Fontos határ:** ez nem bizonyított fizikai elmélet, hanem egy következetesen felépített, falszifikálható keret, amelyből konkrét megfigyelési pipeline is készült.

---

# 0. Vezető gondolat

A Tau Core alapállítása:

\[
\boxed{
\text{a téridő, anyag, kvantumállapot, gauge-szimmetria és kozmikus háló ugyanazon mélyebb morfológiai Tau-struktúra különböző readoutjai.}
}
\]

A fizika nem közvetlenül az alap Tau-állapotból származik, hanem annak **closure-stabil readoutjaiból**.

A központi objektum:

\[
\mathcal T=(V,E,w,\mu,\Sigma,C_\tau,\prec)
\]

ahol:

- \(V\): Tau-csomópontok,
- \(E\): morfológiai kapcsolatok,
- \(w_{ij}\): él-/kapcsolatsúly,
- \(\mu_i\): lokális súly / morfológiai térfogat,
- \(\Sigma\): lokális szabályrendszer,
- \(C_\tau\): closure-operátor,
- \(\prec\): belső morfológiai rendezés.

A 4D megfigyelő nem \(\mathcal T\)-t látja, hanem readoutokat:

\[
U_g(\mathcal T)=(M_4,g_{ab}),
\]

\[
U_m(\mathcal T)=T_{ab},
\]

\[
U_q(\mathcal T)=|\psi\rangle,
\]

\[
U_{\rm gauge}(\mathcal T)=U(1)\times SU(2)\times SU(3),
\]

\[
U_{\rm web}(\mathcal T)=\mathcal W_{ab}.
\]

---

# 1. Axiomatikus mag

## Axiom A1 — Morfológiai elsődlegesség

Nem a tér, idő vagy anyag az elsődleges, hanem egy absztrakt morfológiai struktúra:

\[
\mathcal T=(V,E,w,\mu,\Sigma,C_\tau,\prec).
\]

A tér, idő, anyag, részecske és mező csak későbbi readout.

---

## Axiom A2 — Projekció / readout

Létezik readout-család:

\[
U_\alpha:\mathcal T\rightarrow\mathcal O_\alpha.
\]

Példák:

\[
U_g:\mathcal T\rightarrow(M_4,g_{ab}),
\]

\[
U_m:\mathcal T\rightarrow T_{ab},
\]

\[
U_q:\mathcal T\rightarrow|\psi\rangle,
\]

\[
U_f:\mathcal T\rightarrow \text{kozmikus filamentháló}.
\]

---

## Axiom A3 — Closure

A fizikai állapot nem nyers Tau-állapot, hanem closure-stabil állapot:

\[
C_\tau(q)\approx q.
\]

Egy objektum, részecske, galaxis, filament vagy háttérgeometria csak akkor jelenik meg stabil 4D objektumként, ha mögötte closure-stabil Tau-részállapot áll.

---

## Axiom A4 — Konzisztencia

Létezik konzisztenciafunkcionál:

\[
D_\tau(q)\ge 0,
\]

ahol:

\[
D_\tau(q)=0
\]

a teljes önkonzisztencia.

A closure definíciója:

\[
\boxed{
C_\tau(q)=
\arg\min_{q'\supseteq q}
\left[
D_\tau(q')+\alpha\,\mathrm{Cost}(q'\setminus q)
\right].
}
\]

Ez azt mondja: a closure a **legkisebb önkonzisztens bővítés**.

---

## Axiom A5 — Readout-invariancia

A fizikai tartalom nem függhet önkényes readout-választástól. Ha két readout ugyanazt a closure-stabil struktúrát méri, akkor kompatibilis invariánsokat kell adniuk.

A Tau-anomáliák ott jelennek meg, ahol ez csak közelítően igaz:

\[
UC_\tau-C_{4D}U\neq0.
\]

---

# 2. Tau-closure részletesen

Egy lokális Tau-állapot:

\[
q=(V_q,E_q,s_q).
\]

A defektus:

\[
D_\tau(q)=
D_{\rm local}(q)
+
D_{\rm edge}(q)
+
D_{\rm scale}(q)
+
D_{\rm order}(q).
\]

A closure:

\[
C_\tau(q)=
\arg\min_{q'\supseteq q}
\left[
D_\tau(q')+\alpha\,\mathrm{Cost}(q'\setminus q)
\right].
\]

Tulajdonságok ideális esetben:

\[
q\subseteq C_\tau(q)
\quad\text{extenzivitás},
\]

\[
C_\tau(C_\tau(q))=C_\tau(q)
\quad\text{idempotencia},
\]

\[
q_1\subseteq q_2
\Rightarrow
C_\tau(q_1)\subseteq C_\tau(q_2)
\quad\text{monotonitás}.
\]

A closure-mélység:

\[
q_{n+1}=C_\tau(q_n),
\]

\[
\ell_C(q)=
\min\{n:\|q_{n+1}-q_n\|<\epsilon_C\}.
\]

A 4D idő egyik jelöltje:

\[
t(q)=U_t(q)\sim \ell_t\ell_C(q)+\eta_t(q).
\]

Így az idő:

\[
\boxed{
\text{idő}=\text{closure-mélység readoutja}.
}
\]

---

# 3. Tau-dinamika idő nélkül

A Tau-ban nincs alap fizikai idő, ezért nem:

\[
\frac{dq}{dt}=F(q).
\]

Hanem:

\[
q\rightarrow C_\tau(q)
\]

és a teljes dinamikai elv:

\[
\boxed{
\delta\mathcal S_\tau[q]=0.
}
\]

Tau-akció:

\[
\mathcal S_\tau[q]=
D_\tau[q]
+
\alpha K_\tau[q]
+
\beta B_\tau[q].
\]

ahol:

- \(D_\tau\): closure-defektus,
- \(K_\tau\): morfológiai komplexitás,
- \(B_\tau\): peremilleszkedési tag.

A klasszikus világvonal Tau-ban egy closure-kompatibilis lánc:

\[
q_0\prec q_1\prec q_2\prec\dots
\]

amelynek 4D readoutja:

\[
x_n^\mu=U_g(q_n).
\]

Ha sima határ létezik:

\[
x_n^\mu\rightarrow x^\mu(t).
\]

A geodetikus:

\[
\boxed{
\text{4D geodetikus}=
\text{Tau-akció stacionárius closure-láncának readoutja}.
}
\]

---

# 4. Geometriai readout \(U_g\)

A cél:

\[
U_g:\mathcal T\rightarrow(M_4,g_{ab}).
\]

A Tau-Laplacian:

\[
(\Delta_\tau f)_i=
\frac1{\mu_i}
\sum_{j\sim i}
w_{ij}(f_j-f_i).
\]

Sajátmódusok:

\[
\Delta_\tau\phi_a=-\lambda_a\phi_a.
\]

A hőmag:

\[
K_s=e^{s\Delta_\tau}.
\]

Spektrális dimenzió:

\[
d_s(s)=
-2\frac{d\log\mathrm{Tr}(K_s)}{d\log s}.
\]

4D readout feltétel:

\[
d_s(s_\star)\approx4.
\]

Koordináta-readout:

\[
X^a(i)=
\ell_\tau e^{-s_\star\lambda_a}\phi_a(i),
\quad a=1,\dots,4.
\]

Effektív hordozó:

\[
M_4=\overline{\{X(i)\mid i\in V\}}.
\]

Lokális energiaforma:

\[
\Gamma_\tau(f,g)(i)=
\frac1{2\mu_i}
\sum_{j\sim i}
w_{ij}(f_j-f_i)(g_j-g_i).
\]

Metrika-jelölt:

\[
G^{ab}(i)=\Gamma_\tau(X^a,X^b)(i),
\]

\[
h_{ab}=(G^{-1})_{ab}.
\]

Lorentz-időirány closure-rendezésből:

\[
\tau(i)=\ell_tT_\tau(i),
\]

\[
n_a=
\frac{\partial_a\tau}
{\sqrt{h^{bc}\partial_b\tau\partial_c\tau}}.
\]

Lorentz-metrika:

\[
\boxed{
g_{ab}=h_{ab}-2n_an_b.
}
\]

Tehát:

\[
\boxed{
U_g(\mathcal T)=
\left(
\overline{\{X(i)\}},
g_{ab}=h_{ab}-2n_an_b
\right).
}
\]

---

# 5. Anyag-readout \(U_m\)

Az anyag nem alapobjektum, hanem closure-stabil geometriai maradék.

A Tau-Hilbert-szerű módustér:

\[
\mathcal H_\tau=
\mathcal H_g\oplus\mathcal H_m.
\]

A geometriai módusok:

\[
\mathcal H_g=\text{alacsony, sima spektrális módusok}.
\]

Az anyagi módusok:

\[
\mathcal H_m=\mathcal H_\tau\ominus\mathcal H_g.
\]

Lokális állapot:

\[
q_i=q_i^{(g)}+q_i^{(m)}.
\]

Anyagsűrűség:

\[
\rho_\tau(i)=\|q_i^{(m)}\|^2.
\]

Stabil anyagfeltétel:

\[
\|C_\tau(q_i^{(m)})-q_i^{(m)}\|<\epsilon_m.
\]

Anyagáram:

\[
J^a(i)=
\frac1{\mu_i}
\sum_{j\sim i}
w_{ij}\rho_\tau(j)\xi_{ij}^a,
\]

ahol:

\[
\xi_{ij}^a=X^a(j)-X^a(i).
\]

Effektív négyessebesség:

\[
u^a=
\frac{J^a}
{\sqrt{-g_{bc}J^bJ^c}}.
\]

Stressz-energia tenzor:

\[
\boxed{
T_{ab}
=
A_\tau
\left[
\rho_\tau u_a u_b
+
P_\tau h^\perp_{ab}
+
\Pi^\tau_{ab}
\right].
}
\]

ahol:

\[
h^\perp_{ab}=g_{ab}+u_au_b.
\]

Az anizotropikus stressz:

\[
\Pi^\tau_{ab}=M_{\langle ab\rangle}.
\]

Ez lesz kulcsfontosságú a kozmikus webnél.

---

# 6. Tau-maradék \(\Delta^\tau_{ab}\)

A master-egyenlet:

\[
G_{ab}+\Lambda_\tau g_{ab}
=
8\pi G_\tau T_{ab}
+
\Delta^\tau_{ab}.
\]

A maradék nem szabad illesztési tag, hanem closure-readout kommutátor:

\[
\boxed{
\Delta^\tau_{ab}
=
\mathcal P_{ab}
\left[
UC_\tau-C_{4D}U
\right].
}
\]

Geometriai és anyagi kommutátor:

\[
\mathfrak D_g=U_gC_\tau-C_{4D}U_g,
\]

\[
\mathfrak D_m=U_mC_\tau-C_{4D}U_m.
\]

Teljes:

\[
\mathfrak D_\tau=
\mathfrak D_g-\kappa_\tau\mathfrak D_m.
\]

\[
\Delta^\tau_{ab}=\mathcal P_{ab}(\mathfrak D_\tau).
\]

Felbontás:

\[
\Delta^\tau_{ab}
=
\Delta^{\rm web}_{ab}
+
\Delta^{\rm lens}_{ab}
+
\Delta^{\rm back}_{ab}
+
\Delta^{H}_{ab}
+
\Delta^{q}_{ab}
+
\Delta^{\rm obs}_{ab}.
\]

---

# 7. GR-határ

Geometriai Tau-akció:

\[
\mathcal S_{\rm geom}^{\tau}
=
\mathrm{Tr}
F(\Delta_\tau/\Lambda_\tau^2).
\]

Ha a Tau-gráfnak sima 4D hőmag-határa van:

\[
\mathrm{Tr}F(\Delta_\tau/\Lambda_\tau^2)
\sim
c_0\Lambda_\tau^4
\int\sqrt{-g}\,d^4x
+
c_1\Lambda_\tau^2
\int R\sqrt{-g}\,d^4x
+
\cdots.
\]

Azonosítás:

\[
\frac1{16\pi G}=c_1\Lambda_\tau^2.
\]

A kozmológiai tag:

\[
\Lambda_{\rm spec}\sim
-\frac{c_0}{2c_1}\Lambda_\tau^2.
\]

4D akció:

\[
S_{4D}
=
\frac1{16\pi G}
\int(R-2\Lambda)\sqrt{-g}\,d^4x
+
S_m
+
S_{\rm closure}^{4D}
+
S_{\rm boundary}.
\]

Variáció:

\[
G_{ab}+\Lambda g_{ab}
=
8\pi GT_{ab}
+
\Delta^\tau_{ab}.
\]

Klasszikus GR-határ:

\[
UC_\tau\approx C_{4D}U
\Rightarrow
\Delta^\tau_{ab}\rightarrow0.
\]

Így:

\[
\boxed{
G_{ab}+\Lambda g_{ab}=8\pi GT_{ab}.
}
\]

---

# 8. Kvantum-határ

Egy lokális Tau-állapotnak több closure-fixpontja lehet:

\[
q_k^\star=C_\tau^{(k)}(q).
\]

Tau-kvantumállapot:

\[
\Psi_\tau(q)=\{q_k^\star,A_k\}.
\]

Amplitúdó:

\[
A_k=
\frac1{\sqrt Z}
e^{-\frac12\beta D_\tau(q_k^\star)}
e^{i\Theta_\tau(q_k^\star)}.
\]

4D readout:

\[
|\psi\rangle=
\sum_k A_k|k\rangle.
\]

Born-szerű valószínűség:

\[
p_k=|A_k|^2
=
\frac{e^{-\beta D_\tau(q_k^\star)}}
{\sum_l e^{-\beta D_\tau(q_l^\star)}}.
\]

Mérés:

\[
\boxed{
\text{collapse}=
\text{egy closure-ág makroszkopikus stabilizálódása a readoutban}.
}
\]

Összefonódás:

\[
C_\tau(q_A\cup q_B)
\neq
C_\tau(q_A)\cup C_\tau(q_B).
\]

No-signalling feltétel:

\[
P(A|a,b)=P(A|a).
\]

Schrödinger-határ:

\[
\Theta_k(t)-\Theta_k(0)=-E_kt/\hbar,
\]

\[
A_k(t)=A_k(0)e^{-iE_kt/\hbar}.
\]

Általánosan:

\[
i\hbar\partial_t|\psi\rangle=\hat H_\tau|\psi\rangle.
\]

---

# 9. Konstansok

Fizikai konstans:

\[
\boxed{
K_{\rm phys}=
\text{closure-stabil readout-arány}.
}
\]

Fénysebesség:

\[
c_\tau=
\sup_{\gamma_\tau}
\frac{\Delta U_x(\gamma_\tau)}
{\Delta U_t(\gamma_\tau)}.
\]

Planck-állandó:

\[
\Theta_\tau=\frac{S_{4D}}{\hbar},
\]

\[
\hbar=
\frac{S_{4D}}{\Theta_\tau}.
\]

Newton-állandó:

\[
G=
\frac1{16\pi c_1\Lambda_\tau^2}.
\]

Kozmológiai konstans:

\[
\Lambda_{\rm eff}
=
\Lambda_{\rm spec}
+
\Lambda_{\rm closure},
\]

\[
\Lambda_{\rm closure}
=
\chi_\Lambda
\left[
D_\tau^{\rm glob}
-
\langle D_\tau^{\rm loc}\rangle
\right].
\]

Finomszerkezeti állandó:

\[
\alpha_{\rm EM}
=
\frac1{4\pi\mathcal K_{\rm gauge}}.
\]

Tömeg:

\[
m_p\sim\frac{\hbar}{c}\sqrt{\lambda_p}.
\]

---

# 10. Gauge-szimmetriák

Tau-gauge csoport:

\[
\boxed{
\mathcal G_\tau(q)=
\{g\in\mathrm{Aut}_\tau(q)\mid C_\tau(gq)=gC_\tau(q)\}.
}
\]

Lokális gauge-transzformáció:

\[
q_i\mapsto g_iq_i.
\]

Él-transzport:

\[
A_{ij}\in\mathcal G_\tau.
\]

Kovariáns különbség:

\[
D_{ij}\psi=\psi_j-A_{ij}\psi_i.
\]

Gauge-görbület hurok-holonómiából:

\[
F_\ell=A_{ki}A_{jk}A_{ij}.
\]

Gauge-akció:

\[
S_{\rm gauge}^{\tau}
=
\sum_\ell \beta_\ell\mathrm{Tr}(1-F_\ell).
\]

Sima határ:

\[
S_{\rm gauge}^{4D}
=
-\frac1{4g^2}
\int F_{\mu\nu}F^{\mu\nu}\sqrt{-g}\,d^4x.
\]

Standard modell gauge-csoport jelölt:

\[
\mathcal G_\tau^{\rm stable}
\approx
U(1)_Y\times SU(2)_L\times SU(3)_C.
\]

---

# 11. Standard Modell readout

Részecske:

\[
\boxed{
\text{részecske}=
\text{closure-stabil belső Tau-módus adott gauge-reprezentációban}.
}
\]

Belső szál:

\[
\mathcal F_x=
\mathcal F_{\rm phase}
\oplus
\mathcal F_{\rm weak}
\oplus
\mathcal F_{\rm color}
\oplus
\mathcal F_{\rm gen}
\oplus
\mathcal F_{\rm mass}.
\]

Fermion reprezentációs csomag:

\[
q_p\mapsto
[
\rho_{U(1)},
\rho_{SU(2)},
\rho_{SU(3)},
\chi,
g
].
\]

Chirális aszimmetria:

\[
C_\tau(\mathcal F_L)
\sim
\mathcal F_L^{(1)}\oplus\mathcal F_L^{(2)}
\Rightarrow
SU(2)_L.
\]

Jobb szektor:

\[
C_\tau(\mathcal F_R)\sim\mathcal F_R
\Rightarrow
SU(2)\text{-szinglet}.
\]

Higgs:

\[
\boxed{
\text{Higgs}=
\text{belső closure-orientáció}.
}
\]

Törés:

\[
SU(2)_L\times U(1)_Y
\rightarrow
U(1)_{\rm EM}.
\]

Gauge-bozon tömeg:

\[
m_A^2\sim\|T_Ah_\tau\|^2_{\rm closure}.
\]

Foton:

\[
Q_{\rm EM}h_\tau=0
\Rightarrow
m_\gamma=0.
\]

Konfinement:

\[
C_\tau(q_{\rm color})\neq q_{\rm color},
\]

de:

\[
C_\tau(q_{\rm singlet})\approx q_{\rm singlet}.
\]

---

# 12. Hipertöltések

Elektromos töltés:

\[
Q=T_3+\frac Y2.
\]

Higgs semlegesség:

\[
Q(H^0)=0
\Rightarrow
Y(H)=1.
\]

Yukawa closure-kompatibilitás:

\[
Y(u_R)=Y(Q_L)+1,
\]

\[
Y(d_R)=Y(Q_L)-1,
\]

\[
Y(e_R)=Y(L_L)-1.
\]

Anomáliamentesség:

\[
3Y(Q_L)+Y(L_L)=0.
\]

Neutrino semlegesség:

\[
Q(\nu_L)=0
\Rightarrow
Y(L_L)=-1.
\]

Így:

\[
Y(Q_L)=\frac13,
\]

\[
Y(u_R)=\frac43,
\]

\[
Y(d_R)=-\frac23,
\]

\[
Y(e_R)=-2.
\]

Elektromos töltések:

\[
Q(u)=\frac23,
\quad
Q(d)=-\frac13,
\quad
Q(e)=-1,
\quad
Q(\nu)=0.
\]

---

# 13. Három generáció

Generáció:

\[
\boxed{
\text{generáció}=
\text{ugyanazon fermion closure-módus belső spektrális állapota}.
}
\]

Generációs operátor:

\[
\Delta_{\rm gen}\psi_n=-\lambda_n^{\rm gen}\psi_n.
\]

Fizikai generáció:

\[
C_\tau(\psi_n)\approx\psi_n,
\quad
\lambda_n^{\rm gen}<\lambda_{\rm cutoff}.
\]

Erősebb topológiai modell:

\[
N_{\rm gen}
=
\mathrm{Index}(\mathcal D_{\rm gen})=3.
\]

Tömeghierarchia:

\[
m_{f,g}
=
v_\tau
|\langle L_{f,g}|\mathcal Y_\tau(h_\tau)|R_{f,g}\rangle|.
\]

CKM:

\[
V_{ij}^{\rm CKM}=
\langle\psi_i^u|\psi_j^d\rangle_\tau.
\]

PMNS:

\[
U_{ij}^{\rm PMNS}=
\langle\psi_i^\nu|\psi_j^e\rangle_\tau.
\]

CP-sértés:

\[
\arg V_{ij}
=
\text{generációs closure-holonómia}.
\]

---

# 14. Kozmológiai master-modell

Master-egyenlet:

\[
G_{ab}+\Lambda_\tau g_{ab}
=
8\pi G_\tau
(T_{ab}^{\rm lum}+T_{ab}^{\rm hidden})
+
\Delta^\tau_{ab}.
\]

Sötét anyag:

\[
T_{ab}^{\rm hidden}
=
T_{ab}^{\rm grav}
-
T_{ab}^{\rm lum}.
\]

Sötét energia:

\[
\Lambda_\tau
=
\Lambda_{\rm spec}
+
\Lambda_{\rm closure}.
\]

Hubble-feszültség:

\[
\Delta H_0=
U_H(C_\tau^{\rm loc})
-
U_H(C_\tau^{\rm glob}).
\]

Backreaction:

\[
\Delta^{\rm back}_{ab}
=
\mathcal P_{ab}
[
U_gC_\tau^{\rm glob}
-
\langle U_gC_\tau^{\rm loc}\rangle
].
\]

FLRW limit:

\[
\Delta^\tau_{ab}\rightarrow0
\Rightarrow
\Lambda{\rm CDM}.
\]

---

# 15. Kozmikus web tenzor

Párok:

\[
\xi_{ij}^a=X_j^a-X_i^a,
\]

\[
\hat\xi_{ij}^a=\frac{\xi_{ij}^a}{r_{ij}}.
\]

Web-tenzor:

\[
\boxed{
\mathcal W_{ab}(R)
=
\mathcal N_R^{-1}
\sum_{i<j}
w_iw_jK_R(r_{ij})
\left(
\hat\xi_{ij,a}\hat\xi_{ij,b}
-
\frac13h_{ab}
\right).
}
\]

Tulajdonság:

\[
\mathcal W_{ab}=\mathcal W_{ba},
\quad
h^{ab}\mathcal W_{ab}=0.
\]

Tau-kapcsolat:

\[
\mathcal W_{ab}^{\tau}
=
U_{\rm web}(\Pi^\tau_{ab}).
\]

Tisztított jel:

\[
\widehat{\mathcal W}_{ab}^{\tau}
=
\mathcal W_{ab}^{\rm obs}
-
\langle\mathcal W_{ab}^{\Lambda{\rm CDM}}\rangle
-
\mathcal W_{ab}^{\rm sys}.
\]

Tau-web komponens:

\[
\Delta^{\rm web}_{ab}
=
\chi_{\rm web}\widehat{\mathcal W}_{ab}^{\tau}.
\]

Fő predikció:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}.
}
\]

Strong witness:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\parallel
\mathcal W^{\rm extra}_{ab}.
}
\]

---

# 16. Megfigyelési pipeline

A teljes pipeline:

1. DESI/LSS adat:
   \[
   D_{\rm gal}\rightarrow\mathcal W^{\rm gal}_{ab}.
   \]

2. Lensing/kappa adat:
   \[
   D_{\rm lens}\rightarrow\mathcal W^{\rm lens}_{ab}.
   \]

3. Systematics projector:
   \[
   \mathcal W^{\rm clean}=(I-\Pi_{\rm sys})\mathcal W^{\rm obs}.
   \]

4. Cross-readout:
   \[
   C_{\rm gal-lens}
   =
   \frac{
   \mathcal W^{\rm gal}_{ab}\mathcal W_{\rm lens}^{ab}
   }
   {
   \|\mathcal W^{\rm gal}\|\|\mathcal W^{\rm lens}\|
   }.
   \]

5. Redshift stability:
   \[
   S_z=
   \left\langle
   \frac{\mathcal W(z_i)\cdot\mathcal W(z_j)}
   {\|\mathcal W(z_i)\|\|\mathcal W(z_j)\|}
   \right\rangle.
   \]

6. Weighted stability:
   \[
   S_{z,w}=
   \frac{\sum_{i<j}(A_iA_j)^pC_{ij}}
   {\sum_{i<j}(A_iA_j)^p}.
   \]

7. Mock covariance:
   \[
   \chi^2_{\rm obs}=
   (v_{\rm obs}-\bar v)^TC^{-1}(v_{\rm obs}-\bar v).
   \]

8. Extra readout:
   \[
   \mathcal V_{ab}\parallel\mathcal W^{\rm gal}_{ab}
   \quad\text{or}\quad
   \mathcal W^{\rm CMB}_{ab}\parallel\mathcal W^{\rm gal}_{ab}.
   \]

9. Verdict ladder:
   - NULL
   - WEAK-ANOMALY-GALAXY-ONLY
   - TAU-COMPATIBLE-CANDIDATE
   - TAU-COMPATIBLE-WEIGHTED-Z-CANDIDATE
   - TAU-COMPATIBLE
   - STRONG-WITNESS-CANDIDATE
   - SYSTEMATICS-DOMINATED

---

# 17. Mit sikerült ténylegesen futtatni?

A sandboxban a valós DESI letöltés nem tudott lefutni DNS/internet hiba miatt:

\[
\texttt{Temporary failure in name resolution}.
\]

Viszont a teljes pipeline szintetikus adatokon lefutott:

- két-readout stabil demo:
  \[
  \text{TAU-COMPATIBLE}
  \]
- három-readout stabil demo:
  \[
  \text{STRONG-WITNESS-CANDIDATE}.
  \]
- zajos z-stabilitás demo:
  \[
  \text{TAU-COMPATIBLE-CANDIDATE}.
  \]

Ez azt bizonyítja, hogy az elemzési architektúra működik, de nem bizonyítja a valós fizikai állítást.

---

# 18. Mivel kell folytatni?

## 18.1 Valós DESI futás saját gépen

Első lépés:

```bash
python tc_desi_connector.py \
  --tracer LRG \
  --region NGC \
  --random-indices 0 \
  --out-dir tau_web_run/data/desi \
  --plan
```

Majd kis első futás:

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

Utána full-run sorlimit nélkül.

---

## 18.2 Lensing adat kiválasztása

Kell egy valódi második readout:

- Planck CMB-lensing kappa map,
- Euclid Q1 / későbbi DR1 lensing proxy,
- Rubin/LSST későbbi weak-lensing,
- egy nyilvános kappa/mass-map katalógus.

A jelenlegi pipeline tud:

- kappa table,
- flat-sky shear proxy,
- HEALPix kappa map.

---

## 18.3 Hivatalos mockok

A mock covariance csak akkor lesz értelmes, ha sok hivatalos mock fut:

\[
N_{\rm mock}\ge 100
\]

exploratív szinten, és inkább:

\[
N_{\rm mock}\ge 500
\]

komolyabb kovarianciához.

---

## 18.4 Vak lensing teszt

A galaxy web-tenzort előre le kell zárni:

\[
\mathcal W^{\rm gal}_{ab}\ \text{frozen}.
\]

Utána egyszer kell mérni a lensing-alignmentet.

Nem szabad utólag tengelyt vagy skálát keresgélni.

---

## 18.5 Harmadik readout

Strong witnesshez kell legalább egy:

- peculiar velocity katalógus,
- CMB-lensing / ISW tensor,
- független lensing survey,
- független galaxy tracer.

---

## 18.6 Elméleti blokkolók

A valódi elméleti áttöréshez bizonyítani kell:

1. \(U_g\) tényleg sima Lorentz-geometriát ad bizonyos Tau-gráfosztályokra.
2. A spektrális akció határa tényleg Einstein-Hilbert.
3. \(U_m\) standard mezőket/részecskéket ad.
4. A gauge-stabil automorfizmusok tényleg \(U(1)\times SU(2)\times SU(3)\)-at adnak.
5. \(\mathrm{Index}(\mathcal D_{\rm gen})=3\) nem kézzel betett.
6. A Born-szabály és no-signalling valóban kijön a closure-ágakból.
7. A \(\Delta^\tau_{ab}\) numerikusan prediktív, nem illeszthető szemetesláda.

---

## 18.7 Legközelebbi konkrét lépés

A legpraktikusabb következő lépés:

\[
\boxed{
\text{Planck CMB-lensing HEALPix map}
+
\text{DESI LRG DR1}
}
\]

első durva cross-readout tesztként.

A Planck kappa map adhat egy harmadik jellegű tömeg-readoutot. Nem tökéletes, mert broad light-cone kernel, de jó első kontroll.

A második lépés:

\[
\boxed{
\text{Euclid / Rubin weak-lensing mass map}
}
\]

ha megfelelő nyilvános, kalibrált adat elérhető.

---

# 19. Rövid végső összefoglaló

A Tau Core jelenlegi állapota:

\[
\boxed{
\text{formalizált, falszifikálható kutatási keret}
}
\]

nem bizonyított elmélet.

A legerősebb kész predikciós ág:

\[
\boxed{
\mathcal W^{\rm clean,gal}_{ab}
\parallel
\mathcal W^{\rm clean,lens}_{ab}
\parallel
\mathcal W^{\rm extra}_{ab}.
}
\]

A pipeline ezt már tudja mérni.

A következő feladat:

\[
\boxed{
\text{valós survey adatokon, vak protokollal, mock kovarianciával futtatni.}
}
\]
