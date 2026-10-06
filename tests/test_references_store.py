"""
Storage for the References feature: saved articles, abstracts, excerpts and the
specialists each excerpt is for.

All fixture data is made up. Nothing here touches the network.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import GeneticProfileDB, ArticleInUse  # noqa: E402

NEW_TABLES = ('citation_abstracts', 'citation_excerpts', 'citation_excerpt_specialties')

ABSTRACT = (
    "Aim\n\nWe tested nothing in a made-up trial.  Participants received\n"
    "no treatment. Results were unremarkable."
)


def make_article(**overrides):
    """A made-up article dict with the keys save_article accepts."""
    article = {
        'title': 'A made-up trial of nothing',
        'authors': 'Example A, Sample B',
        'journal': 'Journal of Examples',
        'year': 2020,
        'doi': '10.0000/example.1',
        'pubmed_id': '10000001',
        'url': 'https://doi.org/10.0000/example.1',
        'abstract': None,
    }
    article.update(overrides)
    return article


class StoreTestCase(unittest.TestCase):
    """A fresh temporary ledger per test."""

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        handle.close()
        self.db_path = handle.name
        self.db = GeneticProfileDB(self.db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ('', '-wal', '-shm'):
            try:
                os.unlink(self.db_path + suffix)
            except FileNotFoundError:
                pass

    def count(self, table):
        return self.db.conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]

    def tables(self):
        rows = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        return {row[0] for row in rows}


class TestAddReferenceOnFreshLedger(StoreTestCase):

    def test_add_research_reference_works_on_a_fresh_ledger(self):
        """The research_references insert named pdf_file_path too, and failed the same way."""
        ref_id = self.db.add_research_reference(1, authors='Example A', year=2020,
                                                title='A made-up paper', journal='J')
        self.assertIsInstance(ref_id, int)

    def test_add_reference_returns_an_id(self):
        new_id = self.db.add_reference(1, authors='Example A', year=2020,
                                       title='A made-up trial of nothing')
        self.assertIsInstance(new_id, int)
        self.assertGreater(new_id, 0)

    def test_add_reference_still_writes_pdf_file_path_when_the_column_exists(self):
        self.db.conn.execute('ALTER TABLE citations ADD COLUMN pdf_file_path TEXT')
        new_id = self.db.add_reference(1, title='Made up', pdf_file_path='made-up.pdf')
        row = self.db.conn.execute(
            'SELECT pdf_file_path FROM citations WHERE id = ?', (new_id,)).fetchone()
        self.assertEqual(row[0], 'made-up.pdf')


class TestSchemaReachesExistingDatabases(StoreTestCase):

    def test_new_tables_exist_on_a_fresh_ledger(self):
        for table in NEW_TABLES:
            self.assertIn(table, self.tables())

    def test_existing_database_gains_the_tables(self):
        for table in ('citation_excerpt_specialties', 'citation_excerpts',
                      'citation_abstracts'):
            self.db.conn.execute(f'DROP TABLE {table}')
        self.db.conn.commit()
        for table in NEW_TABLES:
            self.assertNotIn(table, self.tables())
        self.db.close()

        self.db = GeneticProfileDB(self.db_path)
        for table in NEW_TABLES:
            self.assertIn(table, self.tables())


class TestSaveArticle(StoreTestCase):

    def test_saves_a_journal_row_numbered_after_the_maximum(self):
        self.db.add_reference(7, title='Existing')
        new_id = self.db.save_article(make_article())
        row = self.db.conn.execute(
            'SELECT * FROM citations WHERE id = ?', (new_id,)).fetchone()
        self.assertEqual(row['reference_type'], 'journal')
        self.assertEqual(row['citation_number'], 8)
        self.assertEqual(row['title'], 'A made-up trial of nothing')

    def test_first_article_is_number_one(self):
        new_id = self.db.save_article(make_article())
        row = self.db.conn.execute(
            'SELECT citation_number FROM citations WHERE id = ?', (new_id,)).fetchone()
        self.assertEqual(row[0], 1)

    def test_saving_twice_by_pubmed_id_gives_one_row(self):
        first = self.db.save_article(make_article(doi=None))
        second = self.db.save_article(make_article(doi=None))
        self.assertEqual(first, second)
        self.assertEqual(self.count('citations'), 1)

    def test_saving_by_a_doi_already_present_returns_that_id(self):
        existing = self.db.add_reference(1, title='Old', doi='10.0000/example.1')
        saved = self.db.save_article(make_article(pubmed_id=None))
        self.assertEqual(saved, existing)
        self.assertEqual(self.count('citations'), 1)

    def test_saving_by_a_pubmed_id_already_among_old_citations_returns_that_id(self):
        existing = self.db.add_reference(1, title='Old', pubmed_id='10000001')
        saved = self.db.save_article(make_article(doi=None))
        self.assertEqual(saved, existing)
        self.assertEqual(self.count('citations'), 1)

    def test_resaving_stores_an_abstract_the_row_lacked(self):
        first = self.db.save_article(make_article())
        self.assertIsNone(self.db.get_article(first)['abstract'])
        self.db.save_article(make_article(abstract=ABSTRACT))
        self.assertEqual(self.db.get_article(first)['abstract'], ABSTRACT)

    def test_resaving_does_not_overwrite_an_existing_abstract(self):
        first = self.db.save_article(make_article(abstract=ABSTRACT))
        self.db.save_article(make_article(abstract='Something else entirely.'))
        self.assertEqual(self.db.get_article(first)['abstract'], ABSTRACT)

    def test_abstract_is_stored_with_the_article(self):
        new_id = self.db.save_article(make_article(abstract=ABSTRACT))
        self.assertEqual(self.db.get_article(new_id)['abstract'], ABSTRACT)

    def test_markup_is_stored_as_plain_text(self):
        title = 'Is a < b & "c"?'
        new_id = self.db.save_article(make_article(title=title))
        self.assertEqual(self.db.get_article(new_id)['title'], title)

    def test_only_a_title_is_required(self):
        new_id = self.db.save_article({'title': 'Only a title'})
        self.assertEqual(self.db.get_article(new_id)['title'], 'Only a title')


class TestListAndGet(StoreTestCase):

    def test_list_articles_leaves_primary_source_rows_out(self):
        journal = self.db.save_article(make_article())
        self.db.add_reference(50, title='My own record', reference_type='primary_source')
        listed = self.db.list_articles()
        self.assertEqual([a['id'] for a in listed], [journal])

    def test_list_articles_reports_abstract_and_excerpt_counts(self):
        with_abstract = self.db.save_article(make_article(abstract=ABSTRACT))
        without = self.db.save_article(make_article(
            title='Another made-up trial', pubmed_id='10000002', doi='10.0000/example.2'))
        self.db.add_excerpt(with_abstract, 'We tested nothing')
        self.db.add_excerpt(with_abstract, 'Results were unremarkable.')
        by_id = {a['id']: a for a in self.db.list_articles()}
        self.assertIs(by_id[with_abstract]['has_abstract'], True)
        self.assertEqual(by_id[with_abstract]['excerpt_count'], 2)
        self.assertIs(by_id[without]['has_abstract'], False)
        self.assertEqual(by_id[without]['excerpt_count'], 0)

    def test_get_article_unknown_id_is_none(self):
        self.assertIsNone(self.db.get_article(999))

    def test_get_article_carries_excerpts_with_specialties(self):
        article = self.db.save_article(make_article(abstract=ABSTRACT))
        excerpt = self.db.add_excerpt(article, 'We tested nothing')
        self.db.set_excerpt_specialties(excerpt, ['psychiatrist', 'cardiologist'])
        got = self.db.get_article(article)
        self.assertEqual(len(got['excerpts']), 1)
        self.assertEqual(got['excerpts'][0]['id'], excerpt)
        self.assertEqual(got['excerpts'][0]['excerpt_text'], 'We tested nothing')
        self.assertEqual(sorted(got['excerpts'][0]['specialties']),
                         ['cardiologist', 'psychiatrist'])


class TestAbstractsAndExcerpts(StoreTestCase):

    def setUp(self):
        super().setUp()
        self.article = self.db.save_article(make_article(abstract=ABSTRACT))

    def test_set_article_abstract_replaces_the_abstract(self):
        self.db.set_article_abstract(self.article, 'A replacement abstract.')
        self.assertEqual(self.db.get_article(self.article)['abstract'],
                         'A replacement abstract.')

    def test_excerpt_that_differs_only_in_whitespace_is_accepted_and_collapsed(self):
        excerpt = self.db.add_excerpt(
            self.article, 'tested   nothing in a made-up trial.\n Participants received no')
        stored = self.db.get_article(self.article)['excerpts'][0]
        self.assertEqual(stored['id'], excerpt)
        self.assertEqual(stored['excerpt_text'],
                         'tested nothing in a made-up trial. Participants received no')

    def test_excerpt_not_in_the_abstract_raises(self):
        with self.assertRaises(ValueError):
            self.db.add_excerpt(self.article, 'We tested something else')
        self.assertEqual(self.count('citation_excerpts'), 0)

    def test_empty_excerpt_raises(self):
        for text in ('', '   \n '):
            with self.assertRaises(ValueError):
                self.db.add_excerpt(self.article, text)

    def test_excerpt_on_an_article_without_an_abstract_raises(self):
        bare = self.db.save_article(make_article(
            title='No abstract here', pubmed_id='10000002', doi='10.0000/example.2'))
        with self.assertRaises(ValueError):
            self.db.add_excerpt(bare, 'anything')

    def test_specialties_are_replaced_not_appended(self):
        excerpt = self.db.add_excerpt(self.article, 'We tested nothing')
        self.db.set_excerpt_specialties(excerpt, ['cardiologist', 'psychiatrist'])
        self.db.set_excerpt_specialties(excerpt, ['neurologist'])
        got = self.db.get_article(self.article)['excerpts'][0]
        self.assertEqual(got['specialties'], ['neurologist'])
        self.db.set_excerpt_specialties(excerpt, [])
        self.assertEqual(self.db.get_article(self.article)['excerpts'][0]['specialties'], [])

    def test_repeated_specialty_in_one_call_is_stored_once(self):
        excerpt = self.db.add_excerpt(self.article, 'We tested nothing')
        self.db.set_excerpt_specialties(excerpt, ['cardiologist', 'cardiologist'])
        self.assertEqual(self.count('citation_excerpt_specialties'), 1)

    def test_delete_excerpt_returns_the_citation_id_and_its_specialties_go(self):
        excerpt = self.db.add_excerpt(self.article, 'We tested nothing')
        self.db.set_excerpt_specialties(excerpt, ['cardiologist'])
        self.assertEqual(self.db.delete_excerpt(excerpt), self.article)
        self.assertEqual(self.count('citation_excerpts'), 0)
        self.assertEqual(self.count('citation_excerpt_specialties'), 0)

    def test_delete_excerpt_unknown_id_is_none(self):
        self.assertIsNone(self.db.delete_excerpt(999))

    def test_get_excerpt_article_id(self):
        excerpt = self.db.add_excerpt(self.article, 'We tested nothing')
        self.assertEqual(self.db.get_excerpt_article_id(excerpt), self.article)
        self.assertIsNone(self.db.get_excerpt_article_id(999))
        self.assertEqual(self.count('citation_excerpts'), 1)


class TestDeleteArticle(StoreTestCase):

    def cite(self, table, citation_id):
        """Make another table name the citation, with just the columns it needs."""
        if table in ('gene_trait_citations', 'gene_health_citations'):
            self.db.conn.execute(
                f'INSERT INTO {table} (citation_id) VALUES (?)', (citation_id,))
        elif table == 'research_finding_citations':
            self.db.conn.execute(
                'INSERT INTO research_finding_citations (research_finding_id, citation_id) '
                'VALUES (1, ?)', (citation_id,))
        elif table == 'primary_sources':
            self.db.conn.execute(
                "INSERT INTO primary_sources (source_name, source_type, citation_id) "
                "VALUES ('A made-up record', 'medical_record', ?)", (citation_id,))
        elif table == 'pharmacogenomic_data':
            self.db.conn.execute(
                "INSERT INTO pharmacogenomic_data (gene_id, metabolism_status, citation_id) "
                "VALUES (1, 'normal', ?)", (citation_id,))
        self.db.conn.commit()

    def test_a_cited_article_raises_and_nothing_is_removed(self):
        for table in ('gene_trait_citations', 'gene_health_citations',
                      'research_finding_citations', 'primary_sources',
                      'pharmacogenomic_data'):
            with self.subTest(table=table):
                article = self.db.save_article(make_article(
                    title=f'Cited by {table}', pubmed_id=None, doi=None,
                    abstract=ABSTRACT))
                excerpt = self.db.add_excerpt(article, 'We tested nothing')
                self.cite(table, article)
                with self.assertRaises(ArticleInUse):
                    self.db.delete_article(article)
                got = self.db.get_article(article)
                self.assertIsNotNone(got)
                self.assertEqual(got['abstract'], ABSTRACT)
                self.assertEqual([e['id'] for e in got['excerpts']], [excerpt])

    def test_an_uncited_article_goes_with_its_abstract_and_excerpts(self):
        article = self.db.save_article(make_article(abstract=ABSTRACT))
        excerpt = self.db.add_excerpt(article, 'We tested nothing')
        self.db.set_excerpt_specialties(excerpt, ['cardiologist'])
        keep = self.db.save_article(make_article(
            title='Keep me', pubmed_id='10000002', doi='10.0000/example.2',
            abstract=ABSTRACT))
        self.db.add_excerpt(keep, 'Results were unremarkable.')

        self.db.delete_article(article)

        self.assertIsNone(self.db.get_article(article))
        self.assertEqual(self.count('citations'), 1)
        self.assertEqual(self.count('citation_abstracts'), 1)
        self.assertEqual(self.count('citation_excerpts'), 1)
        self.assertEqual(self.count('citation_excerpt_specialties'), 0)


class TestExcerptsForSpecialty(StoreTestCase):

    def test_returns_only_excerpts_assigned_to_that_specialty(self):
        first = self.db.save_article(make_article(abstract=ABSTRACT))
        second = self.db.save_article(make_article(
            title='A second made-up trial', authors='Example C', journal='Annals of Examples',
            year=2021, pubmed_id='10000002', doi='10.0000/example.2',
            url='https://doi.org/10.0000/example.2', abstract=ABSTRACT))
        heart = self.db.add_excerpt(first, 'We tested nothing')
        mind = self.db.add_excerpt(first, 'Participants received no treatment.')
        both = self.db.add_excerpt(second, 'Results were unremarkable.')
        self.db.set_excerpt_specialties(heart, ['cardiologist'])
        self.db.set_excerpt_specialties(mind, ['psychiatrist'])
        self.db.set_excerpt_specialties(both, ['psychiatrist', 'cardiologist'])

        rows = self.db.get_excerpts_for_specialty('cardiologist')

        self.assertEqual([r['excerpt_text'] for r in rows],
                         ['We tested nothing', 'Results were unremarkable.'])
        self.assertEqual(rows[1]['title'], 'A second made-up trial')
        self.assertEqual(rows[1]['authors'], 'Example C')
        self.assertEqual(rows[1]['journal'], 'Annals of Examples')
        self.assertEqual(rows[1]['year'], 2021)
        self.assertEqual(rows[1]['doi'], '10.0000/example.2')
        self.assertEqual(rows[1]['pubmed_id'], '10000002')
        self.assertEqual(rows[1]['url'], 'https://doi.org/10.0000/example.2')

    def test_orders_by_article_then_excerpt_id(self):
        first = self.db.save_article(make_article(abstract=ABSTRACT))
        second = self.db.save_article(make_article(
            title='Second', pubmed_id='10000002', doi='10.0000/example.2',
            abstract=ABSTRACT))
        late = self.db.add_excerpt(second, 'We tested nothing')
        early_b = self.db.add_excerpt(first, 'Results were unremarkable.')
        early_a = self.db.add_excerpt(first, 'We tested nothing')
        for excerpt in (late, early_b, early_a):
            self.db.set_excerpt_specialties(excerpt, ['cardiologist'])
        rows = self.db.get_excerpts_for_specialty('cardiologist')
        self.assertEqual([r['title'] for r in rows],
                         ['A made-up trial of nothing', 'A made-up trial of nothing',
                          'Second'])
        self.assertEqual([r['excerpt_text'] for r in rows[:2]],
                         ['Results were unremarkable.', 'We tested nothing'])

    def test_unknown_specialty_is_empty(self):
        self.assertEqual(self.db.get_excerpts_for_specialty('cardiologist'), [])


if __name__ == '__main__':
    unittest.main()
