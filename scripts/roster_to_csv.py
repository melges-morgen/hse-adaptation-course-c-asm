"""Extract the colour-coded student roster from the course spreadsheet."""

import argparse
import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

NS = {
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
}
FIELDS = ('student_id', 'group', 'subgroup', 'full_name')


def read_ods(path):
    with zipfile.ZipFile(path) as archive:
        content = ET.fromstring(archive.read('content.xml'))
        styles = ET.fromstring(archive.read('styles.xml'))
    colors = {}
    parents = {}
    for document in (styles, content):
        for style in document.findall('.//style:style', NS):
            name = style.get(f'{{{NS["style"]}}}name')
            parents[name] = style.get(f'{{{NS["style"]}}}parent-style-name')
            properties = style.find('style:table-cell-properties', NS)
            if properties is not None:
                colors[name] = properties.get(f'{{{NS["fo"]}}}background-color')

    def background(style):
        visited = set()
        while style and style not in visited:
            visited.add(style)
            if colors.get(style):
                return colors[style].lower()
            style = parents.get(style)
        return None

    sheet = content.find('.//table:table', NS)
    if sheet is None:
        raise ValueError('В ODS нет листа со студентами')
    roster = []
    headers = None
    counters = Counter()
    seen = set()
    for row in sheet.findall('table:table-row', NS):
        cells = []
        for cell in row:
            if cell.tag not in (f'{{{NS["table"]}}}table-cell', f'{{{NS["table"]}}}covered-table-cell'):
                continue
            value = '\n'.join(''.join(p.itertext()).strip() for p in cell.findall('text:p', NS)).strip()
            style = cell.get(f'{{{NS["table"]}}}style-name')
            repeat = int(cell.get(f'{{{NS["table"]}}}number-columns-repeated', '1'))
            if headers is None and repeat > 100:
                repeat = 1
            cells.extend([(value, background(style))] * repeat)
        if headers is None:
            headers = [cell[0] for cell in cells if re.fullmatch(r'БПИ\d+', cell[0])]
            if not headers:
                raise ValueError('Не найдены заголовки групп БПИ')
            continue
        for index, group in enumerate(headers):
            if index >= len(cells) or not cells[index][0]:
                continue
            name, color = cells[index]
            if (group, name) in seen:
                raise ValueError(f'Дубликат студента: {group} {name}')
            seen.add((group, name))
            counters[group] += 1
            roster.append(dict(student_id=f'BPI{group[3:]}-{counters[group]:03}',
                               group=group, subgroup='1' if color == '#d9ead3' else '2', full_name=name))
    return roster


def write_roster(path, roster):
    path = Path(path)
    if path.exists():
        with path.open(encoding='utf-8', newline='') as inp:
            existing = {(s['group'], s['full_name']): s['student_id'] for s in csv.DictReader(inp)}
        used = set(existing.values())
        next_ids = Counter()
        for code in used:
            match = re.fullmatch(r'BPI(\d+)-(\d+)', code)
            if match:
                next_ids[match[1]] = max(next_ids[match[1]], int(match[2]))
        for student in roster:
            key = student['group'], student['full_name']
            if key in existing:
                student['student_id'] = existing[key]
            else:
                suffix = student['group'][3:]
                next_ids[suffix] += 1
                student['student_id'] = f'BPI{suffix}-{next_ids[suffix]:03}'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(roster)


def main():
    parser = argparse.ArgumentParser(description='Экспорт пофамильного списка из ODS в UTF-8 CSV')
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    roster = read_ods(args.input)
    write_roster(args.output, roster)
    print(f'Записано {len(roster)} студентов в {args.output}')


if __name__ == '__main__':
    main()
