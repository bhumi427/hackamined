import requests

def get_scene_image(query):

    url = f"https://source.unsplash.com/1600x900/?{query}"

    return url