import assert from 'node:assert/strict';
import { test } from 'node:test';
import { access } from 'node:fs/promises';
import { presentationPaths, studentMaterials } from './publication.mjs';

test('main and alternate decks share a lesson but keep separate HTML and PDF trees', () => {
  assert.deepEqual(presentationPaths('lecture04', { pdf: 'lecture04-slides.pdf' }), {
    html: 'html/lecture04', pdf: 'pdf/lecture04/lecture04-slides.pdf', lesson: 'lecture04',
  });
  assert.deepEqual(presentationPaths('lecture04-journal', {
    lesson: 'lecture04', variant: 'journal', pdf: 'lecture04-journal.pdf',
  }), {
    html: 'html/lecture04/journal', pdf: 'pdf/lecture04/lecture04-journal.pdf', lesson: 'lecture04',
  });
  assert.deepEqual(presentationPaths('lecture02-original', {
    lesson: 'lecture02', variant: 'original', pdf: 'lecture02-original.pdf',
  }).html, 'html/lecture02/original');
});

test('student materials contain everything needed for seminar instructions, without solutions', async () => {
  const materials = studentMaterials('seminar04');
  assert.deepEqual(materials.map(file => file.name).sort(), [
    'README.md', 'hello.asm', 'boot16.asm', 'journal.asm', 'memory.c', 'memory.gdb',
  ].sort());
  assert.deepEqual(materials.find(file => file.name === 'journal.asm'), {
    source: 'demos/lecture04-journal/stages/stage6/journal.asm', name: 'journal.asm',
  });
  assert.ok(materials.every(file => !file.name.includes('/') &&
    !/(?:teacher|solution|check|test|prepare|__pycache__)/i.test(file.source)));
  await Promise.all(materials.map(file => access(file.source)));
});

test('basic factorial variant ships input data and instructions but no completed source', async () => {
  const materials = studentMaterials('seminar04/factorial');
  assert.deepEqual(materials.map(file => file.name).sort(), ['README.md', 'input.txt']);
  assert.ok(materials.every(file => !/(?:reference|teacher|solution)/i.test(file.source)));
  await Promise.all(materials.map(file => access(file.source)));
});

test('lecture materials include C/NASM examples and all six journal stages', async () => {
  const materials = studentMaterials('lecture04');
  assert.deepEqual(materials.map(file => file.name).sort(), [
    'README.md', 'Dockerfile', 'memory.c', 'add_middle.asm', 'boot16.asm',
    ...Array.from({ length: 6 }, (_, index) => `journal-stage${index + 1}.asm`),
  ].sort());
  for (let stage = 1; stage <= 6; stage++) {
    assert.deepEqual(materials.find(file => file.name === `journal-stage${stage}.asm`), {
      source: `demos/lecture04-journal/stages/stage${stage}/journal.asm`,
      name: `journal-stage${stage}.asm`,
    });
  }
  await Promise.all(materials.map(file => access(file.source)));
  assert.deepEqual(studentMaterials('lecture02'), []);
});
