// Integration acceptance check: the actual PDF must contain one 16:9 page per slide.
import { readFile, access, readdir } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { presentationPaths, studentMaterials } from './publication.mjs';
const require = createRequire('/opt/slides/package.json');
const { PDFDocument } = require('pdf-lib');
const root = process.argv[2] || 'build';
const id = process.argv[3] || 'lecture02';
const presentations = JSON.parse(await readFile('slides/presentations.json', 'utf8'));
if (!Object.hasOwn(presentations, id)) throw new Error(`Unknown presentation: ${id}`);
const expected = presentations[id];
const paths = presentationPaths(id, expected);
const html = await readFile(`${root}/${paths.html}/index.html`, 'utf8').catch(() => '');
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
const pdf = await PDFDocument.load(await readFile(`${root}/${paths.pdf}`));
if (pdf.getPageCount() !== slides) throw new Error(`PDF: ${pdf.getPageCount()}, slides: ${slides}`);
for (const page of pdf.getPages()) {
  const { width, height } = page.getSize();
  if (Math.abs(width / height - 16 / 9) > 0.01) throw new Error('PDF is not 16:9');
}
await access(`${root}/html/vendor/reveal/dist/reveal.js`);
await access(`${root}/html/vendor/fonts/Carlito-Regular.ttf`);
const materials = studentMaterials(paths.lesson);
if (materials.length) {
  const names = materials.map(({ name }) => name).sort();
  for (const format of ['html', 'pdf']) {
    assert.deepEqual((await readdir(`${root}/${format}/${paths.lesson}/materials`)).sort(),
      names, `Unexpected ${format} materials for ${paths.lesson}`);
  }
}
for (const { name } of materials) {
  const htmlMaterial = `${root}/html/${paths.lesson}/materials/${name}`;
  const pdfMaterial = `${root}/pdf/${paths.lesson}/materials/${name}`;
  assert.deepEqual(await readFile(pdfMaterial), await readFile(htmlMaterial), `Different copies of ${name}`);
}
for (const format of ['html', 'pdf']) {
  for (const forbidden of ['demos/seminar04/teacher.md', 'demos/seminar04/solutions']) {
    if (await access(`${root}/${format}/${paths.lesson}/materials/${forbidden}`).then(() => true, () => false)) {
      throw new Error(`Teacher material published: ${forbidden}`);
    }
  }
}
if (materials.length && await access(`${root}/pdf/${paths.lesson}/materials/index.html`).then(() => true, () => false)) {
  throw new Error('HTML index published among PDF materials');
}
if (/(?:src|href)=["']https?:/.test(html)) throw new Error('Remote dependency in HTML');
console.log(`${id}: ${slides} slides, ${slides} PDF pages, 16:9, local assets — OK`);
