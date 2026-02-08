import streamlit as st
import matplotlib.pyplot as plt

# --- Configuration de la page ---
st.set_page_config(page_title="CF-Testing-b0", page_icon="💼", layout="centered")

# --- Style CSS personnalisé ---
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-size: 110% !important;
            color: white !important;
        }
        h1 {
            font-size: 2em !important;
        }
        .stSlider > div > div {
            color: white !important;
        }
        .stSlider > div > div > div[role="slider"] {
            background-color: orange !important;
            border: 1px solid white;
            height: 150px !important;
            width: 150px !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("CF-Testing-b0")

# --- Stockage des calculs précédents ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Table frais de notaire (bien ancien, estimations) + interpolation ---
NOTAIRE_TABLE = [
    (10_000, 1_100),
    (20_000, 1_900),
    (30_000, 2_700),
    (40_000, 3_400),
    (50_000, 3_900),
    (60_000, 4_500),
    (70_000, 5_100),
    (80_000, 5_700),
    (90_000, 6_200),
    (100_000, 6_700),
    (120_000, 7_900),
    (150_000, 9_700),
    (200_000, 12_900),
    (250_000, 16_000),
    (300_000, 19_100),
    (350_000, 22_300),
    (400_000, 25_400),
    (450_000, 28_600),
    (500_000, 31_800),
]

def frais_notaire_estime(prix: float) -> float:
    table = NOTAIRE_TABLE
    if prix <= table[0][0]:
        return float(table[0][1])
    if prix >= table[-1][0]:
        return float(table[-1][1])

    for (p0, f0), (p1, f1) in zip(table[:-1], table[1:]):
        if p0 <= prix <= p1:
            t = (prix - p0) / (p1 - p0)
            return float(f0 + t * (f1 - f0))
    return float(prix * 0.07)

# --- Estimation grossière CFE (LMNP) en fonction du prix ---
def estimer_cfe_lmnp(prix_bien: float) -> int:
    if prix_bien <= 90_000:
        return 250  # studio / petit T2
    elif prix_bien <= 180_000:
        return 300  # T2/T3
    else:
        return 400  # plus grand / plus cher

# --- Entrée utilisateur ---
st.markdown("#### 🔕 Informations générales")

prix_bien = st.slider("Prix du bien", 30000, 350000, step=5000, value=150000, format="€%d")
travaux = st.slider("Estimation des travaux", 0, 150000, step=2000, value=20000, format="€%d")
loyer = st.slider("Loyer mensuel estimé", 300, 3500, step=50, value=700, format="€%d")

taxe_fonciere = st.slider("Taxe foncière annuelle", 500, 3000, step=50, value=800, format="€%d")
charges_copro = st.slider("Charges de copropriété mensuelles", 10, 400, step=10, value=100, format="€%d")
assurance = st.slider("Assurance mensuelle", 0, 100, step=5, value=20, format="€%d")

taux_credit = st.slider("Taux du crédit", 0.0, 6.0, step=0.1, value=1.5, format="%.2f %%")
duree_credit_ans = st.slider("Durée du crédit", 10, 30, step=1, value=20, format="%d ans")

st.markdown("#### ⚙️ Choix du montage fiscal")
montage = st.radio("Montage", ["Nom Propre (LMNP)", "SCI", "Nom Propre (Nue)"], horizontal=True)

# Param fiscal simplifié pour "Nue"
tmi = st.slider("TMI (IR) - utilisé pour 'Nue'", 0, 45, step=1, value=30, format="%d %%") / 100
ps = 0.172  # prélèvements sociaux

def calculer_interet_annee1(capital: float, taux_mensuel: float, mensualite: float) -> float:
    solde = capital
    interet_total = 0.0
    for _ in range(12):
        interet = solde * taux_mensuel
        amort = mensualite - interet
        solde -= amort
        interet_total += interet
    return interet_total

def calculer_resultats(montage):
    duree_credit_mois = duree_credit_ans * 12
    taux_mensuel = taux_credit / 100 / 12

    frais_notaire = frais_notaire_estime(prix_bien)
    frais_dossier = 1400
    montant_emprunte = prix_bien + frais_notaire + frais_dossier + travaux

    if taux_mensuel > 0:
        mensualite = montant_emprunte * (taux_mensuel / (1 - (1 + taux_mensuel) ** -duree_credit_mois))
    else:
        mensualite = montant_emprunte / duree_credit_mois

    interet_annuel_annee1 = calculer_interet_annee1(montant_emprunte, taux_mensuel, mensualite)

    loyer_annuel = loyer * 12
    assurance_annuelle = assurance * 12
    charges_copro_annuelles = charges_copro * 12

    cfe_annuelle_calc = estimer_cfe_lmnp(prix_bien) if montage == "Nom Propre (LMNP)" else 0

    charges_exploitation = taxe_fonciere + assurance_annuelle + charges_copro_annuelles + cfe_annuelle_calc
    resultat_exploitation = loyer_annuel - charges_exploitation  # net avant crédit/impôt

    # ✅ Rendement net (hors crédit / hors impôt) : net d'exploitation / prix d'achat
    # On prend le prix du bien seul (classique). Si tu veux sur "coût total" => change le dénominateur.
    rendement_net = (resultat_exploitation / prix_bien) * 100 if prix_bien > 0 else 0

    # Amortissements (LMNP réel, simplifié)
    amortissement_bien = prix_bien / 30
    amortissement_travaux = travaux / 10 if travaux > 0 else 0

    credit_annuel = mensualite * 12

    if montage == "Nom Propre (LMNP)":
        resultat_fiscal = resultat_exploitation - interet_annuel_annee1 - amortissement_bien - amortissement_travaux
        impot = 0 if resultat_fiscal <= 0 else resultat_fiscal * ps
    elif montage == "SCI":
        resultat_imposable = resultat_exploitation - interet_annuel_annee1 - amortissement_bien - amortissement_travaux
        impot = max(resultat_imposable * 0.15, 0)
    else:  # Nue
        resultat_imposable = resultat_exploitation - interet_annuel_annee1
        impot = max(resultat_imposable * (tmi + ps), 0)

    resultat_net_apres = resultat_exploitation - credit_annuel - impot
    cashflow = resultat_net_apres / 12
    rendement = (resultat_net_apres / montant_emprunte) * 100

    return {
        "cashflow": round(cashflow, 2),
        "rendement": round(rendement, 2),
        "rendement_net": round(rendement_net, 2),
        "impot": round(impot),
        "taxe_fonciere": taxe_fonciere,
        "assurance": assurance_annuelle,
        "charges_copro": charges_copro_annuelles,
        "cfe": cfe_annuelle_calc,
        "credit": credit_annuel,
        "interet": round(interet_annuel_annee1),
        "frais_notaire": round(frais_notaire),
        "travaux": travaux
    }

if st.button("Calculer"):
    data = calculer_resultats(montage)
    st.session_state.history.insert(0, data)
    st.session_state.history = st.session_state.history[:3]

if st.session_state.history:
    selected = st.radio(
        "Résultats enregistrés :",
        [f"CF{i+1}" for i in range(len(st.session_state.history))],
        index=0,
        horizontal=True
    )
    idx = int(selected[2]) - 1
    data = st.session_state.history[idx]

    couleur_cf = "green" if data["cashflow"] > 0 else "red"
    couleur_rdt = "violet" if data["rendement"] > 5 else ("green" if data["rendement"] > 3 else "gray")

    # ✅ Couleur Rendement Net selon règles demandées
    if data["rendement_net"] > 10:
        couleur_rdt_net = "green"
    elif data["rendement_net"] < 6:
        couleur_rdt_net = "red"
    else:
        couleur_rdt_net = "gray"

    st.markdown(f"### 💶 Cashflow : <span style='color:{couleur_cf}'> {data['cashflow']} €</span>", unsafe_allow_html=True)
    st.markdown(f"### 📈 Rendement Annuel : <span style='color:{couleur_rdt}'> {data['rendement']} %</span>", unsafe_allow_html=True)
    st.markdown(f"### 🧾 Rendement Net : <span style='color:{couleur_rdt_net}'> {data['rendement_net']} %</span>", unsafe_allow_html=True)

    labels = ["Impôt", "Taxe foncière", "Assurance", "Charges copro", "CFE", "Crédit", "Cashflow"]
    values = [
        data["impot"],
        data["taxe_fonciere"],
        data["assurance"],
        data["charges_copro"],
        data["cfe"],
        data["credit"],
        data["cashflow"] * 12
    ]
    colors = ["red", "orange", "gold", "gray", "purple", "dodgerblue", "lime"]
    total = sum(values)

    fig, ax = plt.subplots(figsize=(6, 1.2))
    left = 0
    for v, c in zip(values, colors):
        ax.barh(0, v, left=left, color=c, edgecolor="none")
        left += v
    ax.set_xlim(0, total if total > 0 else 1)
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    ax.axis("off")
    st.pyplot(fig)

    legend_items = [
        f"<span style='color:{colors[i]}'>{labels[i]} : {values[i]:,.0f} € ({(values[i]/total*100):.1f}%)</span>"
        if total > 0 else f"<span style='color:{colors[i]}'>{labels[i]} : {values[i]:,.0f} €</span>"
        for i in range(len(labels))
    ]
    st.markdown(" | ".join(legend_items), unsafe_allow_html=True)

    with st.expander("🔍 Voir détails"):
        st.write(f"Montage : {montage}")
        st.write(f"Impôt : {data['impot']} €")
        st.write(f"Taxe foncière : {data['taxe_fonciere']} €")
        st.write(f"Assurance : {data['assurance']} €")
        st.write(f"Charges copro : {data['charges_copro']} €")
        st.write(f"CFE (estimée) : {data['cfe']} €")
        st.write(f"Crédit : {data['credit']} €")
        st.write(f"Intérêt annuel (année 1) : {data['interet']} €")
        st.write(f"Frais de notaire : {data['frais_notaire']} €")
        st.write(f"Travaux : {data['travaux']} €")
        st.write(f"Cashflow : {data['cashflow']*12:.2f} € / an")
        st.write(f"Rendement Net : {data['rendement_net']:.2f} %")

    with st.expander("📊 Comparer les régimes fiscaux"):
        comparaisons = {m: calculer_resultats(m) for m in ["Nom Propre (LMNP)", "SCI", "Nom Propre (Nue)"]}
        for m, d in comparaisons.items():
            couleur = "green" if d["cashflow"] > 0 else "red"
            st.markdown(
                f"{m} : Cashflow <span style='color:{couleur}'>{d['cashflow']} €/mois</span> — "
                f"Rendement : {d['rendement']:.2f} % — Impôt : {d['impot']} €",
                unsafe_allow_html=True
            )
