import os
import re

import requests


BASE_REALMEYE_URL = "https://www.realmeye.com"
ASSET_TOKEN_FALLBACK = "gu"


def _get_asset_token() -> str:
    response = requests.get(BASE_REALMEYE_URL, timeout=10)
    response.raise_for_status()

    token_match = re.search(r'"/s/([^/]+)/css/[^"]+\.css"', response.text)
    if token_match:
        return token_match.group(1)

    return ASSET_TOKEN_FALLBACK


def _download_image(image_name: str, asset_path: str) -> None:
    response = requests.get(asset_path, stream=True, timeout=10)
    response.raise_for_status()

    os.makedirs("./images", exist_ok=True)

    with open(os.path.join("./images", image_name), 'wb') as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)

    print(f"Image saved as {image_name}")


def Download_Images() -> None:
    try:
        asset_token = _get_asset_token()
    except requests.exceptions.RequestException as e:
        print(f"Error getting latest RealmEye asset token: {e}. Falling back to '{ASSET_TOKEN_FALLBACK}'.")
        asset_token = ASSET_TOKEN_FALLBACK

    try:
        _download_image("sheets.png", f"{BASE_REALMEYE_URL}/s/{asset_token}/img/sheets.png")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}, sheets.png")
    except Exception as e:
            print(f"An error occurred: {e}, sheets.png")

    try:
        _download_image("renders.png", f"{BASE_REALMEYE_URL}/s/{asset_token}/css/renders.png")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}, renders.png")
    except Exception as e:
            print(f"An error occurred: {e}, renders.png")
