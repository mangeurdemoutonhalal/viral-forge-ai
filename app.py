import streamlit as st
import os
import json
import time
import subprocess
import google.generativeai as genai

# Configuration de la page Viral Forge AI
st.set_page_config(
    page_title="Viral Forge AI - Studio de Clipping Video",
    page_icon="⚡",
    layout="wide"
)

# Titre & Branding
st.title("⚡ Viral Forge AI")
st.caption("Transforme tes podcasts et vidéos YouTube en clips viraux TikTok/Reels en 1 clic.")

# Sidebar pour la configuration API
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_key = st.text_input("Clé API Gemini (commence par AIzaSy...)", type="password")
    num_clips = st.slider("Nombre de clips à générer", min_value=1, max_value=5, value=3)
    st.info("Obtiens ta clé API gratuite sur aistudio.google.com")

# Formulaire principal
youtube_url = st.text_input("🔗 Lien de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Générer mes clips viraux", type="primary"):
    if not gemini_key or not gemini_key.startswith("AIzaSy"):
        st.error("❌ Ta clé API Gemini est invalide. Elle doit commencer par 'AIzaSy'.")
    elif not youtube_url:
        st.warning("⚠️ Veuillez entrer un lien YouTube valide.")
    else:
        try:
            # 1. Config API
            genai.configure(api_key=gemini_key)
            output_dir = "./viral_forge_clips"
            os.makedirs(output_dir, exist_ok=True)

            status_text = st.empty()
            progress_bar = st.progress(0)

            # 2. Téléchargement
            status_text.text("📥 Téléchargement de la vidéo YouTube en haute définition...")
            progress_bar.progress(20)
            
            video_input = "temp_source.mp4"
            cmd_download = [
                "yt-dlp",
                "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--output", video_input,
                "--force-overwrites",
                youtube_url
            ]
            subprocess.run(cmd_download, check=True)

            # 3. Analyse IA
            status_text.text("🧠 Analyse sémantique Gemini 1.5 Pro (détection des hooks viraux)...")
            progress_bar.progress(50)
            
            uploaded_file = genai.upload_file(path=video_input)
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)

            prompt = f"""
            Analyse cette vidéo et trouve les {num_clips} passages les plus viraux pour TikTok/Reels (30 à 60 secondes).
            Renvoie STRICTEMENT un tableau JSON :
            [
              {{
                "title": "Titre_Accrocheur",
                "start_time": 60,
                "end_time": 100,
                "hook": "Raison de la viralité"
              }}
            ]
            """

            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(
                [uploaded_file, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            clips_data = json.loads(response.text)
            genai.delete_file(uploaded_file.name)

            # 4. Découpage & Encodage Web
            status_text.text("🎬 Montage vertical (9:16) et encodage haute compatibilité web...")
            progress_bar.progress(80)

            generated_clips = []
            for idx, clip in enumerate(clips_data, 1):
                clean_title = "".join(c for c in clip["title"] if c.isalnum() or c in ("_", "-"))
                out_path = os.path.join(output_dir, f"ViralForge_{idx}_{clean_title}.mp4")
                start = clip["start_time"]
                duration = clip["end_time"] - start

                # FORCE LE FORMAT COMPATIBLE TOUS LECTEURS (-pix_fmt yuv420p)
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(start),
                    "-t", str(duration),
                    "-i", video_input,
                    "-vf", "crop=ih*(9/16):ih,eq=contrast=1.04:brightness=0.01:saturation=1.05",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",  # FIX LECTURE ÉCRAN NOIR / ERREUR LECTEUR
                    "-preset", "fast",
                    "-c:a", "aac",
                    out_path
                ]
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                generated_clips.append({"path": out_path, "title": clip["title"], "hook": clip.get("hook", "")})

            progress_bar.progress(100)
            status_text.text("✅ Traitement terminé avec succès !")

            # 5. Affichage direct dans Viral Forge AI
            st.subheader("🎯 Vos Clips Générés :")
            cols = st.columns(len(generated_clips))

            for i, clip_info in enumerate(generated_clips):
                with cols[i % len(cols)]:
                    st.markdown(f"**{clip_info['title']}**")
                    st.caption(f"💡 {clip_info['hook']}")
                    
                    # LECTEUR VIDÉO INTÉGRÉ
                    st.video(clip_info["path"])
                    
                    # BOUTON TÉLÉCHARGEMENT DIRECT
                    with open(clip_info["path"], "rb") as file:
                        st.download_button(
                            label="📥 Télécharger ce clip",
                            data=file,
                            file_name=os.path.basename(clip_info["path"]),
                            mime="video/mp4"
                        )

        except Exception as e:
            st.error(f"❌ Une erreur est survenue : {e}")
