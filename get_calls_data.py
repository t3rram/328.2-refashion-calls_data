import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import base64
from io import BytesIO

# Fonction pour convertir un DataFrame en fichier CSV téléchargeable
def to_csv(df):
    output = BytesIO()
    df.to_csv(output, index=False)
    processed_data = output.getvalue()
    return processed_data

# Fonction pour générer un lien de téléchargement d'un fichier CSV
def get_table_download_link(df):
    val = to_csv(df)
    b64 = base64.b64encode(val).decode()  # Valeurs encodées en base64
    href = f'<a href="data:text/csv;base64,{b64}" download="filtered_data.csv">Télécharger les données filtrées (CSV)</a>'
    return href

# Fonction pour lire et filtrer le fichier XML
def load_and_filter_data(file, phone_filter, name_filter, start_date, end_date):
    tree = ET.parse(file)
    root = tree.getroot()
    
    data = []
    for call in root.findall('call'):
        number = call.get('number')
        contact_name = call.get('contact_name', '').lower()  # Convertir le nom du contact en minuscules
        date_time = datetime.fromtimestamp(int(call.get('date')) / 1000)
        duration = int(call.get('duration'))
        call_type = call.get('type')  # Type d'appel
        
        # Vérifier si la date est dans l'intervalle spécifié
        if start_date and end_date:
            if not (start_date <= date_time.date() <= end_date):
                continue

        if (not phone_filter or phone_filter in number) and \
           (not name_filter or name_filter.lower() in contact_name):
            data.append([number, contact_name, date_time.strftime('%Y-%m-%d %H:%M:%S'), duration, call_type])
    
    df = pd.DataFrame(data, columns=['Number', 'Contact Name', 'Date Time', 'Duration', 'Type'])
    # Créer un tableau récapitulatif pour les types d'appels
    # Appels entrants: types 1, 3, 5
    # Appels sortants: types 2, 4
    summary_data = {
        'Type d\'appel': ['Appels Entrants', 'Appels Sortants'],
        'Nombre d\'appels': [
            df[df['Type'].isin(['1', '3', '5'])].shape[0],
            df[df['Type'].isin(['2', '4'])].shape[0]
        ],
        'Somme de la durée': [
            df[df['Type'].isin(['1', '3', '5'])]['Duration'].sum(),
            df[df['Type'].isin(['2', '4'])]['Duration'].sum()
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    return df, summary_df


# Interface Streamlit avec sidebar pour les filtres
st.title('Analyseur d\'appels XML')

# Téléchargement du fichier dans la sidebar
uploaded_file = st.sidebar.file_uploader("Choisissez un fichier XML", type=['xml'])

# Filtres dans la sidebar
phone_filter = st.sidebar.text_input('Filtrer par numéro de téléphone:')
name_filter = st.sidebar.text_input('Filtrer par nom de contact:')

# Sélection de l'intervalle de dates
date_range = st.sidebar.date_input("Filtrer par intervalle de dates:", [], key="date_range")

start_date, end_date = date_range if len(date_range) == 2 else (None, None)

if uploaded_file is not None:
    # Charger et filtrer les données
    df_filtered, summary_df = load_and_filter_data(uploaded_file, phone_filter, name_filter, start_date, end_date)
    # Afficher le tableau récapitulatif
    if not summary_df.empty:
        st.write("Récapitulatif par type d'appel :")
        st.write(summary_df)
    # Afficher les données filtrées
    if not df_filtered.empty:
        st.write("Données filtrées :")
        st.write(df_filtered)
        st.markdown(get_table_download_link(df_filtered), unsafe_allow_html=True)
    else:
        st.write("Aucun résultat correspondant aux filtres.")