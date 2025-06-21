import streamlit as st
import time
import numpy as np
import pandas as pd

st.set_page_config(page_title="Analyse Immo", page_icon="🏡", layout="centered")

st.title("📊 Analyse Immo - Saisie rapide")

st.markdown("#### 📥 Informations générales")

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

# Pré-calculs
duree_credit_mois = duree_credit_ans * 12
taux_mensuel = taux_credit / 100 / 12
frais_notaire = prix_bien * 0.08
frais_dossier = 1400
montant_emprunte = prix_bien + frais_notaire + frais_dossier + travaux

# Mensualité de crédit
if taux_mensuel > 0:
    mensualite = montant_emprunte * (taux_mensuel / (1 - (1 + taux_mensuel) ** -duree_credit_mois))
else:
    mensualite = montant_emprunte / duree_credit_mois

# Amortissement annuel
solde = montant_emprunte
interets_annuels = []
amortissements_annuels = []
mensualites_annuelles = []

for annee in range(1, duree_credit_ans + 1):
    interet_total = 0
    amortissement_total = 0
    for mois in range(12):
        interet = solde * taux_mensuel
        amortissement = mensualite - interet
        solde -= amortissement
        interet_total += interet
        amortissement_total += amortissement
    interets_annuels.append(interet_total)
    amortissements_annuels.append(amortissement_total)
    mensualites_annuelles.append(mensualite * 12)

# Calculs fiscaux
loyer_annuel = loyer * 12
assurance_annuelle = assurance * 12
revenu_foncier = loyer_annuel - taxe_fonciere - assurance_annuelle
amortissement_bien = prix_bien / 20
amortissement_travaux = travaux / 25
revenu_imposable = revenu_foncier - interets_annuels[0] - amortissement_bien - amortissement_travaux

# Imposition selon montage
taux_imposition = 0.15 if montage == "SCI" else 0.582
impot = max(revenu_imposable * taux_imposition, 0)

credit_annuel = mensualite * 12
resultat_net_annuel = revenu_foncier - impot - credit_annuel
cashflow_mensuel = resultat_net_annuel / 12
rendement_annuel = resultat_net_annuel / montant_emprunte

# Affichage principal
if st.button("🔍 Calculer"):
    with st.spinner("Calcul en cours..."):
        time.sleep(2)

    st.success("✅ Analyse terminée")

    # Cashflow mensuel
    if cashflow_mensuel >= 0:
        st.markdown(f"<h3 style='color:green;'>💶 Cashflow mensuel : {cashflow_mensuel:,.0f} €</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='color:red;'>💶 Cashflow mensuel : {cashflow_mensuel:,.0f} €</h3>", unsafe_allow_html=True)

    # Rendement annuel
    couleur_rendement = (
        "gray" if rendement_annuel < 0.03 else
        "green" if rendement_annuel < 0.05 else
        "purple"
    )
    st.markdown(f"<h4 style='color:{couleur_rendement};'>📈 Rendement annuel : {rendement_annuel * 100:.2f} %</h4>", unsafe_allow_html=True)

    # Détails dans une section repliable
    with st.expander("📂 Voir les détails du calcul"):
        st.markdown("### 📄 Résumé du financement")
        st.write(f"**Montage choisi :** {montage}")
        st.write(f"**Taux d'imposition appliqué :** {int(taux_imposition * 100)} %")
        st.write(f"**Frais de notaire :** {frais_notaire:,.0f} €")
        st.write(f"**Montant total emprunté :** {montant_emprunte:,.0f} €")
        st.write(f"**Mensualité de crédit :** {mensualite:,.0f} €")

        st.markdown("### 📘 Amortissement - Année 1")
        st.write(f"**Intérêts (année 1) :** {interets_annuels[0]:,.0f} €")
        st.write(f"**Capital remboursé (année 1) :** {amortissements_annuels[0]:,.0f} €")

        st.markdown("### 💰 Simulation fiscale")
        st.write(f"**Loyer annuel :** {loyer_annuel:,.0f} €")
        st.write(f"**Assurance annuelle :** {assurance_annuelle:,.0f} €")
        st.write(f"**Revenus fonciers annuels :** {revenu_foncier:,.0f} €")
        st.write(f"**Revenu imposable :** {revenu_imposable:,.0f} €")
        st.write(f"**Impôt estimé :** {impot:,.0f} €")

        st.markdown("### 💸 Résultat net")
        st.write(f"**Résultat net annuel :** {resultat_net_annuel:,.0f} €")

        # Tableau annuel
        df_amortissement = pd.DataFrame({
            "Année": list(range(1, duree_credit_ans + 1)),
            "Mensualités totales (€)": np.round(mensualites_annuelles, 0),
            "Part intérêt (€)": np.round(interets_annuels, 0),
            "Part capital (€)": np.round(amortissements_annuels, 0)
        })

        st.markdown("### 📊 Détail complet du crédit")
        st.dataframe(df_amortissement, use_container_width=True)
