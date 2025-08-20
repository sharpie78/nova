// Font size cycle via #zoom-ratio click (dropdown removed)

const fontSizes = ['1rem', '1.5rem', '2.5rem', '3.5rem'];
let currentFontSizeIndex = 0;

function setFontSize(size) {
  let fontSize = '1.5rem'; // default to medium

  if (size === 'small') fontSize = '1rem';
  else if (size === 'regular') fontSize = '1.5rem';
  else if (size === 'medium') fontSize = '2.5rem';
  else if (size === 'large') fontSize = '3.5rem';
  else fontSize = size;

  cm.getWrapperElement().style.fontSize = fontSize;
  cm.getGutterElement().style.width = `calc(${fontSize} * 1.5)`;
  cm.getGutterElement().style.fontSize = fontSize;
  cm.refresh();
}

const zoomRatioButton = document.getElementById('zoom-ratio');
if (zoomRatioButton) {
  zoomRatioButton.addEventListener('click', () => {
    currentFontSizeIndex = (currentFontSizeIndex + 1) % fontSizes.length;
    setFontSize(fontSizes[currentFontSizeIndex]);
  });
}

// Apply initial font size
setFontSize(fontSizes[currentFontSizeIndex]);
