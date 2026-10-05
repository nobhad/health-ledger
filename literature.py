"""
Journal lookup: the one module in the app that reaches the internet.

A lookup is something the person presses. It sends the words they searched for
(or one PubMed id) to Europe PMC's public search, plus fixed parameters, and
nothing from their records: no cookies, no account, no email address. The
User-Agent says only which app and version is asking.

"Reputable" is a query, not a judgement: results are limited to MEDLINE-indexed
articles (SRC:MED), which leaves preprints out, and no search term can cancel
that filter. The words must be in the title or the abstract, and the index is
asked for the most-cited matches. Its own default order was tried first, on
2026-10-05: for "CYP2D6 codeine" it returned 25 articles, most of them months
old with no citations, and none of the three clinical guidelines on exactly
that pair. Searching every field and sorting by citations found the guidelines
but put an atrial fibrillation guideline that merely mentions the words above
them. Title-or-abstract, most cited first, put the guidelines on top for each
of four terms tried.

What comes back is then ordered guidelines first, then meta-analyses,
systematic reviews and reviews, then everything else, each group by how often
it has been cited, and each one says what kind of article it is. Most-cited
favours older work: a guideline revised last year sits below the one it
replaced until the citations catch up, which is why the year is shown.

Abstracts arrive with HTML in them. They are reduced to plain text here, before
anything is stored; templates escape it on the way out.

Everything that can go wrong on the way is a LookupFailed whose message is a
sentence for the screen. Parsing is pure, so tests feed it a made-up response.
"""

import re
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

import requests

import config

SEARCH_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
REQUEST_TIMEOUT_SECONDS = 10
MAX_TERM_LENGTH = 200
PAGE_SIZE = 25
SOURCE_FILTER = 'SRC:MED'
SORT_MOST_CITED = 'CITED desc'

KIND_GUIDELINE = 'Guideline'
KIND_META_ANALYSIS = 'Meta-analysis'
KIND_SYSTEMATIC_REVIEW = 'Systematic review'
KIND_REVIEW = 'Review'
KIND_STUDY = 'Study'

# Most trusted first. (kind, lower-case phrase a publication type contains.)
KIND_ORDER = [
    (KIND_GUIDELINE, 'guideline'),
    (KIND_META_ANALYSIS, 'meta-analysis'),
    (KIND_SYSTEMATIC_REVIEW, 'systematic review'),
    (KIND_REVIEW, 'review'),
]
KIND_RANK = {kind: rank for rank, (kind, _) in enumerate(KIND_ORDER)}
KIND_RANK[KIND_STUDY] = len(KIND_ORDER)

BLOCK_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'br', 'li'}
PARAGRAPH_BREAK = '\n\n'

DOI_URL = 'https://doi.org/{doi}'
PUBMED_URL = 'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'

MESSAGE_OFFLINE = ('Could not reach the journal index. Check your internet connection and try '
                   'again. Nothing was saved.')
MESSAGE_TIMED_OUT = ('The journal index took too long to answer. Try again in a moment. '
                     'Nothing was saved.')
MESSAGE_ERROR = ('The journal index answered with an error. Try again later. '
                 'Nothing was saved.')
MESSAGE_UNREADABLE = ('The journal index answered with something this app could not read. '
                      'Try again later. Nothing was saved.')


class LookupFailed(Exception):
    """A lookup did not complete. The message is a sentence for a non-technical reader."""


@dataclass
class Article:
    title: str
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    publication_types: List[str] = field(default_factory=list)
    cited_by: int = 0
    kind: str = KIND_STUDY

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class _TextExtractor(HTMLParser):
    """Collects text, turning block-level tags into paragraph breaks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append(PARAGRAPH_BREAK)

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self.parts.append(PARAGRAPH_BREAK)

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(markup: str) -> str:
    """Tags removed, entities decoded, block tags turned into paragraph breaks."""
    extractor = _TextExtractor()
    extractor.feed(markup or '')
    extractor.close()
    text = ''.join(extractor.parts)
    # A break marker is the only newline source worth keeping; stray newlines are spaces.
    text = text.replace(PARAGRAPH_BREAK, '\x00')
    text = re.sub(r'\s+', ' ', text)
    paragraphs = [p.strip() for p in text.split('\x00')]
    return PARAGRAPH_BREAK.join(p for p in paragraphs if p).strip()


def _sanitise_term(term: str) -> str:
    if not isinstance(term, str):
        raise ValueError('Enter something to search for.')
    term = term.strip()
    if not term:
        raise ValueError('Enter something to search for.')
    if len(term) > MAX_TERM_LENGTH:
        raise ValueError(f'Search for {MAX_TERM_LENGTH} characters or fewer.')
    for character in '():':
        term = term.replace(character, ' ')
    if term.count('"') % 2:
        term = term.replace('"', ' ')
    term = re.sub(r'\s+', ' ', term).strip()
    if not term.strip('" '):
        raise ValueError('Enter something to search for.')
    return term


def _request_params(query: str, sort: Optional[str] = None) -> Dict[str, str]:
    params = {'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': str(PAGE_SIZE)}
    if sort:
        params['sort'] = sort
    return params


def build_search_request(term: str) -> Tuple[str, Dict[str, str]]:
    """The URL and parameters for a search. No term can cancel the source filter."""
    term = _sanitise_term(term)
    query = f'(TITLE:({term}) OR ABSTRACT:({term})) AND {SOURCE_FILTER}'
    return SEARCH_URL, _request_params(query, sort=SORT_MOST_CITED)


def build_id_request(pubmed_id: str) -> Tuple[str, Dict[str, str]]:
    """The URL and parameters for one article by PubMed id (digits only)."""
    pubmed_id = str(pubmed_id).strip()
    if not (pubmed_id.isascii() and pubmed_id.isdigit()):
        raise ValueError('A PubMed id is digits only.')
    return SEARCH_URL, _request_params(f'EXT_ID:{pubmed_id} AND {SOURCE_FILTER}')


def _kind(publication_types: List[str]) -> str:
    lowered = [t.lower() for t in publication_types]
    for kind, phrase in KIND_ORDER:
        if any(phrase in t for t in lowered):
            return kind
    return KIND_STUDY


def _clean(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    value = plain_text(value).replace('\n', ' ').strip().rstrip('.').strip()
    return value or None


def _year(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _count(value: Any) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _article(item: Dict[str, Any]) -> Optional[Article]:
    title = _clean(item.get('title'))
    if not title:
        return None
    journal_info = item.get('journalInfo')
    journal = None
    if isinstance(journal_info, dict) and isinstance(journal_info.get('journal'), dict):
        journal = _clean(journal_info['journal'].get('title'))
    types = (item.get('pubTypeList') or {}).get('pubType') if isinstance(item.get('pubTypeList'), dict) else None
    publication_types = [t for t in types if isinstance(t, str)] if isinstance(types, list) else []
    pubmed_id = str(item['pmid']).strip() if item.get('pmid') else None
    doi = str(item['doi']).strip() if item.get('doi') else None
    if doi:
        url = DOI_URL.format(doi=doi)
    elif pubmed_id:
        url = PUBMED_URL.format(pmid=pubmed_id)
    else:
        url = None
    abstract = item.get('abstractText')
    abstract = plain_text(abstract) if isinstance(abstract, str) else ''
    return Article(
        title=title,
        authors=_clean(item.get('authorString')),
        journal=journal,
        year=_year(item.get('pubYear')),
        pubmed_id=pubmed_id,
        doi=doi,
        url=url,
        abstract=abstract or None,
        publication_types=publication_types,
        cited_by=_count(item.get('citedByCount')),
        kind=_kind(publication_types),
    )


def parse(payload: Dict[str, Any]) -> List[Article]:
    """Articles from a Europe PMC response, in kind order, then most cited first."""
    if not isinstance(payload, dict) or not isinstance(payload.get('resultList'), dict):
        raise LookupFailed(MESSAGE_UNREADABLE)
    items = payload['resultList'].get('result') or []
    if not isinstance(items, list):
        raise LookupFailed(MESSAGE_UNREADABLE)
    articles = [a for a in (_article(i) for i in items if isinstance(i, dict)) if a]
    articles.sort(key=lambda a: (KIND_RANK[a.kind], -a.cited_by))
    return articles


def _get(url: str, params: Dict[str, str]) -> List[Article]:
    headers = {'User-Agent': f'HealthLedger/{config.APP_VERSION}', 'Accept': 'application/json'}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout:
        raise LookupFailed(MESSAGE_TIMED_OUT) from None
    except requests.ConnectionError:
        raise LookupFailed(MESSAGE_OFFLINE) from None
    except requests.HTTPError:
        raise LookupFailed(MESSAGE_ERROR) from None
    except requests.RequestException:
        raise LookupFailed(MESSAGE_OFFLINE) from None
    except ValueError:
        raise LookupFailed(MESSAGE_UNREADABLE) from None
    return parse(payload)


def search(term: str) -> List[Article]:
    """Look a term up. ValueError for a term that cannot be searched, LookupFailed otherwise."""
    url, params = build_search_request(term)
    return _get(url, params)


def fetch_by_pubmed_id(pubmed_id: str) -> Optional[Article]:
    """The article with this PubMed id, or None when the index has no such article."""
    url, params = build_id_request(pubmed_id)
    articles = _get(url, params)
    return articles[0] if articles else None
