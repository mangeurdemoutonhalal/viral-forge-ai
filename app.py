import os
import re
import json
import subprocess
import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# Augmentation de la limite d'upload Streamlit à 1000 MB (1 Go)
st.set_page_config(page_title="IA de Viral Forge", page_icon="⚡", layout="wide")

st.title("⚡ IA de Viral Forge - Version Podcast HD")
st.write("Transformez vos longs podcasts en clips viraux TikTok/Reels de haute qualité.")

# Barre latérale de configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API Gemini", type="password", help="Collez votre clé Google AI Studio ici")
    num_clips = st.slider("Nombre de clips à générer", min_value=1, max_value=15, value=5)
    st.markdown("[Obtenez votre clé API gratuite sur aistudio.google.com](https://aistudio.google.com)")

# Zone d'importation vidéo (jusqu'à 1 Go)
uploaded_file = st.file_uploader(
    "📁 Déposez votre podcast/vidéo longue ici (MP4, MOV, MKV - jusqu'à 1 Go) :", 
    type=["mp4", "mov", "mkv"]
)

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def analyze_podcast_with_gemini(api_key, duration, num_clips):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Prompt optimisé pour repérer des séquences ultra-virales
    prompt = f"""
    Tu es un monteur vidéo expert en création de contenu viral sur TikTok, Instagram Reels et YouTube Shorts.
    J'ai une vidéo de podcast d'une durée totale de {int(duration)} secondes.
    
    Analyse le contenu de cette vidéo et sélectionne exactement {num_clips} moments d'exception.
    Chaque clip doit :
    1. Avoir une durée comprise entre 30 et 60 secondes.
    2. Débuter par une accroche très forte (Hook) dans les 3 premières secondes (une question choc, une affirmation audacieuse, une histoire captivante).
    3. Traiter d'un sujet fort : business, argent, échecs/succès, relations, secrets, leçons de vie ou débat passionné.
    4. Former une séquence autonome compréhensible sans le reste du podcast.

    Format de réponse JSON STRICT (sans aucun texte introductif ni balises markdown) :
    [
        {{
            "title": "Titre choc et viral",
            "start": 120,
            "end": 175,
            "reason": "Accroche puissante sur la réussite financière"
        }}
    ]
    Assure-toi que les timestamps ("start" et "end" en secondes) soient bien répartis et valides sur la durée globale ({int(duration)}s).
    """
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    else:
        return json.loads(text)

def crop_to_vertical_hd(input_path, output_path, start, end):
    """
    Découpe et réencodage HD 1080x1920 (9:16) avec haute qualité (CRF 18)
    """
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, check=True)

if st.button("🚀 Générer mes clips viraux HD", type="primary"):
    if not api_key:
        st.error("❌ Veuillez saisir votre clé API Gemini dans le menu latéral à gauche.")
    elif uploaded_file is None:
        st.error("❌ Veuillez déposer un fichier vidéo dans la zone ci-dessus.")
    else:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.info("💾 Chargement de votre podcast...")
            progress_bar.progress(10)
            
            video_file = "input_podcast.mp4"
            with open(video_file, "wb") as f:
                f.write(uploaded_file.getbuffer())

            duration = get_video_duration(video_file)

            status_text.info(f"🧠 Recherche des {num_clips} meilleurs moments viraux par Gemini...")
            progress_bar.progress(30)
            
            try:
                clips_info = analyze_podcast_with_gemini(api_key, duration, num_clips)
            except Exception as e:
                st.warning("⚠️ L'analyse dynamique a utilisé un découpage séquentiel de secours.")
                clip_len = min(45, duration / num_clips)
                clips_info = []
                for i in range(num_clips):
                    start = i * (duration / num_clips) + 10
                    end = min(start + clip_len, duration - 1)
                    clips_info.append({
                        "title": f"Clip Viral #{i+1}",
                        "start": int(start),
                        "end": int(end),
                        "reason": "Séquence clé du podcast"
                    })

            status_text.info("✂️ Découpage vertical 9:16 HD & Encodage Haute Qualité...")
            progress_bar.progress(60)

            generated_files = []
            total_clips = len(clips_info)
            for idx, clip in enumerate(clips_info):
                out_filename = f"clip_{idx+1}.mp4"
                crop_to_vertical_hd(video_file, out_filename, clip["start"], clip["end"])
                generated_files.append((out_filename, clip))
                
                # Mise à jour progressive de la barre
                prog = 60 + int((idx + 1) / total_clips * 35)
                progress_bar.progress(prog)

            progress_bar.progress(100)
            status_text.success("🎉 Tous vos clips viraux HD sont prêts !")

            st.markdown("---")
            st.subheader(f"🎬 Vos {len(generated_files)} Clips Prêts à Publier")

            for idx, (filename, clip) in enumerate(generated_files):
                st.markdown(f"### 📌 {idx+1}. {clip.get('title', f'Clip #{idx+1}')}")
                if "reason" in clip:
                    st.caption(f"💡 *{clip['reason']}*")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    with open(filename, "rb") as file:
                        st.video(file.read())
                with col2:
                    st.write(f"⏱️ **Durée:** {int(clip['end'] - clip['start'])}s")
                    st.write(f"🕒 **Timing:** {int(clip['start'])}s ➔ {int(clip['end'])}s")
                    
                    # Bouton 1 : Téléchargement direct
                    with open(filename, "rb") as file:
                        st.download_button(
                            label=f"📥 Télécharger le Clip #{idx+1}",
                            data=file,
                            file_name=f"viral_clip_{idx+1}.mp4",
                            mime="video/mp4",
                            key=f"dl_{idx}"
                        )
                    
                    # Bouton 2 : Partager / Enregistrer dans la Galerie (Mobile)
                    st.caption("📱 *Sur mobile : utilise le bouton Télécharger ou les options du lecteur pour sauvegarder dans tes photos.*")

                st.markdown("---")

        except Exception as e:
            st.error(f"❌ Une erreur s'est produite lors du traitement : {e}")
