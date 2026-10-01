import { cp, mkdir, rm } from 'node:fs/promises';
import { basename, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { studentMaterials } from './publication.mjs';

export async function publishMaterials(workspace, build, lesson) {
  const materials = studentMaterials(lesson);
  if (!materials.length) return;
  const names = materials.map(({ name }) => name);
  if (names.some(name => basename(name) !== name || name === '.' || name === '..') ||
      new Set(names).size !== names.length) {
    throw new Error(`Invalid student material names for ${lesson}`);
  }
  for (const format of ['html', 'pdf']) {
    const target = resolve(build, format, lesson, 'materials');
    // Replace only generated material directories; leave other build outputs alone.
    await rm(target, { recursive: true, force: true });
    await mkdir(target, { recursive: true });
    for (const { source, name } of materials) {
      await cp(resolve(workspace, source), resolve(target, name));
    }
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  await publishMaterials(process.cwd(), resolve(process.argv[2] || 'build'), process.argv[3] || 'seminar04');
}
