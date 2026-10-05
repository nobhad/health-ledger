"""The folder of saved articles: one readable file each, named safely."""

import shutil
import tempfile
import unittest
from pathlib import Path

import config
import ledger_setup
import reference_files


def make_article(**overrides):
    article = {
        'id': 1,
        'citation_number': 7,
        'title': 'A made-up trial of an example thing',
        'authors': 'Example A, Sample B, Other C',
        'journal': 'Journal of Examples',
        'year': 2020,
        'doi': '10.1000/example',
        'pubmed_id': '10000001',
        'url': None,
        'abstract': 'First paragraph.\n\nSecond paragraph.',
        'excerpts': [],
    }
    article.update(overrides)
    return article


class ReferenceFilesTest(unittest.TestCase):
    def setUp(self):
        self.original = config.DATA_ROOT
        self.tmp = tempfile.mkdtemp()
        config.set_data_root(self.tmp)

    def tearDown(self):
        config.set_data_root(self.original)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def files(self):
        return sorted(p.name for p in config.REFERENCES_DIR.iterdir())


class FileNameTest(ReferenceFilesTest):
    def test_name_follows_the_pattern(self):
        name = reference_files.article_file_name(make_article())
        self.assertEqual(
            name, 'Example_2020_A_made-up_trial_of_an_example_thing_PMID10000001.html')

    def test_long_unsafe_title_is_bounded_and_safe(self):
        title = ('a/b:c ' * 60)
        name = reference_files.article_file_name(make_article(title=title))
        self.assertLessEqual(len(name), 120)
        self.assertRegex(name, r'^[A-Za-z0-9._-]+$')
        self.assertTrue(name.endswith('_PMID10000001.html'))

    def test_same_author_year_title_get_different_names(self):
        a = reference_files.article_file_name(make_article(pubmed_id='10000001'))
        b = reference_files.article_file_name(make_article(pubmed_id='10000002'))
        self.assertNotEqual(a, b)

    def test_no_pubmed_id_uses_citation_number(self):
        name = reference_files.article_file_name(
            make_article(pubmed_id=None, citation_number=42))
        self.assertTrue(name.endswith('_ref42.html'))
        other = reference_files.article_file_name(
            make_article(pubmed_id=None, citation_number=43))
        self.assertNotEqual(name, other)

    def test_missing_parts_are_left_out(self):
        name = reference_files.article_file_name(
            make_article(authors=None, year=None, title=None))
        self.assertEqual(name, 'article_PMID10000001.html')

    def test_path_characters_cannot_escape(self):
        name = reference_files.article_file_name(
            make_article(authors='../../Evil, X', title='../../etc/passwd'))
        self.assertNotIn('/', name)
        self.assertFalse(name.startswith('.'))


class HtmlTest(ReferenceFilesTest):
    def test_page_holds_title_link_abstract_and_excerpts(self):
        article = make_article(excerpts=[
            {'id': 1, 'excerpt_text': 'First paragraph.',
             'specialties': ['cardiologist', 'pharmacist']},
            {'id': 2, 'excerpt_text': 'Second paragraph.', 'specialties': []},
        ])
        page = reference_files.article_html(article)
        self.assertTrue(page.startswith('<!DOCTYPE html>'))
        self.assertIn('<meta charset="UTF-8">', page)
        self.assertIn('<h1>A made-up trial of an example thing</h1>', page)
        self.assertIn('Example A, Sample B, Other C', page)
        self.assertIn('Journal of Examples', page)
        self.assertIn('<a href="https://doi.org/10.1000/example">', page)
        self.assertIn('<h2>Abstract</h2>', page)
        self.assertIn('<p>First paragraph.</p>', page)
        self.assertIn('<p>Second paragraph.</p>', page)
        self.assertIn('<h2>Your excerpts</h2>', page)
        self.assertIn('<blockquote>First paragraph.</blockquote>', page)
        self.assertIn('For: Cardiologist, Pharmacist', page)
        self.assertIn('Not assigned to a specialist yet', page)
        self.assertIn(config.DOCUMENT_DISCLAIMER.replace("'", '&#x27;'), page)
        for forbidden in ('<style', '<script', 'stylesheet', 'style='):
            self.assertNotIn(forbidden, page)

    def test_link_order(self):
        self.assertIn('href="https://example.org/x"', reference_files.article_html(
            make_article(url='https://example.org/x')))
        self.assertIn('href="https://pubmed.ncbi.nlm.nih.gov/10000001/"',
                      reference_files.article_html(make_article(doi=None)))
        page = reference_files.article_html(make_article(doi=None, pubmed_id=None))
        self.assertNotIn('<a ', page)

    def test_only_a_web_address_becomes_a_link(self):
        """A stored url is whatever an earlier import wrote; a double-click follows it."""
        page = reference_files.article_html(
            make_article(url='javascript:alert(1)', doi=None, pubmed_id=None))
        self.assertNotIn('<a ', page)
        page = reference_files.article_html(make_article(url='file:///etc/hosts'))
        self.assertIn('href="https://doi.org/10.1000/example"', page)

    def test_a_long_first_author_is_bounded(self):
        name = reference_files.article_file_name(make_article(authors='X' * 300))
        self.assertLessEqual(len(name), 160)

    def test_no_abstract_and_no_excerpts(self):
        page = reference_files.article_html(make_article(abstract=None))
        self.assertIn('No abstract has been fetched yet', page)
        self.assertNotIn('Your excerpts', page)

    def test_script_in_title_is_escaped(self):
        page = reference_files.article_html(
            make_article(title='<script>alert(1)</script> & "q"'))
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('&amp;', page)

    def test_everything_else_is_escaped_too(self):
        page = reference_files.article_html(make_article(
            url='https://example.org/?a=1&b="2"',
            abstract='x < y & z',
            excerpts=[{'id': 1, 'excerpt_text': '<b>x</b>', 'specialties': ['<i>']}]))
        self.assertNotIn('<b>x</b>', page)
        self.assertNotIn('<i>', page)
        self.assertNotIn('href="https://example.org/?a=1&b="', page)
        self.assertIn('x &lt; y &amp; z', page)

    def test_sparse_article_does_not_raise(self):
        page = reference_files.article_html({'id': 3})
        self.assertIn('<h1>', page)


class WriteRemoveTest(ReferenceFilesTest):
    def test_write_creates_folder_and_file(self):
        shutil.rmtree(config.REFERENCES_DIR, ignore_errors=True)
        path = reference_files.write_article_file(make_article())
        self.assertIsInstance(path, Path)
        self.assertEqual(path.parent, config.REFERENCES_DIR)
        text = path.read_text(encoding='utf-8')
        self.assertIn('A made-up trial', text)

    def test_unicode_is_written_as_utf8(self):
        path = reference_files.write_article_file(make_article(abstract='café – ok'))
        self.assertIn('café – ok', path.read_text(encoding='utf-8'))

    def test_title_change_leaves_one_file(self):
        reference_files.write_article_file(make_article())
        reference_files.write_article_file(make_article(title='A different title'))
        self.assertEqual(len(self.files()), 1)
        self.assertIn('different_title', self.files()[0])

    def test_other_articles_are_left_alone(self):
        reference_files.write_article_file(make_article(pubmed_id='10000001'))
        reference_files.write_article_file(make_article(id=2, pubmed_id='10000002'))
        reference_files.write_article_file(make_article(id=3, pubmed_id=None, citation_number=5))
        self.assertEqual(len(self.files()), 3)

    def test_prefix_pmid_is_not_matched(self):
        reference_files.write_article_file(make_article(pubmed_id='110000001'))
        reference_files.write_article_file(make_article(pubmed_id='10000001'))
        self.assertEqual(len(self.files()), 2)

    def test_remove_deletes_and_is_quiet_when_gone(self):
        article = make_article()
        reference_files.write_article_file(article)
        reference_files.remove_article_file(article)
        self.assertEqual(self.files(), [])
        reference_files.remove_article_file(article)

    def test_remove_is_quiet_when_folder_missing(self):
        shutil.rmtree(config.REFERENCES_DIR, ignore_errors=True)
        reference_files.remove_article_file(make_article())
        self.assertFalse(config.REFERENCES_DIR.exists())

    def test_follows_set_data_root(self):
        other = tempfile.mkdtemp()
        try:
            config.set_data_root(other)
            path = reference_files.write_article_file(make_article())
            self.assertTrue(str(path).startswith(str(Path(other).resolve())))
        finally:
            config.set_data_root(self.tmp)
            shutil.rmtree(other, ignore_errors=True)


class SetupTest(ReferenceFilesTest):
    def test_ensure_data_directories_creates_references(self):
        self.assertFalse(config.REFERENCES_DIR.exists())
        ledger_setup.ensure_data_directories()
        self.assertTrue(config.REFERENCES_DIR.is_dir())
        self.assertEqual(config.REFERENCES_DIR, config.DATA_ROOT / 'references')


if __name__ == '__main__':
    unittest.main()
