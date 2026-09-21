"""
The properties a downloadable copy depends on.

Every one of these was a real bug found while packaging 1.0.0, and each fails
silently rather than loudly: the app still starts, and only a person who
downloaded it ever sees the consequence. They are asserted here because
nothing else would notice them coming back.
"""

import errno
import re
import socket
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class TestDebugIsOffByDefault(unittest.TestCase):
    """
    Flask's debug mode serves the Werkzeug interactive debugger, which
    evaluates arbitrary Python for anything that can reach the port. Shipping
    it on would be a remote code execution hole in an app holding medical
    records, on every copy downloaded.
    """

    def test_an_unset_flag_reads_false(self):
        self.assertFalse(config._env_flag('HEALTH_LEDGER_NOT_A_REAL_VARIABLE'))

    def test_flag_parsing(self):
        import os
        for raw, expected in (('1', True), ('true', True), ('TRUE', True),
                              ('yes', True), ('on', True),
                              ('0', False), ('false', False), ('', False),
                              ('anything else', False)):
            os.environ['HEALTH_LEDGER_TEST_FLAG'] = raw
            try:
                self.assertIs(config._env_flag('HEALTH_LEDGER_TEST_FLAG'), expected,
                              f'{raw!r} should read as {expected}')
            finally:
                del os.environ['HEALTH_LEDGER_TEST_FLAG']

    def test_debug_is_not_hardcoded_on(self):
        source = (ROOT / 'config.py').read_text(encoding='utf-8')
        self.assertNotRegex(
            source, r'(?m)^DEBUG\s*=\s*True\b',
            "DEBUG must come from HEALTH_LEDGER_DEBUG, never be hardcoded True")
        self.assertRegex(source, r"(?m)^DEBUG\s*=\s*_env_flag\('HEALTH_LEDGER_DEBUG'\)")


class TestResourcePathsSurviveFreezing(unittest.TestCase):
    """
    A packaged build runs its modules out of the PyInstaller archive while its
    data files are unpacked somewhere else entirely, so a resource located
    relative to __file__ is simply not there.
    """

    def test_config_exposes_the_three_roots(self):
        for name in ('IS_FROZEN', 'BASE_DIR', 'CONFIG_DIR', 'ENV_PATH', 'DATA_ROOT'):
            self.assertTrue(hasattr(config, name), f'config.{name} is missing')

    def test_base_dir_honours_the_pyinstaller_unpack_directory(self):
        source = (ROOT / 'config.py').read_text(encoding='utf-8')
        self.assertIn('_MEIPASS', source,
                      'BASE_DIR must resolve to sys._MEIPASS in a packaged build')

    def test_the_schema_is_not_found_through_dunder_file(self):
        source = (ROOT / 'database_manager.py').read_text(encoding='utf-8')
        self.assertNotIn('Path(__file__).parent / "genetic_profile_db_schema.sql"', source)
        self.assertIn('config.DB_SCHEMA_PATH', source)

    def test_flask_templates_and_static_are_pinned_to_base_dir(self):
        source = (ROOT / 'app.py').read_text(encoding='utf-8')
        self.assertRegex(source, r"template_folder=str\(config\.BASE_DIR / 'templates'\)")
        self.assertRegex(source, r"static_folder=str\(config\.BASE_DIR / 'static'\)")

    def test_a_frozen_copy_never_falls_back_to_its_own_directory(self):
        """
        The unpack directory is deleted when the app quits. Falling back to it
        for the records would lose them on the first launch that happened
        before a folder was chosen.
        """
        source = (ROOT / 'config.py').read_text(encoding='utf-8')
        self.assertRegex(
            source,
            r'_DATA_ROOT_FALLBACK\s*=\s*\(Path\.home\(\)\s*/\s*DEFAULT_DATA_DIR_NAME\)\s*if\s*IS_FROZEN',
            'a frozen build must fall back to a folder in the home directory')

    def test_a_frozen_copy_writes_settings_outside_the_bundle(self):
        source = (ROOT / 'config.py').read_text(encoding='utf-8')
        self.assertRegex(source, r'CONFIG_DIR\s*=\s*_user_config_dir\(\)\s*if\s*IS_FROZEN')

    def test_the_user_config_dir_is_per_platform(self):
        path = config._user_config_dir()
        self.assertTrue(path.is_absolute())
        self.assertIn(str(Path.home()), str(path))


class TestFreePortSearch(unittest.TestCase):
    """A double-clicked app cannot be told to pass a different port, so it
    finds its own rather than refusing to start."""

    def test_the_preferred_port_is_used_when_free(self):
        import desktop
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((config.HOST, 0))
            free = probe.getsockname()[1]
        self.assertEqual(desktop.find_free_port(free), free)

    def test_a_busy_port_is_skipped(self):
        import desktop
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as taken:
            taken.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                taken.bind((config.HOST, 0))
            except OSError as exc:  # pragma: no cover
                if exc.errno == errno.EADDRINUSE:
                    self.skipTest('could not reserve a port')
                raise
            taken.listen(1)
            busy = taken.getsockname()[1]
            chosen = desktop.find_free_port(busy)
        self.assertNotEqual(chosen, busy)
        self.assertGreater(chosen, 0)


class TestTheSpecMatchesTheRepository(unittest.TestCase):
    """The spec names data files by path. A rename that misses it produces a
    build that is missing a template or the schema, and only fails when run."""

    def setUp(self):
        self.spec = (ROOT / 'packaging' / 'health_ledger.spec').read_text(encoding='utf-8')

    def test_every_bundled_resource_exists(self):
        for rel in re.findall(r"ROOT / '([^']+)'", self.spec):
            self.assertTrue((ROOT / rel).exists(), f'the spec bundles missing {rel}')

    def test_the_entry_point_is_the_desktop_launcher(self):
        self.assertIn("ROOT / 'desktop.py'", self.spec)

    def test_weasyprint_is_excluded(self):
        """It is a Pango/GTK binding; the bundle cannot carry the C libraries,
        and the app is built to degrade to the browser's print dialog."""
        self.assertIn("'weasyprint'", self.spec)

    def test_the_icons_the_spec_names_are_committed(self):
        for name in ('icon.png', 'icon.icns', 'icon.ico'):
            self.assertTrue((ROOT / 'packaging' / name).is_file(),
                            f'packaging/{name} is missing; run packaging/make_icons.py')

    def test_no_console_window(self):
        self.assertRegex(self.spec, r'(?m)^\s*console=False,')


class TestTheLicenceAndDisclaimerAreShipped(unittest.TestCase):

    def test_the_licence_exists_and_names_its_terms(self):
        licence = (ROOT / 'LICENSE').read_text(encoding='utf-8')
        self.assertIn('Source-Available', licence)
        self.assertIn('NOT MEDICAL ADVICE, NOT A MEDICAL DEVICE', licence)

    def test_the_readme_carries_the_disclaimer(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('Not medical advice', readme)

    def test_the_stale_status_files_are_gone(self):
        for name in ('ALL_FIXES_COMPLETE.md', 'COMPLETE_REVIEW_SUMMARY.md',
                     'EXTRACTION_STATUS.md', 'FIXES_APPLIED.md', 'FIXES_SUMMARY.md',
                     'MEDIUM_PRIORITY_COMPLETE.md', 'PROJECT_STATUS.md',
                     'PROJECT_EVALUATION_AND_RECOMMENDATIONS.md'):
            self.assertFalse((ROOT / name).exists(), f'{name} came back')


if __name__ == '__main__':
    unittest.main()
