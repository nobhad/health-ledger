"""Tests for literature.py: the one module that reaches the journal index.

Nothing here touches the network: requests.get is patched, and the payload is made up.
"""

import re
import unittest
from pathlib import Path
from unittest import mock

import requests

import config
import literature

REPO_ROOT = Path(__file__).resolve().parent.parent
NETWORK_IMPORT = re.compile(r'^\s*(import|from)\s+(requests|urllib\.request|http\.client)\b', re.MULTILINE)
# desktop.py polls its own local server to learn it is up (127.0.0.1 only).
LOCAL_ONLY_MODULES = {'desktop.py'}


def _payload():
    return {
        'hitCount': 5,
        'resultList': {'result': [
            {'title': 'A plain study of example things.', 'authorString': 'Example A, Sample B.',
             'journalInfo': {'journal': {'title': 'Journal of Examples'}}, 'pubYear': '2020',
             'pmid': '10000001', 'doi': '10.0000/example.1', 'citedByCount': 900,
             'abstractText': '<h4>Aim</h4><p>A &amp; B <i>x</i></p>',
             'pubTypeList': {'pubType': ['Journal Article', 'research-article']}},
            {'title': 'A review of sample matters.', 'authorString': 'Example C',
             'journalInfo': {'journal': {'title': 'Sample Reviews'}}, 'pubYear': '2018',
             'pmid': '10000002', 'citedByCount': 50,
             'pubTypeList': {'pubType': ['Review']}},
            {'title': 'A pooled analysis of examples.', 'authorString': 'Example D',
             'pubYear': '2019', 'pmid': '10000003', 'citedByCount': 10,
             'pubTypeList': {'pubType': ['Meta-Analysis', 'Review']}},
            {'title': 'Example practice recommendations.', 'authorString': 'Example E',
             'pubYear': '2017', 'pmid': '10000004', 'doi': '10.0000/example.4', 'citedByCount': 1,
             'pubTypeList': {'pubType': ['Practice Guideline', 'Journal Article']}},
            {'title': 'A systematic look at samples.', 'authorString': 'Example F',
             'pubYear': '2021', 'pmid': '10000005', 'citedByCount': 5,
             'pubTypeList': {'pubType': ['Systematic Review']}},
        ]},
    }


def _response(payload=None, status=200, json_error=False):
    response = mock.Mock()
    response.status_code = status
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError('boom http://secret.example')
    else:
        response.raise_for_status.return_value = None
    if json_error:
        response.json.side_effect = ValueError('not json')
    else:
        response.json.return_value = payload
    return response


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.articles = literature.parse(_payload())
        self.by_pmid = {a.pubmed_id: a for a in self.articles}

    def test_fields_map(self):
        first = self.by_pmid['10000001']
        self.assertEqual(first.title, 'A plain study of example things')
        self.assertEqual(first.authors, 'Example A, Sample B')
        self.assertEqual(first.journal, 'Journal of Examples')
        self.assertEqual(first.year, 2020)
        self.assertEqual(first.doi, '10.0000/example.1')
        self.assertEqual(first.url, 'https://doi.org/10.0000/example.1')
        self.assertEqual(first.cited_by, 900)
        self.assertEqual(first.kind, 'Study')
        self.assertEqual(first.publication_types, ['Journal Article', 'research-article'])
        self.assertEqual(first.abstract, 'Aim\n\nA & B x')

    def test_url_falls_back_to_pubmed(self):
        self.assertEqual(self.by_pmid['10000002'].url, 'https://pubmed.ncbi.nlm.nih.gov/10000002/')

    def test_kinds_by_precedence(self):
        kinds = {pmid: a.kind for pmid, a in self.by_pmid.items()}
        self.assertEqual(kinds, {'10000001': 'Study', '10000002': 'Review',
                                 '10000003': 'Meta-analysis', '10000004': 'Guideline',
                                 '10000005': 'Systematic review'})

    def test_ordering_by_kind_then_citations(self):
        self.assertEqual([a.pubmed_id for a in self.articles],
                         ['10000004', '10000003', '10000005', '10000002', '10000001'])

    def test_same_kind_orders_by_cited_by(self):
        payload = {'resultList': {'result': [
            {'title': 'Low', 'pmid': '10000010', 'citedByCount': 1},
            {'title': 'High', 'pmid': '10000011', 'citedByCount': 99},
        ]}}
        self.assertEqual([a.pubmed_id for a in literature.parse(payload)], ['10000011', '10000010'])

    def test_result_without_abstract(self):
        article = self.by_pmid['10000002']
        self.assertIsNone(article.abstract)

    def test_missing_fields_do_not_raise(self):
        articles = literature.parse({'resultList': {'result': [{'title': 'Bare'}]}})
        self.assertEqual(len(articles), 1)
        self.assertIsNone(articles[0].year)
        self.assertEqual(articles[0].cited_by, 0)
        self.assertEqual(articles[0].kind, 'Study')
        self.assertEqual(articles[0].publication_types, [])

    def test_hit_count_zero(self):
        self.assertEqual(literature.parse({'hitCount': 0, 'resultList': {'result': []}}), [])

    def test_payload_without_result_list_fails(self):
        with self.assertRaises(literature.LookupFailed):
            literature.parse({'hitCount': 3})

    def test_payload_not_a_dict_fails(self):
        with self.assertRaises(literature.LookupFailed):
            literature.parse(['nope'])

    def test_as_dict_has_every_field(self):
        data = self.by_pmid['10000001'].as_dict()
        self.assertEqual(set(data), {'title', 'authors', 'journal', 'year', 'pubmed_id', 'doi', 'url',
                                     'abstract', 'publication_types', 'cited_by', 'kind'})


class PlainTextTests(unittest.TestCase):
    def test_example(self):
        self.assertEqual(literature.plain_text('<h4>Aim</h4><p>A &amp; B <i>x</i></p>'), 'Aim\n\nA & B x')

    def test_never_more_than_one_blank_line(self):
        self.assertEqual(literature.plain_text('<p>One</p><br><br><p></p><div>Two</div>'), 'One\n\nTwo')

    def test_spaces_collapse(self):
        self.assertEqual(literature.plain_text('<p>a    b \n c</p>'), 'a b c')

    def test_escaped_markup_stays_text(self):
        self.assertEqual(literature.plain_text('<p>x &lt; y &amp;&amp; &quot;z&quot;</p>'), 'x < y && "z"')


class BuildRequestTests(unittest.TestCase):
    def test_params_are_exactly_these(self):
        url, params = literature.build_search_request('statin')
        self.assertEqual(url, literature.SEARCH_URL)
        self.assertEqual(params, {'query': '(TITLE:(statin) OR ABSTRACT:(statin)) AND SRC:MED',
                                  'format': 'json', 'resultType': 'core', 'pageSize': '25',
                                  'sort': 'CITED desc'})

    def test_term_cannot_escape_the_parentheses(self):
        _, params = literature.build_search_request('x) OR SRC:PPR (')
        query = params['query']
        # What was typed, with its syntax taken out, sits inside each field's
        # own parentheses and nowhere else.
        typed = 'x OR SRC PPR'
        self.assertEqual(query, f'(TITLE:({typed}) OR ABSTRACT:({typed})) AND SRC:MED')
        self.assertEqual(query.count('SRC:'), 1)

    def test_balanced_quotes_kept_unbalanced_removed(self):
        self.assertEqual(literature.build_search_request('"heart failure"')[1]['query'],
                         '(TITLE:("heart failure") OR ABSTRACT:("heart failure")) AND SRC:MED')
        self.assertEqual(literature.build_search_request('heart "failure')[1]['query'],
                         '(TITLE:(heart failure) OR ABSTRACT:(heart failure)) AND SRC:MED')

    def test_empty_and_long_terms_refused(self):
        for term in ('', '   '):
            with self.assertRaises(ValueError):
                literature.build_search_request(term)
        with self.assertRaises(ValueError):
            literature.build_search_request('a' * (literature.MAX_TERM_LENGTH + 1))
        self.assertEqual(literature.MAX_TERM_LENGTH, 200)
        literature.build_search_request('a' * 200)

    def test_term_that_is_only_syntax_is_refused(self):
        with self.assertRaises(ValueError):
            literature.build_search_request('():')

    def test_id_request(self):
        url, params = literature.build_id_request('10000001')
        self.assertEqual(url, literature.SEARCH_URL)
        self.assertEqual(params['query'], 'EXT_ID:10000001 AND SRC:MED')
        self.assertEqual(set(params), {'query', 'format', 'resultType', 'pageSize'})

    def test_id_must_be_digits(self):
        for bad in ('', 'abc', '123 OR 1', '12a'):
            with self.assertRaises(ValueError):
                literature.build_id_request(bad)


class NetworkTests(unittest.TestCase):
    def test_search_sends_exact_headers_and_fixed_call(self):
        with mock.patch('literature.requests.get', return_value=_response(_payload())) as get:
            results = literature.search('statin')
        self.assertEqual(len(results), 5)
        args, kwargs = get.call_args
        self.assertEqual(args[0], literature.SEARCH_URL)
        self.assertEqual(kwargs['headers'], {'User-Agent': f'HealthLedger/{config.APP_VERSION}',
                                             'Accept': 'application/json'})
        self.assertEqual(kwargs['timeout'], literature.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(literature.REQUEST_TIMEOUT_SECONDS, 10)
        self.assertEqual(set(kwargs), {'params', 'headers', 'timeout'})
        self.assertEqual(set(kwargs['params']),
                         {'query', 'format', 'resultType', 'pageSize', 'sort'})

    def test_failures_become_lookup_failed_without_raw_text(self):
        cases = [
            requests.ConnectionError('dns http://secret.example'),
            requests.Timeout('slow http://secret.example'),
        ]
        messages = set()
        for error in cases:
            with mock.patch('literature.requests.get', side_effect=error):
                with self.assertRaises(literature.LookupFailed) as caught:
                    literature.search('statin')
            message = str(caught.exception)
            messages.add(message)
            self.assertNotIn('secret', message)
            self.assertNotIn('http', message)
            self.assertTrue(message.endswith('.'))
        self.assertEqual(len(messages), 2)

    def test_server_error_is_lookup_failed(self):
        with mock.patch('literature.requests.get', return_value=_response(status=500)):
            with self.assertRaises(literature.LookupFailed) as caught:
                literature.search('statin')
        self.assertNotIn('secret', str(caught.exception))
        self.assertNotIn('http', str(caught.exception))

    def test_unreadable_answer_is_lookup_failed(self):
        with mock.patch('literature.requests.get', return_value=_response(json_error=True)):
            with self.assertRaises(literature.LookupFailed):
                literature.search('statin')
        with mock.patch('literature.requests.get', return_value=_response({'unexpected': 1})):
            with self.assertRaises(literature.LookupFailed):
                literature.search('statin')

    def test_any_other_request_error_is_lookup_failed(self):
        with mock.patch('literature.requests.get', side_effect=requests.RequestException('x')):
            with self.assertRaises(literature.LookupFailed):
                literature.search('statin')

    def test_fetch_returns_first_article_or_none(self):
        with mock.patch('literature.requests.get', return_value=_response(_payload())) as get:
            article = literature.fetch_by_pubmed_id('10000001')
        self.assertEqual(get.call_args[1]['params']['query'], 'EXT_ID:10000001 AND SRC:MED')
        self.assertEqual(article.pubmed_id, '10000004')  # first after ordering
        empty = {'hitCount': 0, 'resultList': {'result': []}}
        with mock.patch('literature.requests.get', return_value=_response(empty)):
            self.assertIsNone(literature.fetch_by_pubmed_id('10000001'))

    def test_invalid_search_makes_no_request(self):
        with mock.patch('literature.requests.get') as get:
            with self.assertRaises(ValueError):
                literature.search('')
        get.assert_not_called()


class NetworkBoundaryTests(unittest.TestCase):
    def test_only_literature_reaches_the_network(self):
        matches = set()
        for path in REPO_ROOT.glob('*.py'):
            if NETWORK_IMPORT.search(path.read_text(encoding='utf-8')):
                matches.add(path.name)
        self.assertIn('literature.py', matches)
        self.assertEqual(matches - LOCAL_ONLY_MODULES, {'literature.py'})


if __name__ == '__main__':
    unittest.main()
