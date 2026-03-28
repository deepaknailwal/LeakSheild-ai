from flask import Flask, render_template, request
from PIL import Image
import numpy as np
import os
import hashlib

app = Flask(__name__)

# Folder setup
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HASH_FILE = "hashes.txt"

# Convert text to ASCII
def text_to_ascii(text):
    text = text.ljust(10)[:10]
    return [ord(c) for c in text]

# Convert ASCII back to text
def ascii_to_text(arr):
    return ''.join([chr(i) for i in arr]).strip()

# Add watermark
def add_watermark(image_path, owner):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)

    data = text_to_ascii(owner)

    for i in range(len(data)):
        pixels[0][i][0] = data[i]

    filename = "watermarked_" + os.path.basename(image_path)
    path = os.path.join(UPLOAD_FOLDER, filename)

    Image.fromarray(pixels).save(path)
    return filename

# Extract watermark
def extract_watermark(image_path):
    img = Image.open(image_path)
    pixels = np.array(img)

    data = []
    for i in range(10):
        data.append(pixels[0][i][0])

    return ascii_to_text(data)

# Generate image hash
def get_image_hash(image_path):
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    image = None
    risk = ""

    if request.method == "POST":
        file = request.files.get("image")
        owner = request.form.get("owner")

        if file and owner:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            # HASH CHECK
            img_hash = get_image_hash(filepath)
            match_found = False

            if os.path.exists(HASH_FILE):
                with open(HASH_FILE, "r") as f:
                    hashes = f.read().splitlines()
                    if img_hash in hashes:
                        match_found = True

            with open(HASH_FILE, "a") as f:
                f.write(img_hash + "\n")

            # WATERMARK
            watermarked_filename = add_watermark(filepath, owner)
            watermarked_path = os.path.join(UPLOAD_FOLDER, watermarked_filename)

            extracted = extract_watermark(watermarked_path)

            # RESULT
            if match_found:
                result = f"⚠️ MATCH FOUND! Possible Reuse | Owner: {extracted}"
                risk = "HIGH 🔴"
            else:
                result = f"✅ New Image | Owner: {extracted}"
                risk = "LOW 🟢"

            image = watermarked_filename

    return render_template("index.html", result=result, image=image, risk=risk)

if __name__ == "__main__":
    import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
