import base64


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


if __name__ == "__main__":
    image_path = "image_data/wheat_rust.jpg"
    base64_string = image_to_base64(image_path)
    print(base64_string)
