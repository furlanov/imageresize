from flask import Flask, request, send_file, render_template
from PIL import Image
import datetime
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
    if rename_format == 'add_date':
        current_date = datetime.date.today()
        return f'{original_name}_{current_date.strftime("%d_%m_%Y")}.{output_format}'
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
        if not image:
            return "No file selected"
        if not allowed_file(image.filename):
            return "Invalid file type. Images with extensions - JPG, JPEG, PNG, ICO, and GIF are allowed"
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
        else:
            return "Invalid output format. Choose between JPG, JPEG, PNG, ICO and GIF."
        
        if img.mode == 'RGBA' and img_save_format:
            img = img.convert(img_save_format)
            
        img.save(image_io, img_format)
        image_io.seek(0)
        resized_images.append((image_io, get_renamed_image_filename(image, img, output_format, rename_format)))

    zip_file = io.BytesIO()

    with zipfile.ZipFile(zip_file, mode='w') as zf:
        for i, (resized_image, image_name) in enumerate(resized_images):
            zf.writestr(image_name, resized_image.getbuffer())

    zip_file.seek(0)
    return send_file(zip_file, download_name='resized_images.zip', as_attachment=True)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'ico', 'webp'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(host='0.0.0.0')