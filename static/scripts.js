function toggleAspectRatio() {
    let aspectRatioCheckbox = document.getElementById('aspect-ratio');
    let widthInput = document.getElementById('width');
    if (aspectRatioCheckbox.checked) {
        widthInput.disabled = true;
        widthInput.value = '';
        widthInput.setAttribute('placeholder', 'Auto');
    } else {
        widthInput.disabled = false;
        widthInput.setAttribute('placeholder', 'Width (px)');
    }
}

function toggleResizeType() {
    const resizeType = document.getElementById('resize-type').value;
    const heightInput = document.getElementById('height');
    const widthInput = document.getElementById('width');
    const fileInput = document.getElementById('images');

    if (resizeType === 'ai') {
        heightInput.value = 1024;
        widthInput.value = 1024;
        heightInput.setAttribute('readonly', 'readonly');
        widthInput.setAttribute('readonly', 'readonly');
        heightInput.classList.add('grayed-out');
        widthInput.classList.add('grayed-out');
        document.getElementById('aspect-ratio').setAttribute('disabled', 'disabled');
        fileInput.setAttribute('required', true);
        fileInput.removeAttribute('multiple');
    } else {
        heightInput.value = '';
        widthInput.value = '';
        heightInput.removeAttribute('readonly');
        widthInput.removeAttribute('readonly');
        heightInput.classList.remove('grayed-out');
        widthInput.classList.remove('grayed-out');
        document.getElementById('aspect-ratio').removeAttribute('disabled');
        fileInput.setAttribute('multiple', false);
        fileInput.setAttribute('required', true);
    }
}