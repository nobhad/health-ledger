#!/usr/bin/env python3
"""
A specialist's document carries the journal excerpts assigned to that
specialist, each with the article's title and a printable link.
"""

import inspect
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import GeneticProfileDB
from pdf_generator import generate_doctor_pdf
from scripts.generate_doctor_document import generate_doctor_document_html

REPO = Path(__file__).parent.parent
HEADING = '<h2>From the literature</h2>'
ABSTRACT = 'Alpha beta gamma & delta < epsilon. Zeta eta theta.'


class TestDocumentReferences(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = GeneticProfileDB(self.temp_db.name)
        self.db.add_gene('TEST', 'Test Gene', '1')

    def tearDown(self):
        self.db.close()
        for suffix in ('', '-shm', '-wal'):
            path = self.temp_db.name + suffix
            if os.path.exists(path):
                os.unlink(path)

    def add_excerpt(self, specialties, text='Alpha beta gamma', **article):
        data = {'title': 'Example Title', 'authors': 'Example A, Sample B',
                'journal': 'Example Journal', 'year': 2020,
                'abstract': ABSTRACT}
        data.update(article)
        citation_id = self.db.save_article(data)
        excerpt_id = self.db.add_excerpt(citation_id, text)
        self.db.set_excerpt_specialties(excerpt_id, specialties)
        return excerpt_id

    def document(self, specialty='cardiologist', **kwargs):
        return generate_doctor_document_html(self.db, specialty, **kwargs)

    def source_line(self, page):
        match = re.search(r'<p class="literature-source">(.*?)</p>', page, re.S)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_cardiologist_document_carries_its_excerpt_title_and_link(self):
        self.add_excerpt(['cardiologist'], doi='10.1000/example', pubmed_id='10000001')
        page = self.document()
        self.assertIn(HEADING, page)
        self.assertIn('<blockquote class="literature-excerpt">Alpha beta gamma</blockquote>', page)
        self.assertIn('Example Title', page)
        self.assertIn('<em>Example Journal</em>', page)
        self.assertIn('<a href="https://doi.org/10.1000/example">https://doi.org/10.1000/example</a>', page)
        self.assertIn('literature-note', page)
        self.assertIn('Passages quoted word for word from the abstracts of published '
                      'articles, chosen by the patient.', page)

    def test_excerpt_for_another_specialty_is_left_out(self):
        self.add_excerpt(['psychiatrist'])
        page = self.document('cardiologist')
        self.assertNotIn(HEADING, page)
        self.assertNotIn('Example Title', page)
        self.assertIn(HEADING, self.document('psychiatrist'))

    def test_include_references_false_leaves_the_heading_out(self):
        self.add_excerpt(['cardiologist'])
        self.assertNotIn('From the literature', self.document(include_references=False))

    def test_no_excerpts_no_heading(self):
        self.assertNotIn('From the literature', self.document())

    def test_text_is_escaped(self):
        self.add_excerpt(['cardiologist'], text='gamma & delta < epsilon',
                         title='Fish & <b>Chips</b>')
        page = self.document()
        self.assertIn('gamma &amp; delta &lt; epsilon', page)
        self.assertIn('Fish &amp; &lt;b&gt;Chips&lt;/b&gt;', page)
        self.assertNotIn('<b>Chips', page)

    def test_section_sits_before_the_disclaimer(self):
        self.add_excerpt(['cardiologist'])
        page = self.document()
        self.assertLess(page.index(HEADING), page.index('footer-disclaimer'))

    def test_doi_wins(self):
        self.add_excerpt(['cardiologist'], doi='10.1000/example', pubmed_id='10000001',
                         url='https://example.org/x')
        line = self.source_line(self.document())
        self.assertIn('href="https://doi.org/10.1000/example"', line)
        self.assertNotIn('pubmed.ncbi', line)

    def test_pubmed_when_no_doi(self):
        self.add_excerpt(['cardiologist'], pubmed_id='10000001', url='https://example.org/x')
        line = self.source_line(self.document())
        self.assertIn('<a href="https://pubmed.ncbi.nlm.nih.gov/10000001/">'
                      'https://pubmed.ncbi.nlm.nih.gov/10000001/</a>', line)

    def test_stored_http_url_is_the_last_resort(self):
        self.add_excerpt(['cardiologist'], url='https://example.org/x')
        self.assertIn('<a href="https://example.org/x">https://example.org/x</a>',
                      self.source_line(self.document()))

    def test_unsafe_url_produces_no_link(self):
        self.add_excerpt(['cardiologist'], url='javascript:alert(1)')
        page = self.document()
        self.assertIn(HEADING, page)
        self.assertNotIn('<a', self.source_line(page))
        self.assertNotIn('javascript:', page)

    def test_no_journal_no_year_leaves_no_dangling_punctuation(self):
        self.add_excerpt(['cardiologist'], journal=None, year=None)
        line = self.source_line(self.document())
        self.assertNotIn(', .', line)
        self.assertNotIn('. ,', line)
        self.assertFalse(line.endswith(', '))
        self.assertFalse(line.rstrip().endswith(','))
        self.assertNotIn('<em>', line)
        self.assertEqual(line.strip(), 'Example Title.')

    def test_source_printed_under_each_excerpt_of_the_same_article(self):
        citation_id = self.db.save_article({'title': 'Example Title', 'journal': 'J',
                                            'year': 2020, 'abstract': ABSTRACT})
        for text in ('Alpha beta gamma', 'Zeta eta theta'):
            excerpt_id = self.db.add_excerpt(citation_id, text)
            self.db.set_excerpt_specialties(excerpt_id, ['cardiologist'])
        page = self.document()
        self.assertEqual(page.count('class="literature-source"'), 2)
        self.assertEqual(page.count('class="literature-excerpt"'), 2)

    def test_an_article_with_no_title_still_gets_its_link(self):
        """Citations written by older imports can have no title at all."""
        self.add_excerpt(['cardiologist'], pubmed_id='10000001')
        self.db.conn.execute('UPDATE citations SET title = NULL')
        self.db.conn.commit()
        line = self.source_line(self.document())
        self.assertTrue(line.startswith('<em>Example Journal</em>, 2020.'), line)
        self.assertIn('https://pubmed.ncbi.nlm.nih.gov/10000001/', line)

    def test_the_printed_link_is_not_repeated(self):
        """print.css appends the address after every link; here it is the link text."""
        sheet = (REPO / 'static' / 'css' / 'print.css').read_text()
        self.assertRegex(sheet, r'\.literature-source a:after\s*\{\s*content:\s*none')

    def test_pdf_generator_accepts_include_references(self):
        self.assertIn('include_references', inspect.signature(generate_doctor_pdf).parameters)
        self.assertTrue(inspect.signature(generate_doctor_pdf)
                        .parameters['include_references'].default)

    def test_both_document_stylesheets_style_the_quote(self):
        for name in ('pdf.css', 'print.css'):
            css = (REPO / 'static' / 'css' / name).read_text()
            self.assertIn('.literature-excerpt', css, name)
            self.assertIn('.literature-source', css, name)


if __name__ == '__main__':
    unittest.main()
