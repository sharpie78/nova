// Font size cycle via #zoom-ratio click (dropdown removed)

const fontSizes = ['1.5rem', '2.0rem', '2.5rem', '2.75rem'];
let currentFontSizeIndex = 0;

function setFontSize(size) {
  let fontSize = '1.5rem'; // default to medium

  if (size === 'small') fontSize = '1.5rem';
  else if (size === 'regular') fontSize = '2.0rem';
  else if (size === 'medium') fontSize = '2.5rem';
  else if (size === 'large') fontSize = '2.75rem';
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
