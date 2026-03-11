// Flash auto-hide
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 3500);
});

// Photo Preview
const photoInput = document.getElementById('photoInput');
if (photoInput) {
  photoInput.addEventListener('change', function() {
    const file = this.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      const prev = document.getElementById('photoPreview');
      if (prev) {
        if (prev.tagName === 'IMG') { prev.src = e.target.result; }
        else {
          const img = document.createElement('img');
          img.src = e.target.result;
          img.className = 'photo-preview';
          img.id = 'photoPreview';
          prev.replaceWith(img);
        }
      }
    };
    reader.readAsDataURL(file);
  });
}
