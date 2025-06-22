import streamlit as st
import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
            height: 64px !important;
            width: 64px !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("CF-Testing-b0")

# --- Stockage des calculs précédents ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Étape 1 : Entrée utilisateur ---
st.markdown("#### 📅 Informations générales")

prix_bien = st.slider("Prix du bien", 20000, 500000, step=5000, value=150000, format="€%d")
travaux = st.slider("Estimation des travaux", 5000, 200000, step=5000, value=20000, format="€%d")
loyer = st.slider("Loyer mensuel estimé", 200, 5000, step=50, value=700, format="€%d")

st.markdown("#### 🏦 Données financières")

taxe_fonciere = st.slider("Taxe foncière annuelle", 500, 5000, step=50, value=800, format="€%d")
charges_copro = st.slider("Charges de copropriété mensuelles", 10, 400, step=10, value=100, format="€%d")
assurance = st.slider("Assurance mensuelle", 0, 200, step=5, value=20, format="€%d")
taux_credit = st.slider("Taux du crédit", 0.0, 4.0, step=0.1, value=1.5, format="%.2f %%")
duree_credit_ans = st.slider("Durée du crédit", 10, 30, step=1, value=20, format="%d ans")

st.markdown("#### ⚙️ Choix du montage fiscal")
montage = st.radio("Montage", ["Nom Propre", "SCI"], horizontal=True)

if st.button("Calculer"):
    # --- Calculs ---
    duree_credit_mois = duree_credit_ans * 12
    taux_mensuel = taux_credit / 100 / 12
    frais_notaire = prix_bien * 0.08
    frais_dossier = 1400
    montant_emprunte = prix_bien + frais_notaire + frais_dossier + travaux

    if taux_mensuel > 0:
        mensualite = montant_emprunte * (taux_mensuel / (1 - (1 + taux_mensuel) ** -duree_credit_mois))
    else:
        mensualite = montant_emprunte / duree_credit_mois

    # Simulation année 1
    solde = montant_emprunte
    interets_annuels = []
    amortissements_annuels = []

    for _ in range(duree_credit_ans):
        interet_total = 0
        amort_total = 0
        for _ in range(12):
            interet = solde * taux_mensuel
            amort = mensualite - interet
            solde -= amort
            interet_total += interet
            amort_total += amort
        interets_annuels.append(interet_total)
        amortissements_annuels.append(amort_total)

    loyer_annuel = loyer * 12
    assurance_annuelle = assurance * 12
    charges_copro_annuelles = charges_copro * 12
    revenu_foncier = loyer_annuel - taxe_fonciere - assurance_annuelle
    amortissement_bien = prix_bien / 20
    amortissement_travaux = travaux / 25
    revenu_imposable = revenu_foncier - interets_annuels[0] - amortissement_bien - amortissement_travaux

    taux_imposition = 0.582 if montage == "Nom Propre" else 0.15
    impot = max(revenu_imposable * taux_imposition, 0)
    credit_annuel = mensualite * 12
    resultat_net = revenu_foncier - credit_annuel - impot - charges_copro_annuelles
    cashflow = resultat_net / 12
    rendement = (resultat_net / montant_emprunte) * 100

    # --- Sauvegarde historique ---
    st.session_state.history.insert(0, {
        "cashflow": round(cashflow, 2),
        "rendement": round(rendement, 2),
        "impot": round(impot),
        "revenu_foncier": revenu_foncier,
        "taxe_fonciere": taxe_fonciere,
        "assurance": assurance_annuelle,
        "charges_copro": charges_copro_annuelles,
        "credit": credit_annuel
    })
    st.session_state.history = st.session_state.history[:3]  # max 3 entrées

# --- Étape 3 : Affichage Résultat ---
if st.session_state.history:
    selected = st.radio("Résultats enregistrés :", [f"CF{i+1}" for i in range(len(st.session_state.history))], index=0, horizontal=True)
    idx = int(selected[2]) - 1
    data = st.session_state.history[idx]

    couleur_cf = "green" if data["cashflow"] > 0 else "red"
    if data["rendement"] > 5:
        couleur_rdt = "violet"
    elif data["rendement"] > 3:
        couleur_rdt = "green"
    else:
        couleur_rdt = "gray"

    st.markdown(f"### 💶 Cashflow : <span style='color:{couleur_cf}'> {data['cashflow']} €</span>", unsafe_allow_html=True)
    st.markdown(f"### 📈 Rendement Annuel : <span style='color:{couleur_rdt}'> {data['rendement']} %</span>", unsafe_allow_html=True)

    # --- Graphique répartition ---
    labels = ["Impôt", "Taxe foncière", "Assurance", "Charges copro", "Crédit", "Cashflow"]
    values = [
        data["impot"],
        data["taxe_fonciere"],
        data["assurance"],
        data["charges_copro"],
        data["credit"],
        data["cashflow"] * 12
    ]
    colors = ["red", "orange", "gold", "gray", "dodgerblue", "lime"]
    total = sum(values)
    fig, ax = plt.subplots(figsize=(6, 1.2))
    left = 0
    for v, c in zip(values, colors):
        ax.barh(0, v, left=left, color=c, edgecolor="none")
        left += v
    ax.set_xlim(0, total)
    ax.axis("off")
    st.pyplot(fig)

    # Légende
    legend_items = [
        f"<span style='color:{colors[i]}'><b>{labels[i]}</b> : {values[i]:,.0f} € ({(values[i]/total*100):.1f}%)</span>"
        for i in range(len(labels))
    ]
    st.markdown(" | ".join(legend_items), unsafe_allow_html=True)

    # --- Détails ---
    with st.expander("🔍 Voir détails"):
        st.write(f"Impôt : {data['impot']} €")
        st.write(f"Taxe foncière : {data['taxe_fonciere']} €")
        st.write(f"Assurance : {data['assurance']} €")
        st.write(f"Charges copro : {data['charges_copro']} €")
        st.write(f"Crédit : {data['credit']} €")
        st.write(f"Cashflow : {data['cashflow']*12:.2f} € / an")
