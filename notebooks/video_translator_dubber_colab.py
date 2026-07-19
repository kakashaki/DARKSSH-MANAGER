# @title 🎬 Video Translator & Dubber {display-mode: "form"}

# ==============================================================================
# BƯỚC 1: KIỂM TRA VÀ CÀI ĐẶT HỆ THỐNG
# ==============================================================================
import os
import subprocess
import sys

def install_dependencies():
    """Kiểm tra và cài đặt thư viện, chỉ restart nếu thực sự cần thiết"""
    need_restart = False
    try:
        import httpx
        import gradio as gr
        import jinja2
        # Kiểm tra tính tương thích của httpx (phải có AsyncHTTPTransport cho Gradio mới)
        if not hasattr(httpx, 'AsyncHTTPTransport'):
            print("🔄 Phát hiện phiên bản httpx cũ, đang cập nhật...")
            need_restart = True
    except (ImportError, AttributeError):
        print("📦 Đang thiếu thư viện quan trọng, tiến hành cài đặt...")
        need_restart = True

    if need_restart:
        print("⏳ Đang cấu hình môi trường... (Hệ thống sẽ tự khởi động lại)")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "httpx>=0.24.1", "gradio", "jinja2"])
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "faster-whisper", "googletrans==4.0.0-rc1", "edge-tts", "srt", "librosa", "soundfile"])

        print("✅ Cài đặt xong! Đang khởi động lại session... VUI LÒNG NHẤN CHẠY LẠI Ô NÀY SAU 5 GIÂY.")
        import os
        os.kill(os.getpid(), 9)
    else:
        print("✅ Hệ thống đã sẵn sàng!")

install_dependencies()

import srt
import shutil
import asyncio
import librosa
import soundfile as sf
import gradio as gr
from datetime import timedelta
from faster_whisper import WhisperModel
from googletrans import Translator
import edge_tts

# Cấu hình thư mục làm việc
WORKSPACE = "gensub_stable_workspace"
if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE, exist_ok=True)

# Nạp model
print("🤖 Đang nạp OpenAI Whisper Large-V3...")
try:
    # Chỉ nạp model nếu chưa có trong bộ nhớ
    if 'whisper_model' not in globals():
        whisper_model = WhisperModel("large-v3", device="cuda", compute_type="float16")
except Exception:
    if 'whisper_model' not in globals():
        print("⚠️ Đang sử dụng CPU (Sẽ chậm hơn do không tìm thấy GPU)")
        whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")

translator = Translator()
VOICE_MAPPING = {
    "Tiếng Việt - Giọng Nữ Truyền Cảm (Hoài Như)": "vi-VN-HoaiNhuNeural",
    "Tiếng Việt - Giọng Nam Sâu Lắng (Nam Minh)": "vi-VN-NamMinhNeural"
}

# ==============================================================================
# BƯỚC 2: PIPELINE XỬ LÝ
# ==============================================================================
async def core_process_engine(video_path, voice_name, progress=gr.Progress()):
    if not video_path: return None, "❌ Vui lòng tải file video lên!"

    # Dọn dẹp workspace cũ cho mỗi lần chạy mới
    if os.path.exists(WORKSPACE): shutil.rmtree(WORKSPACE)
    os.makedirs(WORKSPACE, exist_ok=True)

    audio_original = os.path.join(WORKSPACE, "audio_original.wav")
    voice_over_master = os.path.join(WORKSPACE, "voice_over_master.wav")
    video_output = os.path.join(WORKSPACE, "gensub_final_output.mp4")
    selected_voice = VOICE_MAPPING.get(voice_name, "vi-VN-HoaiNhuNeural")

    try:
        progress(0.1, desc="🎵 Trích xuất âm thanh...")
        subprocess.run(f"ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 24000 -ac 1 {audio_original} -y".split(), check=True, capture_output=True)

        progress(0.3, desc="🤖 Nhận diện giọng nói...")
        segments, _ = whisper_model.transcribe(audio_original, beam_size=5, vad_filter=True)
        subs = [srt.Subtitle(index=i, start=timedelta(seconds=s.start), end=timedelta(seconds=s.end), content=s.text.strip()) for i, s in enumerate(segments, start=1)]

        if not subs: return None, "❌ Không tìm thấy giọng nói."

        progress(0.5, desc="🌐 Dịch thuật...")
        for sub in subs:
            try: sub.content = translator.translate(sub.content, dest="vi").text
            except: pass

        progress(0.7, desc="🗣️ Tạo giọng đọc AI...")
        concat_list_path = os.path.join(WORKSPACE, "concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as concat_f:
            last_end_ms = 0
            for i, sub in enumerate(subs):
                start_ms, end_ms = int(sub.start.total_seconds() * 1000), int(sub.end.total_seconds() * 1000)
                dur_target = (end_ms - start_ms) / 1000.0
                silence = (start_ms - last_end_ms) / 1000.0

                if silence > 0:
                    s_file = os.path.join(WORKSPACE, f"s_{i}.wav")
                    subprocess.run(f"ffmpeg -f lavfi -i anullsrc=r=24000:cl=mono -t {silence} {s_file} -y".split(), check=True, capture_output=True)
                    concat_f.write(f"file 's_{i}.wav'\n")

                t_mp3, t_wav = os.path.join(WORKSPACE, f"t_{i}.mp3"), os.path.join(WORKSPACE, f"t_{i}.wav")
                await edge_tts.Communicate(sub.content, selected_voice).save(t_mp3)
                subprocess.run(f"ffmpeg -i {t_mp3} -ar 24000 -ac 1 {t_wav} -y".split(), check=True, capture_output=True)

                y, sr = librosa.load(t_wav, sr=24000)
                act_dur = librosa.get_duration(y=y, sr=sr)
                f_wav = os.path.join(WORKSPACE, f"f_{i}.wav")

                if act_dur > dur_target and dur_target > 0:
                    ratio = min(act_dur / dur_target, 1.6)
                    subprocess.run(f"ffmpeg -i {t_wav} -filter:a atempo={ratio} {f_wav} -y".split(), check=True, capture_output=True)
                else: shutil.copy(t_wav, f_wav)

                concat_f.write(f"file 'f_{i}.wav'\n")
                last_end_ms = end_ms

        subprocess.run(f"ffmpeg -f concat -safe 0 -i concat_list.txt -c copy {voice_over_master} -y", shell=True, cwd=WORKSPACE, check=True, capture_output=True)

        progress(0.9, desc="🎬 Hoàn thiện video...")
        subprocess.run(f"ffmpeg -i {video_path} -i {voice_over_master} -c:v copy -map 0:v:0 -map 1:a:0 {video_output} -y".split(), check=True, capture_output=True)

        return video_output, "🎉 Hoàn thành!"
    except Exception as e:
        return None, f"❌ Lỗi: {str(e)}"

def start_pipeline(video, voice):
    return asyncio.run(core_process_engine(video, voice))

# ==============================================================================
# BƯỚC 3: GIAO DIỆN
# ==============================================================================
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 Dịch & Lồng Tiếng Video")
    with gr.Row():
        with gr.Column():
            in_v = gr.Video(label="Video gốc")
            v_sel = gr.Dropdown(label="Giọng đọc", choices=list(VOICE_MAPPING.keys()), value=list(VOICE_MAPPING.keys())[0])
            btn = gr.Button("BẮT ĐẦU", variant="primary")
        with gr.Column():
            status = gr.Textbox(label="Trạng thái")
            out_v = gr.Video(label="Kết quả")
    btn.click(start_pipeline, [in_v, v_sel], [out_v, status])

demo.queue().launch(share=True, debug=True, inline=False)
