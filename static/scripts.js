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