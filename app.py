from flask import Flask, request, send_file, render_template
from PIL import Image
import zipfile
import secrets
import io
import os


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


@app.route('/')
def index():
    return render_template('index.html')


def get_renamed_image_filename(image, img, output_format, rename_format):
    original_name, original_ext = os.path.splitext(image.filename)
    if rename_format == 'add_resolution':
        width, height = img.size
        return f'{original_name}_{width}x{height}.{output_format}'
    else:
        return f'{original_name}.{output_format}'


@app.route('/resize_images', methods=['POST'])
def resize_images():
    height = int(request.form['height']) if request.form['height'] else None
    aspect_ratio = request.form.get('aspect-ratio') == 'on'
    images = request.files.getlist('images')
    output_format = request.form['output-format']
    rename_format = request.form['rename-format']
    resized_images = []

    for image in images:
        width = int(request.form['width']) if request.form.get('width') and not aspect_ratio else None
        image_io = io.BytesIO(image.read())
        img = Image.open(image_io)

        if aspect_ratio:
            if height is not None and width is None:
                width = int(img.width * height / img.height)
        elif height is None and width is None:
            height = img.height
            width = img.width

        if width is not None and height is not None:
            img = img.resize((width, height))
        image_io = io.BytesIO()

        if output_format in ['jpg', 'jpeg']:
         if img.mode == 'RGBA':
            img = img.convert('RGB')
            img.save(image_io, 'JPEG')
        elif output_format == 'png':
            img.save(image_io, 'PNG')
        elif output_format == 'ico':
            img.save(image_io, 'ICO')
        elif output_format == 'gif':
            img.save(image_io, 'GIF')
        else:
            return "Invalid output format"

        image_io.seek(0)
        resized_images.append((image_io, get_renamed_image_filename(
            image, img, output_format, rename_format)))

    zip_file = io.BytesIO()

    with zipfile.ZipFile(zip_file, mode='w') as zf:
        for i, (resized_image, image_name) in enumerate(resized_images):
            zf.writestr(image_name, resized_image.getbuffer())

    zip_file.seek(0)
    return send_file(zip_file, download_name='resized_images.zip', as_attachment=True)


if __name__ == '__main__':
    app.run()
