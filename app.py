from flask import Flask, request, send_file, render_template, abort
from PIL import Image
import datetime
import zipfile
import requests
import secrets
import openai
import io
import os
import api


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'ico', 'bmp', 'tiff', 'webp'}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/resize_images', methods=['POST'])
def resize_images():
    resize_type = request.form['resize-type']
    if resize_type == 'ai':
        result = resize_ai()
    else:
        result = resize_stretch()
    return result


def resize_ai():
    openai.api_key = api.api_key
    image = request.files['images']
    allowed_file(image.filename)
    output_format = request.form['output-format']
    rename_format = request.form['rename-format']

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
        prompt="Fill the image",
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']

    response = requests.get(image_url, stream=True)
    response.raise_for_status()

    image_io = io.BytesIO(response.content)
    img = Image.open(image_io)

    img, img_format = format(img, output_format)

    output_io = io.BytesIO()
    img.save(output_io, format=img_format)
    output_io.seek(0)

    output_filename = rename(image, img, output_format, rename_format)

    return send_file(output_io, mimetype=f'image/{output_format}', as_attachment=True, download_name=output_filename)


def resize_stretch():
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

        img, img_format = format(img, output_format)

        img.save(image_io, img_format)
        image_io.seek(0)
        resized_images.append((image_io, rename(image, img, output_format, rename_format)))

    if len(resized_images) == 1:
        return send_file(resized_images[0][0], download_name=resized_images[0][1], as_attachment=True)
    else:
        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, mode='w') as zf:
            for i, (resized_image, image_name) in enumerate(resized_images):
                zf.writestr(image_name, resized_image.getbuffer())
        zip_file.seek(0)
        return send_file(zip_file, download_name='resized_images.zip', as_attachment=True)
    

def format(img, output_format):
    format_conversion = {
        'jpg': ('JPEG', 'RGB'),
        'png': ('PNG', None),
        'ico': ('ICO', None),
        'gif': ('GIF', None),
        'bmp': ('BMP', None),
        'tiff': ('TIFF', None),
        'webp': ('WEBP', None)
    }
    img_format, img_save_format = format_conversion.get(output_format, (None, None))

    if img.mode == 'RGBA' and img_save_format:
        img = img.convert(img_save_format)

    return img, img_format


def allowed_file(filename):
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        abort(400, "Only JPG, JPEG, PNG, ICO, BMM, TIFF and GIF are allowed")


def rename(image, img, output_format, rename_format):
    original_name, original_ext = os.path.splitext(image.filename)

    if rename_format == 'add_resolution':
        width, height = img.size
        return f'{original_name}_{width}x{height}.{output_format}'
    elif rename_format == 'add_date':
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