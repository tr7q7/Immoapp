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
            height: 150px !important;
            width: 150px !important;
        }
        input[type=number] {
            font-size: 1em !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("CF-Testing-b0")

# --- Stockage des calculs précédents ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Entrée utilisateur ---
st.markdown("#### 🔕 Informations générales")

def slider_input(label, min_value, max_value, step, default, format_str):
    col1, col2 = st.columns([3, 1])
    with col1:
        slider_val = st.slider(label, min_value, max_value, step=step, value=default, format=format_str, key=f"slider_{label}")
    with col2:
        input_val = st.number_input(" ", min_value=min_value, max_value=max_value, value=slider_val, step=step, label_visibility="collapsed", key=f"input_{label}")
    return input_val

prix_bien = slider_input("Prix du bien", 30000, 350000, 5000, 150000, "€%d")
travaux = slider_input("Estimation des travaux", 0, 150000, 5000, 20000, "€%d")
loyer = slider_input("Loyer mensuel estimé", 300, 3500, 50, 700, "€%d")
taxe_fonciere = slider_input("Taxe foncière annuelle", 500, 3000, 50, 800, "€%d")
charges_copro = slider_input("Charges de copropriété mensuelles", 10, 400, 10, 100, "€%d")
assurance = slider_input("Assurance mensuelle", 0, 100, 5, 20, "€%d")
taux_credit = slider_input("Taux du crédit", 0.0, 4.0, 0.1, 1.5, "%.2f %%")
duree_credit_ans = slider_input("Durée du crédit", 10, 30, 1, 20, "%d ans")

st.markdown("#### ⚙️ Choix du montage fiscal")
montage = st.radio("Montage", ["Nom Propre (LMNP)", "SCI", "Nom Propre (Nue)"], horizontal=True)

# Le reste du script reste inchangé après cette section


def calculer_resultats(montage):
    duree_credit_mois = duree_credit_ans * 12
    taux_mensuel = taux_credit / 100 / 12
    frais_notaire = prix_bien * 0.08
    frais_dossier = 1400
    montant_emprunte = prix_bien + frais_notaire + frais_dossier + travaux

    if taux_mensuel > 0:
        mensualite = montant_emprunte * (taux_mensuel / (1 - (1 + taux_mensuel) ** -duree_credit_mois))
    else:
        mensualite = montant_emprunte / duree_credit_mois

    solde = montant_emprunte
    interets_annuels = []
    for _ in range(duree_credit_ans):
        interet_total = 0
        for _ in range(12):
            interet = solde * taux_mensuel
            amort = mensualite - interet
            solde -= amort
            interet_total += interet
        interets_annuels.append(interet_total)

    loyer_annuel = loyer * 12
    assurance_annuelle = assurance * 12
    charges_copro_annuelles = charges_copro * 12
    revenu_foncier = loyer_annuel - taxe_fonciere - assurance_annuelle - charges_copro_annuelles
    amortissement_bien = prix_bien / 20
    amortissement_travaux = travaux / 25

    if montage == "Nom Propre (LMNP)":
        revenu_imposable = revenu_foncier - interets_annuels[0] - amortissement_bien - amortissement_travaux
        taux_imposition = 0.582
    elif montage == "SCI":
        revenu_imposable = revenu_foncier - interets_annuels[0] - amortissement_bien - amortissement_travaux
        taux_imposition = 0.15 + 0.172
    else:
        revenu_imposable = revenu_foncier - interets_annuels[0]
        taux_imposition = 0.30 + 0.172

    impot = max(revenu_imposable * taux_imposition, 0)
    credit_annuel = mensualite * 12
    resultat_net = revenu_foncier - credit_annuel - impot
    cashflow = resultat_net / 12
    rendement = (resultat_net / montant_emprunte) * 100

    return {
        "cashflow": round(cashflow, 2),
        "rendement": round(rendement, 2),
        "impot": round(impot),
        "revenu_foncier": revenu_foncier,
        "taxe_fonciere": taxe_fonciere,
        "assurance": assurance_annuelle,
        "charges_copro": charges_copro_annuelles,
        "credit": credit_annuel,
        "interet": round(interets_annuels[0]),
        "frais_notaire": round(frais_notaire),
        "travaux": travaux
    }

if st.button("Calculer"):
    data = calculer_resultats(montage)
    st.session_state.history.insert(0, data)
    st.session_state.history = st.session_state.history[:3]

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
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    ax.axis("off")
    st.pyplot(fig)

    legend_items = [
        f"<span style='color:{colors[i]}'><b>{labels[i]}</b> : {values[i]:,.0f} € ({(values[i]/total*100):.1f}%)</span>"
        for i in range(len(labels))
    ]
    st.markdown(" | ".join(legend_items), unsafe_allow_html=True)

    with st.expander("🔍 Voir détails"):
        st.write(f"Montage : {montage}")
        st.write(f"Impôt : {data['impot']} €")
        st.write(f"Taxe foncière : {data['taxe_fonciere']} €")
        st.write(f"Assurance : {data['assurance']} €")
        st.write(f"Charges copro : {data['charges_copro']} €")
        st.write(f"Crédit : {data['credit']} €")
        st.write(f"Intérêt annuel : {data['interet']} €")
        st.write(f"Frais de notaire : {data['frais_notaire']} €")
        st.write(f"Travaux : {data['travaux']} €")
        st.write(f"Cashflow : {data['cashflow']*12:.2f} € / an")

    # --- Comparaison ---
    with st.expander("📊 Comparer les régimes fiscaux"):
        comparaisons = {m: calculer_resultats(m) for m in ["Nom Propre (LMNP)", "SCI", "Nom Propre (Nue)"]}
        for m, d in comparaisons.items():
            couleur = "green" if d["cashflow"] > 0 else "red"
            st.markdown(f"**{m}** : Cashflow <span style='color:{couleur}'><b>{d['cashflow']} €/mois</b></span> — Rendement : {d['rendement']:.2f} % — Impôt : {d['impot']} €", unsafe_allow_html=True)


