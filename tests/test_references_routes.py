"""
Routes for the References feature, with the journal lookup patched.

Fixture data is made up. Nothing here touches the network: literature.search and
literature.fetch_by_pubmed_id are replaced, and each test asserts the mock was
called so the patch is known to have taken.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import config  # noqa: E402
import literature  # noqa: E402
from app import app  # noqa: E402
from database_manager import GeneticProfileDB  # noqa: E402

ABSTRACT = 'Aim\n\nWe tested nothing in a made-up trial. Results were unremarkable.'


def make_result(**overrides):
    fields = dict(title='A made-up trial of nothing', authors='Example A, Sample B',
                  journal='Journal of Examples', year=2020, pubmed_id='10000001',
                  doi='10.0000/example.1', url='https://doi.org/10.0000/example.1',
                  abstract=ABSTRACT, cited_by=3)
    fields.update(overrides)
    return literature.Article(**fields)


def save_body(**overrides):
    body = make_result().as_dict()
    body.update(overrides)
    return body


class ReferencesRoutesTestCase(unittest.TestCase):

    def setUp(self):
        self._original_root = config.DATA_ROOT
        self._original_db_path = config.DB_PATH
        self.root = tempfile.mkdtemp()
        config.set_data_root(self.root)
        self.db_path = os.path.join(self.root, 'test.db')
        GeneticProfileDB(self.db_path).close()
        config.DB_PATH = Path(self.db_path)
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        config.set_data_root(self._original_root)
        config.DB_PATH = self._original_db_path
        shutil.rmtree(self.root, ignore_errors=True)

    def save(self, **overrides):
        response = self.client.post('/api/references', json=save_body(**overrides))
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()['id']

    def citation_count(self):
        db = GeneticProfileDB(self.db_path)
        try:
            return db.conn.execute('SELECT COUNT(*) FROM citations').fetchone()[0]
        finally:
            db.close()

    def files(self):
        folder = Path(config.REFERENCES_DIR)
        return sorted(folder.iterdir()) if folder.is_dir() else []

    def assertRefused(self, response, status):
        self.assertEqual(response.status_code, status, response.get_json())
        data = response.get_json()
        self.assertIs(data['success'], False)
        self.assertTrue(data['message'])
        return data['message']


class TestIsolation(ReferencesRoutesTestCase):

    def test_references_folder_is_inside_the_temp_root(self):
        self.assertIn(Path(self.root).resolve(), Path(config.REFERENCES_DIR).resolve().parents)


class TestPage(ReferencesRoutesTestCase):

    def test_page_renders(self):
        response = self.client.get('/references')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'References', response.data)


class TestSearch(ReferencesRoutesTestCase):

    def test_results_carry_saved_id_and_nothing_is_saved(self):
        self.save()
        found = [make_result(), make_result(title='Another', pubmed_id='10000002',
                                            doi='10.0000/example.2')]
        with patch('literature.search', return_value=found) as search:
            response = self.client.post('/api/references/search', json={'term': 'nothing'})
        search.assert_called_once_with('nothing')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['results'][0]['title'], 'A made-up trial of nothing')
        self.assertEqual(data['results'][0]['kind'], 'Study')
        self.assertIsNotNone(data['results'][0]['saved_id'])
        self.assertIsNone(data['results'][1]['saved_id'])
        self.assertEqual(self.citation_count(), 1)

    def test_value_error_is_400_with_its_message(self):
        with patch('literature.search', side_effect=ValueError('Enter something to search for.')) as search:
            response = self.client.post('/api/references/search', json={'term': ''})
        search.assert_called_once()
        self.assertEqual(self.assertRefused(response, 400), 'Enter something to search for.')

    def test_lookup_failure_is_502_and_saves_nothing(self):
        with patch('literature.search', side_effect=literature.LookupFailed('Could not reach it.')) as search:
            response = self.client.post('/api/references/search', json={'term': 'nothing'})
        search.assert_called_once()
        self.assertEqual(self.assertRefused(response, 502), 'Could not reach it.')
        self.assertEqual(self.citation_count(), 0)

    def test_body_that_is_not_an_object_is_400(self):
        with patch('literature.search') as search:
            response = self.client.post('/api/references/search', data='not json',
                                        content_type='text/plain')
            self.assertRefused(response, 400)
            self.assertRefused(self.client.post('/api/references/search', json=['x']), 400)
        search.assert_not_called()

    def test_unexpected_error_is_a_plain_500(self):
        with patch('literature.search', side_effect=RuntimeError('secret internal detail')):
            response = self.client.post('/api/references/search', json={'term': 'nothing'})
        message = self.assertRefused(response, 500)
        self.assertTrue(message.startswith('Something went wrong'))
        self.assertNotIn('secret', message)


class TestSave(ReferencesRoutesTestCase):

    def test_save_returns_id_and_article_and_writes_a_file(self):
        response = self.client.post('/api/references', json=save_body())
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['article']['title'], 'A made-up trial of nothing')
        self.assertEqual(data['article']['abstract'], ABSTRACT)
        self.assertEqual(len(self.files()), 1)

    def test_same_pubmed_id_twice_is_one_id(self):
        first = self.save()
        second = self.save(title='Retitled')
        self.assertEqual(first, second)
        self.assertEqual(self.citation_count(), 1)
        self.assertEqual(len(self.files()), 1)

    def test_markup_in_the_abstract_is_stripped(self):
        article_id = self.save(abstract='<p>We <b>tested</b> nothing.</p>')
        article = self.client.get(f'/api/references/{article_id}').get_json()['article']
        self.assertEqual(article['abstract'], 'We tested nothing.')
        self.assertNotIn('<b>', article['abstract'])

    def test_title_must_be_a_non_empty_string(self):
        for title in ('', '   ', None, 5):
            self.assertRefused(self.client.post('/api/references', json=save_body(title=title)), 400)
        self.assertEqual(self.citation_count(), 0)

    def test_fields_are_coerced_or_dropped(self):
        article_id = self.save(year='2019', url='javascript:alert(1)', pubmed_id='12ab',
                               doi=None, id=999, citation_number=999, kind='Guideline')
        article = self.client.get(f'/api/references/{article_id}').get_json()['article']
        self.assertEqual(article['year'], 2019)
        self.assertIsNone(article['url'])
        self.assertIsNone(article['pubmed_id'])
        self.assertNotEqual(article['id'], 999)

    def test_bad_year_becomes_none_and_http_url_is_kept(self):
        article_id = self.save(year='soon', url='http://example.org/x', pubmed_id='10000009',
                               doi='10.0000/example.9')
        article = self.client.get(f'/api/references/{article_id}').get_json()['article']
        self.assertIsNone(article['year'])
        self.assertEqual(article['url'], 'http://example.org/x')

    def test_body_that_is_not_an_object_is_400(self):
        self.assertRefused(self.client.post('/api/references', json=[1]), 400)


class TestListAndDetail(ReferencesRoutesTestCase):

    def test_list(self):
        self.save()
        data = self.client.get('/api/references').get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['articles']), 1)
        self.assertTrue(data['articles'][0]['has_abstract'])

    def test_detail_has_specialty_choices(self):
        article_id = self.save()
        data = self.client.get(f'/api/references/{article_id}').get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['article']['id'], article_id)
        choices = {s['id']: s['label'] for s in data['specialties']}
        self.assertEqual(choices['cardiologist'], 'Cardiologist')

    def test_detail_unknown_is_404(self):
        self.assertRefused(self.client.get('/api/references/999'), 404)

    def test_detail_rewrites_a_missing_file(self):
        article_id = self.save()
        for path in self.files():
            path.unlink()
        self.assertEqual(self.files(), [])
        self.assertEqual(self.client.get(f'/api/references/{article_id}').status_code, 200)
        self.assertEqual(len(self.files()), 1)


class TestFetchAbstract(ReferencesRoutesTestCase):

    def test_success_stores_the_abstract_and_rewrites_the_file(self):
        article_id = self.save(abstract=None)
        self.assertNotIn('made-up trial.', self.files()[0].read_text())
        with patch('literature.fetch_by_pubmed_id', return_value=make_result()) as fetch:
            response = self.client.post(f'/api/references/{article_id}/abstract')
        fetch.assert_called_once_with('10000001')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['article']['abstract'], ABSTRACT)
        self.assertIn('made-up trial', self.files()[0].read_text())

    def test_unknown_article_is_404(self):
        with patch('literature.fetch_by_pubmed_id') as fetch:
            self.assertRefused(self.client.post('/api/references/999/abstract'), 404)
        fetch.assert_not_called()

    def test_no_pubmed_id_is_400(self):
        article_id = self.save(pubmed_id=None, abstract=None)
        with patch('literature.fetch_by_pubmed_id') as fetch:
            message = self.assertRefused(
                self.client.post(f'/api/references/{article_id}/abstract'), 400)
        fetch.assert_not_called()
        self.assertEqual(message,
                         'This article has no PubMed id, so its abstract cannot be fetched.')

    def test_nothing_found_or_no_abstract_is_404(self):
        article_id = self.save(abstract=None)
        for returned in (None, make_result(abstract=None)):
            with patch('literature.fetch_by_pubmed_id', return_value=returned) as fetch:
                message = self.assertRefused(
                    self.client.post(f'/api/references/{article_id}/abstract'), 404)
            fetch.assert_called_once()
            self.assertEqual(message, 'The journal index has no abstract for this article.')

    def test_lookup_failure_is_502(self):
        article_id = self.save(abstract=None)
        with patch('literature.fetch_by_pubmed_id',
                   side_effect=literature.LookupFailed('Could not reach it.')) as fetch:
            self.assertRefused(self.client.post(f'/api/references/{article_id}/abstract'), 502)
        fetch.assert_called_once()


class TestDelete(ReferencesRoutesTestCase):

    def test_delete_removes_row_and_file(self):
        article_id = self.save()
        self.assertEqual(len(self.files()), 1)
        response = self.client.delete(f'/api/references/{article_id}')
        self.assertTrue(response.get_json()['success'])
        self.assertEqual(self.files(), [])
        self.assertEqual(self.citation_count(), 0)

    def test_unknown_is_404(self):
        self.assertRefused(self.client.delete('/api/references/999'), 404)

    def test_article_in_use_is_409_and_file_kept(self):
        article_id = self.save()
        db = GeneticProfileDB(self.db_path)
        db.conn.execute('INSERT INTO gene_trait_citations (citation_id) VALUES (?)', (article_id,))
        db.conn.commit()
        db.close()
        message = self.assertRefused(self.client.delete(f'/api/references/{article_id}'), 409)
        self.assertIn('cannot be removed', message)
        self.assertEqual(self.citation_count(), 1)
        self.assertEqual(len(self.files()), 1)


class TestExcerpts(ReferencesRoutesTestCase):

    def add(self, article_id, text='We tested nothing'):
        return self.client.post(f'/api/references/{article_id}/excerpts', json={'text': text})

    def test_add_returns_id_and_article_and_rewrites_file(self):
        article_id = self.save()
        response = self.add(article_id)
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['article']['excerpts'][0]['id'], data['id'])
        self.assertIn('Your excerpts', self.files()[0].read_text())

    def test_refusals(self):
        self.assertRefused(self.add(999), 404)
        with_abstract = self.save()
        message = self.assertRefused(self.add(with_abstract, 'something never said'), 400)
        self.assertEqual(message, 'That text is not in the abstract, word for word.')
        no_abstract = self.save(abstract=None, pubmed_id='10000002', doi='10.0000/example.2')
        self.assertRefused(self.add(no_abstract), 400)
        self.assertRefused(self.client.post(f'/api/references/{with_abstract}/excerpts',
                                            json={'text': 5}), 400)
        self.assertRefused(self.client.post(f'/api/references/{with_abstract}/excerpts',
                                            json=['x']), 400)

    def test_set_specialties(self):
        article_id = self.save()
        excerpt_id = self.add(article_id).get_json()['id']
        response = self.client.put(f'/api/excerpts/{excerpt_id}',
                                   json={'specialties': ['cardiologist']})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['article']['excerpts'][0]['specialties'], ['cardiologist'])
        self.assertIn('Cardiologist', self.files()[0].read_text())

    def test_set_specialties_refusals(self):
        article_id = self.save()
        excerpt_id = self.add(article_id).get_json()['id']
        url = f'/api/excerpts/{excerpt_id}'
        self.assertRefused(self.client.put('/api/excerpts/999', json={'specialties': []}), 404)
        message = self.assertRefused(
            self.client.put(url, json={'specialties': ['cardiologist', 'wizard']}), 400)
        self.assertIn('wizard', message)
        self.assertRefused(self.client.put(url, json={'specialties': 'cardiologist'}), 400)
        self.assertRefused(self.client.put(url, json={'specialties': [1]}), 400)
        self.assertRefused(self.client.put(url, json={}), 400)
        self.assertRefused(self.client.put(url, json=[]), 400)
        article = self.client.get(f'/api/references/{article_id}').get_json()['article']
        self.assertEqual(article['excerpts'][0]['specialties'], [])

    def test_delete_excerpt(self):
        article_id = self.save()
        excerpt_id = self.add(article_id).get_json()['id']
        response = self.client.delete(f'/api/excerpts/{excerpt_id}')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['article']['excerpts'], [])
        self.assertNotIn('Your excerpts', self.files()[0].read_text())
        self.assertRefused(self.client.delete(f'/api/excerpts/{excerpt_id}'), 404)


if __name__ == '__main__':
    unittest.main()


class TestSpecialistDocument(ReferencesRoutesTestCase):
    """The excerpt reaches the document a specialist is handed, and can be left out."""

    def setUp(self):
        super().setUp()
        article_id = self.save()
        excerpt_id = self.client.post(f'/api/references/{article_id}/excerpts',
                                      json={'text': 'We tested nothing'}).get_json()['id']
        response = self.client.put(f'/api/excerpts/{excerpt_id}',
                                   json={'specialties': ['cardiologist']})
        self.assertEqual(response.status_code, 200, response.get_json())

    def test_printable_document_carries_the_excerpt_and_its_source(self):
        page = self.client.get('/doctor-docs/cardiologist/print').get_data(as_text=True)
        self.assertIn('From the literature', page)
        self.assertIn('We tested nothing', page)
        self.assertIn('A made-up trial of nothing', page)
        self.assertIn('https://doi.org/10.0000/example.1', page)

    def test_another_specialist_does_not_get_it(self):
        page = self.client.get('/doctor-docs/psychiatrist/print').get_data(as_text=True)
        self.assertNotIn('From the literature', page)

    def test_references_0_leaves_the_section_out(self):
        page = self.client.get('/doctor-docs/cardiologist/print?references=0').get_data(as_text=True)
        self.assertNotIn('From the literature', page)
        self.assertNotIn('We tested nothing', page)


class TestAnotherSiteCannotDriveALookup(ReferencesRoutesTestCase):
    """
    A page on some other site can make the browser POST here, but only as a
    form or as plain text; sending JSON takes a preflight this app never
    answers. So a body that is not declared as JSON must never reach the
    lookup, or any site the person visits could make this app search for it.
    """

    def test_a_plain_text_post_is_refused_before_the_lookup(self):
        with patch('literature.search') as search:
            response = self.client.post('/api/references/search',
                                        data='{"term": "anything"}',
                                        content_type='text/plain')
        self.assertRefused(response, 400)
        search.assert_not_called()

    def test_a_form_post_is_refused_before_the_lookup(self):
        with patch('literature.search') as search:
            response = self.client.post('/api/references/search', data={'term': 'anything'})
        self.assertRefused(response, 400)
        search.assert_not_called()
