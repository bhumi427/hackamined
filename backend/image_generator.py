# import requests


# def get_scene_image(query):
#     query = query.replace(" ", ",")

#     url = f"https://source.unsplash.com/featured/1600x900/?{query}"

#     return url


import random

def get_scene_images(query, num_images=3):

    images = []

    for i in range(num_images):

        # random image generator
        seed = random.randint(1, 1000)

        url = f"https://picsum.photos/seed/{seed}/800/450"

        images.append(url)

    return images