"""
The folder of saved articles: one readable file each, in the data folder.

The database is the source of truth. Each file is a small self-contained HTML
page (no stylesheet, no script) so it opens by double-click, the link is
clickable, and nothing needs the app. A file is named from the first author,
year and a short title, then ends with the PubMed id (or the citation number
when there is none). That ending is what identifies the article: a changed
title renames the file, and the old one is found and removed by its ending.

The folder is read from `config` at call time, because `config.set_data_root`
re-points it while the app runs.
"""

import html
import re
from pathlib import Path
from typing import Dict, List, Optional

import config

TITLE_CHARACTERS = 60
SURNAME_CHARACTERS = 40
LINK_SCHEMES = ('http://', 'https://')
UNSAFE_NAME_CHARACTERS = re.compile(r'[^A-Za-z0-9._-]+')
DEFAULT_TITLE_PART = 'article'
UNASSIGNED_EXCERPT = 'Not assigned to a specialist yet'
NO_ABSTRACT = 'No abstract has been fetched yet.'


def _safe(part) -> str:
    return UNSAFE_NAME_CHARACTERS.sub('_', str(part)).strip('._')


def _suffix(article: Dict) -> str:
    """What every file name of this article ends with."""
    pubmed_id = article.get('pubmed_id')
    if pubmed_id:
        return f'_PMID{_safe(pubmed_id)}.html'
    return f'_ref{_safe(article.get("citation_number") or article.get("id") or 0)}.html'


def article_file_name(article: Dict) -> str:
    parts: List[str] = []
    authors = (article.get('authors') or '').strip()
    surname = _safe(authors.split(',')[0].strip().split(' ')[0][:SURNAME_CHARACTERS]) if authors else ''
    if surname:
        parts.append(surname)
    year = _safe(article.get('year') or '')
    if year:
        parts.append(year)
    title = _safe((article.get('title') or '')[:TITLE_CHARACTERS])
    parts.append(title or DEFAULT_TITLE_PART)
    return '_'.join(parts) + _suffix(article)


def _link(article: Dict) -> Optional[str]:
    # A stored url is whatever an earlier import wrote down. Only a web
    # address becomes something a double-click will follow.
    url = (article.get('url') or '').strip()
    if url.lower().startswith(LINK_SCHEMES):
        return url
    if article.get('doi'):
        return f'https://doi.org/{article["doi"]}'
    if article.get('pubmed_id'):
        return f'https://pubmed.ncbi.nlm.nih.gov/{article["pubmed_id"]}/'
    return None


def _specialist_label(specialty: str) -> str:
    return str(specialty).replace('_', ' ').title()


def article_html(article: Dict) -> str:
    esc = html.escape
    title = article.get('title') or DEFAULT_TITLE_PART.capitalize()
    body = [f'<h1>{esc(title)}</h1>']
    if article.get('authors'):
        body.append(f'<p>{esc(article["authors"])}</p>')
    published = ', '.join(str(p) for p in (article.get('journal'), article.get('year')) if p)
    if published:
        body.append(f'<p>{esc(published)}</p>')
    link = _link(article)
    if link:
        body.append(f'<p><a href="{esc(link)}">{esc(link)}</a></p>')

    body.append('<h2>Abstract</h2>')
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', article.get('abstract') or '')
                  if p.strip()]
    if paragraphs:
        body.extend(f'<p>{esc(p)}</p>' for p in paragraphs)
    else:
        body.append(f'<p>{esc(NO_ABSTRACT)}</p>')

    excerpts = article.get('excerpts') or []
    if excerpts:
        body.append('<h2>Your excerpts</h2>')
        for excerpt in excerpts:
            body.append(f'<blockquote>{esc(excerpt.get("excerpt_text") or "")}</blockquote>')
            specialties = excerpt.get('specialties') or []
            if specialties:
                names = ', '.join(_specialist_label(s) for s in specialties)
                body.append(f'<p>{esc("For: " + names)}</p>')
            else:
                body.append(f'<p>{esc(UNASSIGNED_EXCERPT)}</p>')

    body.append(f'<p>{esc(config.DOCUMENT_DISCLAIMER)}</p>')
    lines = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="UTF-8">',
             f'<title>{esc(title)}</title>', '</head>', '<body>']
    return '\n'.join(lines + body + ['</body>', '</html>']) + '\n'


def _remove_matching(article: Dict) -> None:
    folder = Path(config.REFERENCES_DIR)
    if not folder.is_dir():
        return
    suffix = _suffix(article)
    for path in folder.iterdir():
        if path.is_file() and path.name.endswith(suffix):
            path.unlink(missing_ok=True)


def write_article_file(article: Dict) -> Path:
    folder = Path(config.REFERENCES_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    _remove_matching(article)
    path = folder / article_file_name(article)
    path.write_text(article_html(article), encoding='utf-8')
    return path


def remove_article_file(article: Dict) -> None:
    _remove_matching(article)
