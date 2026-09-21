#!/usr/bin/env python3
"""
First-run setup: the overview sends an empty ledger to /setup, "start fresh"
ends that, and an imported or restored database replaces the current one
after a backup. Every test works on temporary files; the real records are
never opened.
"""

import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import ledger_setup
from app import app
from database_manager import GeneticProfileDB


class SetupTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='hl-setup-'))
        self.db_path = self.tmp / 'ledger.db'
        # An empty database with the schema applied.
        GeneticProfileDB(str(self.db_path)).close()

        self._saved = {name: getattr(config, name) for name in
                       ('DB_PATH', 'DATA_ROOT', 'BACKUPS_DIR', 'PRIMARY_SOURCES_DIR',
                        'OUTPUT_DIR', 'LOGS_DIR', 'DATA_DIR', 'DOCTOR_DOCS_DIR',
                        'ENV_PATH', 'DATA_DIR_IS_CONFIGURED', 'default_data_root')}
        self._saved_env = os.environ.get('HEALTH_LEDGER_DATA_DIR')
        config.DB_PATH = self.db_path
        config.DATA_ROOT = self.tmp
        config.BACKUPS_DIR = self.tmp / 'backups'
        config.PRIMARY_SOURCES_DIR = self.tmp / 'primary_sources'
        config.OUTPUT_DIR = self.tmp / 'output'
        config.LOGS_DIR = self.tmp / 'logs'
        config.DATA_DIR = self.tmp / 'data'
        config.DOCTOR_DOCS_DIR = self.tmp / 'output' / 'doctor_docs'
        # The folder choice is written to a throwaway .env, and the proposed
        # default points into the temp tree, so no test touches the home
        # directory or the real settings.
        config.ENV_PATH = self.tmp / 'dot-env'
        config.DATA_DIR_IS_CONFIGURED = True
        config.default_data_root = lambda: self.tmp / 'Health Ledger'

        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(config, name, value)
        if self._saved_env is None:
            os.environ.pop('HEALTH_LEDGER_DATA_DIR', None)
        else:
            os.environ['HEALTH_LEDGER_DATA_DIR'] = self._saved_env
        shutil.rmtree(self.tmp, ignore_errors=True)

    # Helpers

    def make_ledger_db(self, path: Path, genes=('BRCA1',)) -> Path:
        db = GeneticProfileDB(str(path))
        for i, symbol in enumerate(genes, start=1):
            db.add_gene(symbol, f'Gene {i}', str(i))
        db.close()
        return path

    def gene_symbols(self) -> list:
        conn = sqlite3.connect(self.db_path)
        try:
            return [r[0] for r in conn.execute('SELECT gene_symbol FROM genes ORDER BY gene_symbol')]
        finally:
            conn.close()

    def upload(self, path: Path, name='mydata.db', folder=None):
        with open(path, 'rb') as fh:
            data = fh.read()
        form = {'database': (io.BytesIO(data), name)}
        if folder is not None:
            form['data_folder'] = folder
        return self.client.post('/setup/import', data=form, content_type='multipart/form-data')

    def env_text(self) -> str:
        return config.ENV_PATH.read_text() if config.ENV_PATH.is_file() else ''


class TestFirstRun(SetupTestCase):
    def test_empty_ledger_redirects_to_setup(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/setup'))

    def test_setup_page_offers_both_choices(self):
        response = self.client.get('/setup')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Import this database', html)
        self.assertIn('Start with an empty ledger', html)

    def test_start_fresh_ends_setup_and_creates_folders(self):
        # The form always carries the folder field; keeping the proposed
        # folder leaves the records where they are.
        response = self.client.post('/setup/start', data={'data_folder': str(self.tmp)})
        self.assertEqual(response.status_code, 302)
        # An empty ledger is not worth looking at, so setup hands straight
        # over to putting the first record in.
        self.assertIn('/import', response.headers['Location'])
        self.assertIn('first=1', response.headers['Location'])
        for folder in ('backups', 'primary_sources', 'output', 'logs'):
            self.assertTrue((self.tmp / folder).is_dir(), folder)

    def test_the_first_run_import_page_is_framed_as_a_first_step(self):
        self.client.post('/setup/start', data={'data_folder': str(self.tmp)})
        html = self.client.get('/import?first=1').get_data(as_text=True)
        self.assertIn('first record', html)
        # And it can be skipped: nobody is trapped in a wizard.
        self.assertIn('Skip for now', html)

    def test_finishing_the_first_import_says_so_on_the_overview(self):
        self.make_ledger_db(self.db_path)
        html = self.client.get('/?notice=first-record').get_data(as_text=True)
        self.assertIn('That is your first record in', html)

    def test_ledger_with_content_never_redirects(self):
        self.make_ledger_db(self.db_path)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_setup_page_hides_start_fresh_once_there_is_content(self):
        self.make_ledger_db(self.db_path)
        html = self.client.get('/setup').get_data(as_text=True)
        self.assertIn('Import this database', html)
        self.assertNotIn('Start with an empty ledger', html)


class TestImport(SetupTestCase):
    def test_import_replaces_empty_ledger(self):
        source = self.make_ledger_db(self.tmp / 'incoming.db', genes=('CYP2D6', 'MTHFR'))
        response = self.upload(source)
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        self.assertIn('notice=imported', response.headers['Location'])
        self.assertEqual(self.gene_symbols(), ['CYP2D6', 'MTHFR'])
        # No backup of an empty database; nothing to keep.
        self.assertFalse(list((self.tmp / 'backups').glob('*.db')))
        # The overview now renders instead of redirecting.
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_import_backs_up_a_ledger_with_content_first(self):
        self.make_ledger_db(self.db_path, genes=('OLD1',))
        source = self.make_ledger_db(self.tmp / 'incoming.db', genes=('NEW1',))
        response = self.upload(source)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.gene_symbols(), ['NEW1'])
        backups = list((self.tmp / 'backups').glob('genetic_profile_backup_*.db'))
        self.assertEqual(len(backups), 1)
        conn = sqlite3.connect(backups[0])
        try:
            self.assertEqual([r[0] for r in conn.execute('SELECT gene_symbol FROM genes')], ['OLD1'])
        finally:
            conn.close()

    def test_import_keeps_wal_writes(self):
        # Rows written through the app's WAL connection are in the copy even
        # though they may still sit in the write-ahead log.
        db = GeneticProfileDB(str(self.tmp / 'incoming.db'))
        db.add_gene('WAL1', 'Gene', '1')
        db.close()
        response = self.upload(self.tmp / 'incoming.db')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.gene_symbols(), ['WAL1'])

    def test_import_refuses_a_non_sqlite_file(self):
        junk = self.tmp / 'notes.db'
        junk.write_bytes(b'this is not a database at all\n')
        response = self.upload(junk)
        self.assertEqual(response.status_code, 400)
        self.assertIn('not a SQLite database', response.get_data(as_text=True))
        self.assertEqual(self.gene_symbols(), [])

    def test_import_refuses_a_foreign_sqlite_database(self):
        other = self.tmp / 'other.db'
        conn = sqlite3.connect(other)
        conn.execute('CREATE TABLE recipes (id INTEGER PRIMARY KEY, name TEXT)')
        conn.commit()
        conn.close()
        response = self.upload(other)
        self.assertEqual(response.status_code, 400)
        self.assertIn('not a Health Ledger database', response.get_data(as_text=True))

    def test_import_without_a_file_is_an_error(self):
        response = self.client.post('/setup/import', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Choose a database file', response.get_data(as_text=True))

    def test_temp_upload_is_removed(self):
        source = self.make_ledger_db(self.tmp / 'incoming.db')
        self.upload(source)
        self.assertFalse(list(self.tmp.glob('import_*.db')))


class TestRestore(SetupTestCase):
    def test_restore_a_backup_by_name(self):
        backups = self.tmp / 'backups'
        backups.mkdir()
        self.make_ledger_db(backups / 'genetic_profile_backup_20260101_120000.db', genes=('RESTORED',))
        html = self.client.get('/setup').get_data(as_text=True)
        self.assertIn('genetic_profile_backup_20260101_120000.db', html)

        response = self.client.post('/setup/restore',
                                    data={'filename': 'genetic_profile_backup_20260101_120000.db'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('notice=restored', response.headers['Location'])
        self.assertEqual(self.gene_symbols(), ['RESTORED'])

    def test_restore_refuses_paths_and_unknown_names(self):
        for name in ('../ledger.db', 'nothing_here.db', ''):
            response = self.client.post('/setup/restore', data={'filename': name})
            self.assertEqual(response.status_code, 404, name)


class TestDataFolder(SetupTestCase):
    def test_setup_page_proposes_the_default_folder(self):
        config.DATA_DIR_IS_CONFIGURED = False
        html = self.client.get('/setup').get_data(as_text=True)
        self.assertIn(str(self.tmp / 'Health Ledger'), html)

    def test_setup_page_proposes_the_configured_folder(self):
        html = self.client.get('/setup').get_data(as_text=True)
        self.assertIn(f'value="{self.tmp}"', html)

    def test_start_fresh_in_a_chosen_folder_writes_env(self):
        chosen = self.tmp / 'chosen'
        response = self.client.post('/setup/start', data={'data_folder': str(chosen)})
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        self.assertTrue((chosen / 'genetic_profile.db').is_file())
        self.assertTrue((chosen / 'backups').is_dir())
        self.assertEqual(config.DATA_ROOT, chosen.resolve())
        self.assertIn(f'HEALTH_LEDGER_DATA_DIR={chosen.resolve()}', self.env_text())
        html = self.client.get('/?notice=fresh').get_data(as_text=True)
        self.assertIn('Your ledger is ready.', html)

    def test_blank_folder_means_the_default(self):
        response = self.client.post('/setup/start', data={'data_folder': '   '})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(config.DATA_ROOT, (self.tmp / 'Health Ledger').resolve())

    def test_tilde_is_expanded(self):
        home = Path.home().resolve()
        response = self.client.post('/setup/start', data={'data_folder': '~/../' + home.name + '/../' + home.name + '/' + self.tmp.name + '-tilde'})
        # Whatever the spelling, the result is absolute, expanded and resolved.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(config.DATA_ROOT.is_absolute())
        self.assertNotIn('~', str(config.DATA_ROOT))
        shutil.rmtree(config.DATA_ROOT, ignore_errors=True)

    def test_relative_folder_is_refused(self):
        response = self.client.post('/setup/start', data={'data_folder': 'records'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('full path', response.get_data(as_text=True))
        self.assertEqual(self.env_text(), '')

    def test_folder_inside_the_app_is_refused(self):
        response = self.client.post('/setup/start', data={'data_folder': str(config.BASE_DIR / 'mydata')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('outside the Health Ledger app folder', response.get_data(as_text=True))
        self.assertFalse((config.BASE_DIR / 'mydata').exists())

    def test_env_line_is_replaced_and_other_lines_kept(self):
        config.ENV_PATH.write_text('# my settings\nHEALTH_LEDGER_DATA_DIR=/somewhere/old\nOTHER=1\n')
        chosen = self.tmp / 'chosen'
        self.client.post('/setup/start', data={'data_folder': str(chosen)})
        text = self.env_text()
        self.assertIn('# my settings\n', text)
        self.assertIn('OTHER=1\n', text)
        self.assertNotIn('/somewhere/old', text)
        self.assertEqual(text.count('HEALTH_LEDGER_DATA_DIR='), 1)

    def test_import_into_a_chosen_folder(self):
        source = self.make_ledger_db(self.tmp / 'incoming.db', genes=('MOVED',))
        chosen = self.tmp / 'chosen'
        response = self.upload(source, folder=str(chosen))
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        conn = sqlite3.connect(chosen / 'genetic_profile.db')
        try:
            self.assertEqual([r[0] for r in conn.execute('SELECT gene_symbol FROM genes')], ['MOVED'])
        finally:
            conn.close()
        self.assertFalse(list(chosen.glob('import_*.db')))

    def test_restore_into_a_chosen_folder(self):
        backups = self.tmp / 'backups'
        backups.mkdir()
        self.make_ledger_db(backups / 'genetic_profile_backup_20260101_120000.db', genes=('KEPT',))
        chosen = self.tmp / 'chosen'
        response = self.client.post('/setup/restore', data={
            'filename': 'genetic_profile_backup_20260101_120000.db', 'data_folder': str(chosen)})
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        conn = sqlite3.connect(chosen / 'genetic_profile.db')
        try:
            self.assertEqual([r[0] for r in conn.execute('SELECT gene_symbol FROM genes')], ['KEPT'])
        finally:
            conn.close()

    def test_folder_field_is_absent_once_there_is_content(self):
        self.make_ledger_db(self.db_path)
        html = self.client.get('/setup').get_data(as_text=True)
        self.assertNotIn('name="data_folder"', html)


class TestPlaceholderDatabase(SetupTestCase):
    def setUp(self):
        super().setUp()
        # Pretend the app fell back to its own folder: the current database
        # is an empty one inside a fake app directory.
        self.fake_app = self.tmp / 'app'
        self.fake_app.mkdir()
        self._saved_base = config.BASE_DIR
        config.BASE_DIR = self.fake_app
        self.placeholder = self.fake_app / 'genetic_profile.db'
        GeneticProfileDB(str(self.placeholder)).close()
        config.DB_PATH = self.placeholder
        config.DATA_ROOT = self.fake_app
        config.DATA_DIR_IS_CONFIGURED = False

    def tearDown(self):
        config.BASE_DIR = self._saved_base
        super().tearDown()

    def test_empty_placeholder_is_removed_after_choosing_a_folder(self):
        response = self.client.post('/setup/start', data={'data_folder': str(self.tmp / 'chosen')})
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        self.assertFalse(self.placeholder.exists())
        self.assertFalse(list(self.fake_app.glob('genetic_profile.db-*')))
        self.assertTrue((self.tmp / 'chosen' / 'genetic_profile.db').is_file())

    def test_placeholder_with_content_is_kept(self):
        db = GeneticProfileDB(str(self.placeholder))
        db.add_gene('KEEP', 'Gene', '1')
        db.close()
        response = self.client.post('/setup/start', data={'data_folder': str(self.tmp / 'chosen')})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.placeholder.exists())


class TestOverviewLeadsWithTheTask(SetupTestCase):
    """
    The overview is organised by what somebody came to do. With an empty
    ledger there is exactly one useful thing to do, so the page is that;
    with records in it the page offers the handful of real tasks before
    the counts.
    """

    def test_an_empty_ledger_offers_only_the_one_useful_thing(self):
        self.client.post('/setup/start', data={'data_folder': str(self.tmp)})
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('Your ledger is empty', html)
        self.assertIn('Add your first record', html)
        # None of the other tasks can be done yet, so none are offered.
        self.assertNotIn('Get ready for an appointment', html)
        self.assertNotIn('See what your records say', html)
        # Bringing in an existing database is still reachable.
        self.assertIn('/setup', html)

    def test_a_filled_ledger_leads_with_tasks_then_counts(self):
        self.make_ledger_db(self.db_path)
        html = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('Your ledger is empty', html)
        for task in ('Add a record', 'Get ready for an appointment',
                     'See what your records say', 'Back up your records'):
            self.assertIn(task, html)
        # The tasks come before what the database happens to contain.
        self.assertLess(html.index('Add a record'), html.index('stat-grid'))

    def test_the_backup_task_says_when_there_has_never_been_one(self):
        self.make_ledger_db(self.db_path)
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('No copy has ever been made', html)


class TestSetupModule(unittest.TestCase):
    def test_needs_setup_logic(self):
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE genes (id INTEGER PRIMARY KEY, gene_symbol TEXT)')
        conn.execute('CREATE TABLE primary_sources (id INTEGER PRIMARY KEY)')
        conn.execute('CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT)')
        self.assertTrue(ledger_setup.needs_setup(conn))
        ledger_setup.mark_setup_completed(conn)
        self.assertFalse(ledger_setup.needs_setup(conn))

    def test_content_alone_ends_setup(self):
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE genes (id INTEGER PRIMARY KEY, gene_symbol TEXT)')
        conn.execute("INSERT INTO genes (gene_symbol) VALUES ('X')")
        self.assertFalse(ledger_setup.needs_setup(conn))


if __name__ == '__main__':
    unittest.main()
