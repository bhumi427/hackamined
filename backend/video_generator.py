from moviepy import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips
# from moviepy.editor import *
from gtts import gTTS


# Generate voice from script
def generate_voice(script, filename):

    tts = gTTS(script)
    tts.save(filename)


# Create video scene from image + audio

def create_scene(image_url, audio_file, output):

    image = ImageClip(image_url).set_duration(10)

    audio = AudioFileClip(audio_file)

    video = image.set_audio(audio)

    video.write_videofile(output)


# Combine scenes into final video
def export_final_video(scene_files, output="final_video.mp4"):

    clips = []

    for scene in scene_files:
        clips.append(VideoFileClip(scene))

    final_video = concatenate_videoclips(clips)

    final_video.write_videofile(output)