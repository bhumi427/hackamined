# backend/video_generator.py
import subprocess
import os
from mutagen.mp3 import MP3
from PIL import Image

def create_scene_video(images, audio_path, output_path):
    """
    Generates a video from images and audio, syncing video length to audio length.
    Automatically resizes images so width & height are divisible by 2.
    """
    if not images:
        raise ValueError("No images provided for video generation.")

    # Get audio duration
    audio_length = MP3(audio_path).info.length
    num_images = len(images)
    duration_per_image = audio_length / num_images

    # Prepare resized images
    resized_images = []
    for img_path in images:
        img = Image.open(img_path)
        w, h = img.size
        # make width & height divisible by 2
        w2 = w - w % 2
        h2 = h - h % 2
        if (w2, h2) != (w, h):
            img = img.resize((w2, h2))
            resized_path = f"resized_{os.path.basename(img_path)}"
            img.save(resized_path)
            resized_images.append(resized_path)
        else:
            resized_images.append(img_path)

    # Build ffmpeg command using loop for each image
    input_files = []
    filter_complex = ""
    for i, img in enumerate(resized_images):
        input_files.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])
        filter_complex += f"[{i}:v]"

    filter_complex += f"concat=n={num_images}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg",
        "-y",
        *input_files,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{num_images}:a",  # audio input is last
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, check=True)

    # cleanup resized images
    for img in resized_images:
        if img.startswith("resized_") and os.path.exists(img):
            os.remove(img)

    return output_path


def concatenate_videos(video_files, output_file="final_video.mp4"):
    """
    Concatenates multiple scene videos into a single video.
    """
    list_file = "file_list.txt"
    with open(list_file, "w") as f:
        for vf in video_files:
            f.write(f"file '{os.path.abspath(vf)}'\n")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_file
    ]
    subprocess.run(cmd, check=True)
    os.remove(list_file)
    return output_file