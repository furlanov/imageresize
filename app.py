from flask import Flask, request, send_file, render_template, abort
from PIL import Image
import datetime
import zipfile
import requests
import secrets
import openai
import io
import os


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/resize_images', methods=['POST'])
def resize_images():
    resize_type = request.form['resize-type']
    if resize_type == 'ai':
        return resize_ai_image()
    else:
        return resize_simple_images()


def resize_ai_image():
    openai.api_key = ""
    image = request.files['images']
    allowed_file(image.filename)

    img = Image.open(image)
    img = crop(img, 512, 512)
    canvas = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    x = (canvas.width - img.width) // 2
    y = (canvas.height - img.height) // 2
    canvas.paste(img, (x, y))

    temp_filename = os.path.join(os.path.dirname(__file__), "temp", f"{secrets.token_hex(8)}.png")
    canvas.save(temp_filename)

    response = openai.Image.create_edit(
        image=open(temp_filename, "rb"),
        mask=open(temp_filename, "rb"),
        prompt="Fill the transparent space",
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']

    response = requests.get(image_url, stream=True)
    response.raise_for_status()

    image_io = io.BytesIO(response.content)

    original_name, original_ext = os.path.splitext(image.filename)
    output_filename = f'{original_name}.png'

    return send_file(image_io, mimetype='image/png', as_attachment=True, download_name=output_filename)


def resize_simple_images():
    height = int(request.form['height']) if request.form['height'] else None
    aspect_ratio = request.form.get('aspect-ratio') == 'on'
    images = request.files.getlist('images')
    output_format = request.form['output-format']
    rename_format = request.form['rename-format']
    resized_images = []
    for image in images:
        allowed_file(image.filename)

        width = int(request.form['width']) if request.form.get('width') and not aspect_ratio else None
        image_io = io.BytesIO(image.read())
        img = Image.open(image_io)

        if aspect_ratio and height is not None and width is None:
            width = int(img.width * height / img.height)
        elif height is None and width is None:
            height = img.height
            width = img.width

        if width is not None and height is not None:
            img = img.resize((width, height))
        image_io = io.BytesIO()

        img_format, img_save_format = None, None
        if output_format in ['jpg', 'jpeg']:
            img_format, img_save_format = 'JPEG', 'RGB'
        elif output_format == 'png':
            img_format = 'PNG'
        elif output_format == 'ico':
            img_format = 'ICO'
        elif output_format == 'gif':
            img_format = 'GIF'
        elif output_format == 'bmp':
            img_format = 'BMP'
        elif output_format == 'tiff':
            img_format = 'TIFF'
        elif output_format == 'webp':
            img_format = 'WEBP'

        if img.mode == 'RGBA' and img_save_format:
            img = img.convert(img_save_format)

        img.save(image_io, img_format)
        image_io.seek(0)
        resized_images.append((image_io, get_renamed_image_filename(image, img, output_format, rename_format)))

    if len(resized_images) == 1:
        return send_file(resized_images[0][0], download_name=resized_images[0][1], as_attachment=True)
    else:
        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, mode='w') as zf:
            for i, (resized_image, image_name) in enumerate(resized_images):
                zf.writestr(image_name, resized_image.getbuffer())

        zip_file.seek(0)
        return send_file(zip_file, download_name='resized_images.zip', as_attachment=True)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'ico', 'webp'}
    if not '.' in filename or \
            filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        abort(400, "Only JPG, JPEG, PNG, ICO, and GIF are allowed")


def get_renamed_image_filename(image, img, output_format, rename_format):
    original_name, original_ext = os.path.splitext(image.filename)
    if rename_format == 'add_resolution':
        width, height = img.size
        return f'{original_name}_{width}x{height}.{output_format}'
    if rename_format == 'add_date':
        current_date = datetime.date.today()
        return f'{original_name}_{current_date.strftime("%d_%m_%Y")}.{output_format}'
    else:
        return f'{original_name}.{output_format}'


def crop(image, target_width, target_height):
    width, height = image.size
    aspect_ratio = width / height

    target_aspect_ratio = target_width / target_height

    if aspect_ratio > target_aspect_ratio:
        new_width = int(height * target_aspect_ratio)
        left = (width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = height
    else:
        new_height = int(width / target_aspect_ratio)
        left = 0
        top = (height - new_height) // 2
        right = width
        bottom = top + new_height

    image = image.crop((left, top, right, bottom))

    image = image.resize((target_width, target_height))

    return image

@app.errorhandler(400)
def error_400(error):
    return render_template('error.html', error_message=error.description), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0')