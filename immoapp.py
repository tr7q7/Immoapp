import streamlit as st
import time

# --- Configuration de la page ---
st.set_page_config(page_title="CF-Testing-b0", page_icon="💼", layout="centered")

# --- Style CSS personnalisé ---
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-size: 120% !important;
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
revenu_foncier = loyer_annuel - taxe_fonciere - assurance_annuelle
amortissement_bien = prix_bien / 20
amortissement_travaux = travaux / 25
revenu_imposable = revenu_foncier - interets_annuels[0] - amortissement_bien - amortissement_travaux

taux_imposition = 0.15 if montage == "SCI" else 0.582
impot = max(revenu_imposable * taux_imposition, 0)
credit_annuel = mensualite * 12
resultat_net_annuel = revenu_foncier - impot - credit_annuel
cashflow_mensuel = resultat_net_annuel / 12
rendement_annuel = resultat_net_annuel / montant_emprunte

# --- Calcul et affichage ---
if st.button("🔍 Calculer"):
    with st.spinner("Calcul en cours..."):
        time.sleep(1.5)

    result = {
        "cashflow": cashflow_mensuel,
        "rendement": rendement_annuel,
        "impot": impot,
        "revenu_imposable": revenu_imposable,
        "revenu_foncier": revenu_foncier,
        "credit": credit_annuel,
        "interet": interets_annuels[0],
        "capital": amortissements_annuels[0],
        "mensualite": mensualite,
        "montage": montage
    }

    st.session_state.history.insert(0, result)
    st.session_state.history = st.session_state.history[:3]

    st.success("✅ Analyse enregistrée")

# --- Affichage des 3 derniers calculs ---
for i, res in enumerate(st.session_state.history):
    nom = f"CF{i+1}"
    couleur_cf = "green" if res["cashflow"] > 0 else "red"
    couleur_rdt = "gray" if res["rendement"] < 0.03 else "green" if res["rendement"] < 0.05 else "purple"

    expanded = True if i == 0 else False
    with st.expander(f"📂 {nom} - Résumé", expanded=expanded):
        st.markdown(f"<span style='color:{couleur_cf}; font-size: 1.5em;'>💶 Cashflow mensuel : {res['cashflow']:,.0f} €</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{couleur_rdt}; font-size: 1.2em;'>📈 Rendement annuel : {res['rendement'] * 100:.2f} %</span>", unsafe_allow_html=True)

        with st.expander("🔎 Voir détails"):
            st.write(f"**Montage :** {res['montage']}")
            st.write(f"**Mensualité :** {res['mensualite']:,.0f} €")
            st.write(f"**Intérêts (année 1) :** {res['interet']:,.0f} €")
            st.write(f"**Capital remboursé (année 1) :** {res['capital']:,.0f} €")
            st.write(f"**Revenu foncier :** {res['revenu_foncier']:,.0f} €")
            st.write(f"**Revenu imposable :** {res['revenu_imposable']:,.0f} €")
            st.write(f"**Impôt estimé :** {res['impot']:,.0f} €")
            st.write(f"**Résultat net annuel :** {res['revenu_foncier'] - res['impot'] - res['credit']:,.0f} €")
