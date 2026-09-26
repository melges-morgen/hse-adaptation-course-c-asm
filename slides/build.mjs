import { cp, mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { resolve, extname, sep } from 'node:path';
import { chromium } from 'playwright';

const workspace = process.cwd();
const build = resolve(workspace, process.argv[2] || 'build');
const id = process.argv[3] || 'lecture02';
const presentations = JSON.parse(await readFile(resolve(workspace, 'slides/presentations.json'), 'utf8'));
if (!Object.hasOwn(presentations, id)) throw new Error(`Unknown presentation: ${id}`);
const expected = presentations[id];
const output = resolve(build, 'slides');
await mkdir(output, { recursive: true });
await cp(resolve(workspace, 'slides', id), resolve(output, id), { recursive: true });
await cp(resolve(workspace, 'slides/theme'), resolve(output, 'theme'), { recursive: true });
await mkdir(resolve(output, 'vendor/reveal'), { recursive: true });
for (const name of ['dist', 'plugin', 'LICENSE']) {
  await cp(`/opt/slides/node_modules/reveal.js/${name}`, resolve(output, 'vendor/reveal', name), { recursive: true });
}
await mkdir(resolve(output, 'vendor/fonts'), { recursive: true });
for (const name of ['Carlito-Regular.ttf', 'Carlito-Bold.ttf']) {
  await cp(`/usr/share/fonts/truetype/crosextra/${name}`, resolve(output, 'vendor/fonts', name));
}
await cp('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', resolve(output, 'vendor/fonts/DejaVuSansMono.ttf'));
await cp('/usr/share/doc/fonts-crosextra-carlito/copyright', resolve(output, 'vendor/fonts/Carlito-LICENSE'));
await cp('/usr/share/doc/fonts-dejavu-core/copyright', resolve(output, 'vendor/fonts/DejaVu-LICENSE'));
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.ttf': 'font/ttf', '.svg': 'image/svg+xml' };
const server = createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    let path = resolve(output, `.${pathname}`);
    if (!path.startsWith(output + sep)) { res.writeHead(403).end(); return; }
    if ((await stat(path)).isDirectory()) path = resolve(path, 'index.html');
    res.setHeader('Content-Type', types[extname(path)] || 'application/octet-stream');
    res.end(await readFile(path));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', req => errors.push(`${req.url()}: ${req.failure()?.errorText}`));
  page.on('response', res => { if (res.status() >= 400) errors.push(`${res.status()} ${res.url()}`); });
  await page.route('**/*', route => {
    if (!route.request().url().startsWith(`http://127.0.0.1:${server.address().port}/`)) {
      errors.push(`External request: ${route.request().url()}`);
      return route.abort();
    }
    return route.continue();
  });
  const url = `http://127.0.0.1:${server.address().port}/${id}/index.html`;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.evaluate(async () => { await window.courseReady; await document.fonts.ready; });
  const report = await page.evaluate(expected => {
    const slides = [...document.querySelectorAll('.slides > section')];
    const issues = [];
    if (slides.length !== expected.slides) issues.push({ issue: `expected ${expected.slides} slides, got ${slides.length}` });
    if (window.courseMainSlideCount !== expected.mainSlides) issues.push({ issue: 'unexpected main/supplement split' });
    for (const pre of document.querySelectorAll('pre')) {
      if (pre.querySelector('div,p,aside,section')) issues.push({ issue: 'malformed pre block', text: pre.textContent.slice(0, 50) });
    }
    if (document.querySelectorAll('.slides section').length !== slides.length) issues.push({ issue: 'unexpected nested slides' });
    for (const [index, slide] of slides.entries()) {
      if (expected.sourceSequence && Number(slide.dataset.sourceSlide) !== index + 1) {
        issues.push({ slide: index + 1, issue: 'PPTX slide order is not preserved' });
      }
      Reveal.slide(index);
      const rect = slide.getBoundingClientRect();
      const scale = rect.width / 1280;
      for (const el of slide.querySelectorAll('h1,h2,h3,p,li,pre,table,.bits,svg,.panel,img.diagram')) {
        if (el.closest('.notes')) continue;
        const r = el.getBoundingClientRect();
        if (r.bottom > rect.top + 648 * scale || r.right > rect.right - 50 * scale || r.left < rect.left) {
          issues.push({ slide: index + 1, text: el.textContent.trim().slice(0, 70), issue: 'content outside safe area' });
        }
        if (el.scrollWidth > el.clientWidth + 2) issues.push({ slide: index + 1, issue: 'horizontal overflow', text: el.textContent.trim().slice(0, 70) });
      }
      for (const img of slide.querySelectorAll('img')) {
        if (!img.complete || !img.naturalWidth) issues.push({ slide: index + 1, issue: 'image not loaded', src: img.getAttribute('src') });
      }
      if (!slide.querySelector('aside.notes')) issues.push({ slide: index + 1, issue: 'missing speaker notes' });
    }
    Reveal.slide(0);
    return { slides: slides.length, main: window.courseMainSlideCount, issues };
  }, expected);
  await writeFile(resolve(build, `${id}-check.json`), JSON.stringify({ ...report, errors }, null, 2));
  if (errors.length || report.issues.length) throw new Error(JSON.stringify({ errors, issues: report.issues }, null, 2));
  // Reveal's print layout waits for load; fonts have already been cached above.
  await page.goto(`${url}?print-pdf`, { waitUntil: 'networkidle' });
  await page.evaluate(async () => { await window.courseReady; await document.fonts.ready; });
  await page.waitForFunction(() => document.querySelectorAll('.pdf-page').length === document.querySelectorAll('.slides section').length);
  await page.emulateMedia({ media: 'print' });
  // Reveal injects print CSS with !important: catch padding resets before PDF export.
  const printPadding = await page.evaluate(() => [...document.querySelectorAll('.slides section')].map(s => getComputedStyle(s).paddingLeft));
  if (printPadding.some(padding => parseFloat(padding) < 80)) throw new Error(`Print padding reset: ${printPadding}`);
  await page.pdf({ path: resolve(build, expected.pdf), printBackground: true,
    width: '1280px', height: '720px', preferCSSPageSize: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  if (errors.length) throw new Error(errors.join('\n'));
  console.log(`Built ${report.slides} slides (${report.main} main): ${output}/${id}/index.html`);
  console.log(`PDF: ${build}/${expected.pdf}`);
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
