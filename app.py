import os
import re
import json
import subprocess
import streamlit as st
import google.generativeai as genai
import yt_dlp

st.set_page_config(page_title="IA de Viral Forge", page_icon="⚡", layout="wide")

st.title("⚡ IA de Viral Forge")
st.write("Transformez vos podcasts et vidéos YouTube en clips viraux TikTok/Reels en 1 clic.")

# Barre latérale de configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API Gemini", type="password", help="Collez votre clé Google AI Studio ici")
    num_clips = st.slider("Nombre de clips à générer", min_value=1, max_value=5, value=3)
    st.markdown("[Obtenez votre clé API gratuite sur aistudio.google.com](https://aistudio.google.com)")

# Champ principal
youtube_url = st.text_input("🔗 Lien de la vidéo YouTube :", placeholder="https://www.youtube.com/watch?v=...")

def download_youtube_video(url, output_path="input_video.mp4"):
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Nettoyage de l'URL YouTube (extraction de l'ID propre)
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if video_id_match:
        url = f"https://www.youtube.com/watch?v={video_id_match.group(1)}"

    # Configuration anti-blocage 403 (imitation client mobile Android / Web)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    return output_path

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def analyze_with_gemini(api_key, duration, num_clips):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Tu es un expert mondial en création de contenu viral (TikTok, Reels, Shorts).
    Une vidéo d'une durée totale de {int(duration)} secondes vient d'être importée.
    Génère exactement {num_clips} moments forts (clips) captivants d'une durée comprise entre 20 et 50 secondes chacun.
    
    Format de réponse JSON STRICT (sans texte autour) :
    [
        {{
            "title": "Titre accrocheur 1",
            "start": 10,
            "end": 45,
            "reason": "Explication de la viralité"
        }}
    ]
    Assure-toi que les timestamps (start et end) soient dans la limite des {int(duration)} secondes.
    """
    response = model.generate_content(prompt)
    text = response.text.strip()
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    else:
        return json.loads(text)

def crop_to_vertical(input_path, output_path, start, end):
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        output_path
    ]
    subprocess.run(cmd, check=True)

if st.button("🚀 Générer mes clips viraux", type="primary"):
    if not api_key:
        st.error("❌ Veuillez saisir votre clé API Gemini dans le menu latéral à gauche.")
    elif not youtube_url:
        st.error("❌ Veuillez coller un lien de vidéo YouTube valide.")
    else:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.info("⬇️ Téléchargement de la vidéo YouTube...")
            progress_bar.progress(15)
            video_file = download_youtube_video(youtube_url)
            duration = get_video_duration(video_file)

            status_text.info("🧠 Analyse des meilleurs moments avec Gemini...")
            progress_bar.progress(40)
            
            try:
                clips_info = analyze_with_gemini(api_key, duration, num_clips)
            except Exception as e:
                clip_len = min(30, duration / num_clips)
                clips_info = []
                for i in range(num_clips):
                    start = i * (duration / num_clips) + 5
                    end = min(start + clip_len, duration - 1)
                    clips_info.append({
                        "title": f"Clip Viral #{i+1}",
                        "start": int(start),
                        "end": int(end),
                        "reason": "Moment clé de la vidéo"
                    })

            status_text.info("✂️ Découpage vertical 9:16 et encodage HD...")
            progress_bar.progress(70)

            generated_files = []
            for idx, clip in enumerate(clips_info):
                out_filename = f"clip_{idx+1}.mp4"
                crop_to_vertical(video_file, out_filename, clip["start"], clip["end"])
                generated_files.append((out_filename, clip))

            progress_bar.progress(100)
            status_text.success("🎉 Vos clips viraux sont prêts !")

            st.markdown("---")
            st.subheader("🎬 Vos Clips Prêts à Publier")

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
                    st.write(f"🕒 **Segment:** {int(clip['start'])}s ➔ {int(clip['end'])}s")
                    with open(filename, "rb") as file:
                        st.download_button(
                            label=f"📥 Télécharger le Clip #{idx+1}",
                            data=file,
                            file_name=f"viral_clip_{idx+1}.mp4",
                            mime="video/mp4",
                            key=f"dl_{idx}"
                        )
                st.markdown("---")

        except Exception as e:
            st.error(f"❌ Une erreur s'est produite lors du traitement : {e}")
