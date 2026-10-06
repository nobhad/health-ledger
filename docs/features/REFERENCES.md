# References

**Added in**: 1.1.0

## What it does

The References page looks up journal articles, keeps the ones you save, and
lets you put short quotes from their abstracts into the document you hand a
specialist. Each quote carries the article's title and a link, so the doctor
can see where it came from.

## Step by step

1. **Look up.** Open **References** in the sidebar. Type a gene, condition or
   medication in the search box and press **Look up**. Each result shows the
   journal, the year, what kind of article it is and how many other papers
   cite it.
2. **Save.** Click a result to read it in the middle of the page, then press
   **Save to my ledger**. It is added to your ledger and appears under
   **Saved articles**. Articles already cited elsewhere in your ledger appear
   there too. If the result came with an abstract, it is saved with it.
3. **Fetch the abstract.** A saved article that has no abstract yet shows a
   **Fetch abstract** button, and only where the article has a PubMed id.
   Press it and the abstract appears in the middle of the page. If the index
   has no abstract for the article, the page says so.
4. **Add an excerpt.** Select a sentence or two of the abstract with the
   mouse and press **Add excerpt**. The excerpt appears on the right.
5. **Tick the specialists.** Each excerpt has a checkbox per specialist. Tick
   the ones who should see it. Untick one to take it back out of that
   specialist's document, or press **Remove excerpt** to delete it.
6. **Find it in the specialist document.** Open **Doctor Docs**, choose that
   specialist and open the document. Near the end there is a section called
   **From the literature**: each excerpt is a quote, followed by the title,
   journal and year, and a link. The **Include journal excerpts** box on
   Doctor Docs is on by default; untick it to leave the section out. A
   specialist with no excerpts gets no section.
7. **Find the file.** Each saved article is also written as a small web page
   in the `references` folder inside your data folder. Double-click it to
   open it in your browser without the app. It holds the title, authors,
   journal and year, the link, the abstract and your excerpts with the
   specialists each is for. The file is rewritten when you change the
   article, and removed when you remove it.

**Remove article** removes a saved article and its excerpts, unless something
else in your ledger cites it.

## What is sent, and to whom

Until version 1.1.0 the app made no outbound request at all. Now there is
exactly one kind: when you press **Look up**, the words you typed are sent to
Europe PMC, a public index of journal articles run by EMBL-EBI. When you press
**Fetch abstract**, the article's PubMed id is sent instead.

Nothing from your records is sent: no names, results, genotypes or files. It
happens only when you press the button, never automatically. A search term
can itself be revealing, such as the name of a gene or a condition. If that
matters to you, search for something more general.

The page says what pressing the button sends, under the search box. With no
internet connection, everything already saved still works, and a lookup tells
you it could not reach the index.

## What "reputable" means here

Results are limited to articles indexed in MEDLINE, which leaves preprints
out. The words you search for must appear in an article's title or abstract,
and the 25 most-cited matches are shown. They are ordered by kind first
(practice guidelines, then meta-analyses, systematic reviews and reviews,
then everything else), and within each kind by how often other papers cite
them.

Most-cited favours older work. A guideline revised last year can sit below
the version it replaced until the citations catch up, so check the year.

That is a filter and an ordering. It is not a guarantee that an article is
right, current or about someone like you. Every result shows what kind of
article it is so you can judge, and you still have to read the paper and talk
to your doctor.

## Limits in this version

- Abstracts only. Full text is not read.
- An excerpt must be word for word from the abstract, apart from spacing. A
  selection that is not in the abstract is refused, so a quote in a document
  is always really from the article.
- The paper's own PDF is not downloaded or stored.
- An excerpt can only be taken from a stored abstract, and an abstract can
  only be fetched for an article with a PubMed id. A saved article that has
  neither a stored abstract nor a PubMed id shows its title and link, and can
  be removed, but cannot take excerpts.
