"""Apply the course handbook theme and a readable title to TeX4ht HTML."""

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class HeadingText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


path = Path(sys.argv[1])
page = path.read_text(encoding='utf-8')
heading = re.search(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', page, re.S)
if not heading or '<title></title>' not in page:
    raise SystemExit(f'No heading or empty title to update in {path}')
parser = HeadingText()
parser.feed(heading.group())
title = ' '.join(''.join(parser.parts).split())
page = page.replace('<title></title>', '<title>' + html.escape(title) + '</title>', 1)
page = page.replace('</head>', "<link href='course.css' rel='stylesheet' type='text/css' />\n</head>", 1)
page = re.sub(r"<h[1-6] class='likesectionHead'><a id='[^']*'></a></h[1-6]>", '', page)
path.write_text(page, encoding='utf-8')
