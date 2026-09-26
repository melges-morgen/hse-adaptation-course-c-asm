// Shared initialization: no remote assets, no autoplay, the PDF uses the same DOM.
const sections = [...document.querySelectorAll('.slides > section')];
const mainCount = sections.filter(section => !section.classList.contains('supplement')).length;
const lectureLabel = document.body.dataset.lectureLabel || 'Лекция 02';
sections.forEach((section, index) => {
  const footer = document.createElement('div');
  footer.className = 'slide-footer';
  const label = document.createElement('span');
  label.textContent = section.classList.contains('supplement')
    ? `Дополнительно · ${document.body.dataset.supplementLabel || 'арифметика и точность'}`
    : `${lectureLabel} · ${section.dataset.block || 'Кодирование данных и команд'}`;
  const number = document.createElement('span');
  number.textContent = `${String(index + 1).padStart(2, '0')} / ${sections.length}`;
  footer.append(label, number);
  section.append(footer);
});
window.courseReady = Reveal.initialize({
  width: 1280, height: 720, margin: 0.02, minScale: 0.1, maxScale: 2,
  center: false, hash: true, controls: true, progress: true,
  transition: 'none', backgroundTransition: 'none',
  // Keep slide mode on narrow screens; phone users can rotate to landscape.
  scrollActivationWidth: null,
  pdfSeparateFragments: false, pdfMaxPagesPerSlide: 1,
  showNotes: false, plugins: [RevealNotes],
});
window.courseMainSlideCount = mainCount;
