// Public paths are relative to the build directory. Keep the source layout intact.
export function presentationPaths(id, presentation) {
  const lesson = presentation.lesson || id;
  const html = `html/${lesson}${presentation.variant ? `/${presentation.variant}` : ''}`;
  return { html, pdf: `pdf/${lesson}/${presentation.pdf}`, lesson };
}

const file = (source, name) => ({ source, name });
const journalStages = Array.from({ length: 6 }, (_, index) => file(
  `demos/lecture04-journal/stages/stage${index + 1}/journal.asm`,
  `journal-stage${index + 1}.asm`,
));

const byLesson = {
  lecture04: [
    file('demos/lecture04/materials/README.md', 'README.md'),
    file('demos/lecture04/materials/Dockerfile', 'Dockerfile'),
    file('demos/lecture04/memory.c', 'memory.c'),
    file('demos/lecture04/add_middle.asm', 'add_middle.asm'),
    file('demos/lecture04-journal/boot16.asm', 'boot16.asm'),
    ...journalStages,
  ],
  seminar04: [
    file('demos/seminar04/materials/README.md', 'README.md'),
    file('demos/seminar04/hello.asm', 'hello.asm'),
    file('demos/lecture04-journal/boot16.asm', 'boot16.asm'),
    file('demos/lecture04-journal/stages/stage6/journal.asm', 'journal.asm'),
    file('demos/seminar04/memory.c', 'memory.c'),
    file('demos/seminar04/memory.gdb', 'memory.gdb'),
  ],
  'seminar04/factorial': [
    file('demos/seminar04/factorial/materials/README.md', 'README.md'),
    file('demos/seminar04/factorial/materials/input.txt', 'input.txt'),
  ],
};

export function studentMaterials(lesson) {
  return byLesson[lesson] || [];
}
