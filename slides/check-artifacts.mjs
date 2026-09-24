// Integration acceptance check: the actual PDF must contain one 16:9 page per slide.
import { readFile, access } from 'node:fs/promises';
import { createRequire } from 'node:module';
const require = createRequire('/opt/slides/package.json');
const { PDFDocument } = require('pdf-lib');
const root = process.argv[2] || 'build';
const id = process.argv[3] || 'lecture02';
const presentations = JSON.parse(await readFile('slides/presentations.json', 'utf8'));
if (!Object.hasOwn(presentations, id)) throw new Error(`Unknown presentation: ${id}`);
const expected = presentations[id];
const html = await readFile(`${root}/slides/${id}/index.html`, 'utf8').catch(() => '');
if (!/<!doctype html>/i.test(html) || !/<title>[^<]+<\/title>/.test(html)) {
  throw new Error(`Missing built lecture HTML: ${id}`);
}
const slides = (html.match(/<section\b/g) || []).length;
if (slides !== expected.slides) throw new Error(`Expected ${expected.slides} slides, got ${slides}`);
if (expected.sourceSequence) {
  const sequence = [...html.matchAll(/data-source-slide="(\d+)"/g)].map(match => Number(match[1]));
  if (sequence.length !== slides || sequence.some((number, index) => number !== index + 1)) {
    throw new Error('PPTX slide order is not preserved');
  }
}
const pdf = await PDFDocument.load(await readFile(`${root}/${expected.pdf}`));
if (pdf.getPageCount() !== slides) throw new Error(`PDF: ${pdf.getPageCount()}, slides: ${slides}`);
for (const page of pdf.getPages()) {
  const { width, height } = page.getSize();
  if (Math.abs(width / height - 16 / 9) > 0.01) throw new Error('PDF is not 16:9');
}
await access(`${root}/slides/vendor/reveal/dist/reveal.js`);
await access(`${root}/slides/vendor/fonts/Carlito-Regular.ttf`);
if (/(?:src|href)=["']https?:/.test(html)) throw new Error('Remote dependency in HTML');
console.log(`${id}: ${slides} slides, ${slides} PDF pages, 16:9, local assets — OK`);
