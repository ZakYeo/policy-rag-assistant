"""Bounded extraction that keeps source structure and never renders uploaded HTML."""
from html.parser import HTMLParser
from pathlib import Path
import re

MAX_CHARACTERS = 2_000_000
MAX_PAGES = 1000


class PolicyHtmlParser(HTMLParser):
    ignored = {'script', 'style', 'template', 'noscript', 'iframe', 'object', 'head', 'svg'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.parts = []
        self.sections = []
        self.heading = ''
        self.level = 0
        self.heading_tag = None
        self.heading_parts = []

    def flush(self):
        text = clean_text(''.join(self.parts))
        if text:
            self.sections.append({'text': text, 'heading': self.heading, 'level': self.level})
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored:
            self.hidden.append(tag)
        if self.hidden:
            return
        if re.fullmatch(r'h[1-6]', tag):
            self.flush()
            self.heading_tag = tag
            self.heading_parts = []
            self.level = int(tag[1])
        elif tag in {'p', 'div', 'section', 'article', 'li', 'br', 'tr'}:
            self.parts.append('\n\n')

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag == self.heading_tag:
            self.heading = clean_text(''.join(self.heading_parts))
            self.parts.extend([self.heading, '\n\n'])
            self.heading_tag = None
        elif tag in {'p', 'div', 'section', 'article', 'li', 'tr'}:
            self.parts.append('\n\n')

    def handle_data(self, data):
        if not self.hidden:
            (self.heading_parts if self.heading_tag else self.parts).append(data)


def clean_text(text):
    text = re.sub(r'[^\S\n]+', ' ', text.replace('\r\n', '\n').replace('\r', '\n'))
    return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)*', '\n\n', text).strip()


def extract_policy(path: Path, format: str):
    sections = []
    if format == 'pdf':
        import fitz
        try:
            with fitz.open(path) as document:
                if not document.is_pdf or document.needs_pass or document.page_count > MAX_PAGES:
                    raise ValueError('Use an unencrypted PDF with at most 1,000 pages.')
                total = 0
                for number, page in enumerate(document, 1):
                    text = clean_text(page.get_text('text'))
                    total += len(text)
                    if total > MAX_CHARACTERS:
                        raise ValueError('The extracted policy exceeds 2 million characters.')
                    if text:
                        sections.append({'text': text, 'page_number': number, 'location': f'Page {number}', 'heading': '', 'level': 0})
        except (RuntimeError, fitz.FileDataError) as exc:
            raise ValueError('This PDF could not be read. Upload a valid, unencrypted PDF.') from exc
    else:
        try:
            text = path.read_text(encoding='utf-8-sig')
        except UnicodeError as exc:
            raise ValueError('HTML and text policies must use UTF-8 encoding.') from exc
        if any(ord(char) < 32 and char not in '\n\r\t' for char in text):
            raise ValueError('This file contains binary data rather than policy text.')
        if len(text) > MAX_CHARACTERS:
            raise ValueError('The extracted policy exceeds 2 million characters.')
        if format in {'html', 'htm'}:
            if not re.search(r'<(?:html|body|h[1-6]|p|div|section)\b', text, re.I):
                raise ValueError('This file does not contain a readable HTML document.')
            parser = PolicyHtmlParser()
            parser.feed(text)
            parser.close()
            parser.flush()
            sections = [{**section, 'page_number': 1, 'location': section['heading'] or f'Section {index + 1}'}
                        for index, section in enumerate(parser.sections)]
        else:
            sections = [{'text': clean_text(text), 'page_number': 1, 'location': 'Text', 'heading': '', 'level': 0}]
    if not sections or not any(section['text'].strip() for section in sections):
        raise ValueError('No readable text was found. Scanned PDFs need OCR before upload.')
    return sections
