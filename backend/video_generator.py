from moviepy import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips
from gtts import gTTS


# Generate voice from script
def generate_voice(script, filename):

    tts = gTTS(script)
    tts.save(filename)


# Create video scene from image + audio
def create_scene(image, audio_file, output):

    # load audio first
    audio = AudioFileClip(audio_file)

    # image may be PIL image -> convert automatically
    video = ImageClip(image).set_duration(audio.duration)

    video = video.set_audio(audio)

    video.write_videofile(output, fps=24)


# Combine scenes into final video
def export_final_video(scene_files, output="final_video.mp4"):

    clips = []

    for scene in scene_files:
        clips.append(VideoFileClip(scene))

    final_video = concatenate_videoclips(clips)

    final_video.write_videofile(output, fps=24)