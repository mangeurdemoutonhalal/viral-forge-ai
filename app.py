import streamlit as st
import os
import json
import time
import subprocess
import google.generativeai as genai

st.set_page_config(page_title="IA de Viral Forge", page_icon="⚡", layout="wide")

st.title("⚡ IA de Viral Forge")
st.write("Transformez vos podcasts et vidéos YouTube en clips viraux TikTok/Reels en 1 clic.")

# Configuration dans la barre latérale
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API Gemini", type="password", help="Collez votre clé Google AI Studio ici")
    num_clips = st.slider("Nombre de clips à générer", min_value=1, max_value=5, value=3)
    st.markdown("[Obtenez votre clé API gratuite sur aistudio.google.com](https://aistudio.google.com)")

# Champ de saisie principal
youtube_url = st.text_input("🔗 Lien de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Générer mes clips viraux", type="primary"):
    if not api_key:
        st.error("❌ Veuillez saisir votre clé API Gemini dans le menu latéral à gauche.")
    elif not youtube_url:
        st.error("❌ Veuillez coller un lien de vidéo YouTube valide.")
    else:
        st.success("✅ Clé API et lien validés ! Lancement du traitement...")
        st.info("Le téléchargement et le découpage de la vidéo sont en cours...")
        # Le reste du traitement s'exécute ici
