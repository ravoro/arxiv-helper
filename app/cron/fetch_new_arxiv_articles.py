"""
Fetch new articles from site and store in db for later processing.

Meant to be run daily.
"""

import logging
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from django.conf import settings

from app.models import Article


def _assert_or_exit(success, error_msg):
    """Log error_msg and exit script if value of success if falsy. Value of success is result of an assertion check."""
    if not success:
        logging.error(error_msg)
        logging.error('Exiting due to error.')
        os._exit(os.EX_OK)  # used instead of sys.exit() to avoid raising SystemExit exception


def _next_tag_sibling(soup):
    """Get the next sibling element that is of type Tag. Needed because newlines are considered as siblings."""
    if isinstance(soup.next_sibling, Tag):
        return soup.next_sibling
    return _next_tag_sibling(soup.next_sibling)


def _pair_dt_dd_tags(tags):
    """Group dt/dd tags into list of pair tuples."""
    true_tags = [c for c in tags if isinstance(c, Tag)]
    pairs = [
        (true_tags[i], true_tags[i + 1])
        for i in range(0, len(true_tags), 2)
    ]
    return pairs


def _validate_dt_dd_pairings(pairs):
    """Validate that all tags are pairings of dt followed by dd."""
    for dt, dd in pairs:
        if dt.name != 'dt' or dd.name != 'dd':
            return False
    return True


def _append_tags(tags):
    """Append a list of beautifulsoup tags inside a div tag."""
    new_tag = Tag(name='div')
    for t in tags:
        new_tag.append(t)
    return new_tag


def _get_submission_arxiv_id_or_none(submission):
    try:
        id_text = submission.select_one('dt .list-identifier a:nth-of-type(1)').text
        id = re.match(r'^arXiv\:([\d|\.]+)$', id_text).group(1)
        return id
    except:
        return None


def _validate_all_submissions_have_arxiv_ids(submissions):
    for s in submissions:
        if not _get_submission_arxiv_id_or_none(s):
            return False
    return True


def _submission_tag_to_dict(tag):
    tag = _modify_tag_links_to_open_in_new_tab(tag)
    tag = _modify_tag_links_to_use_absolute_arxiv_urls(tag)

    return {
        'id_arxiv': _get_submission_arxiv_id_or_none(tag),
        'html_meta': str(tag),
    }


def _modify_tag_links_to_open_in_new_tab(tag):
    a_tags = tag.select('a')
    for a in a_tags:
        a['target'] = '_blank'
    return tag


def _modify_tag_links_to_use_absolute_arxiv_urls(tag):
    a_tags = tag.select('a')
    for a in a_tags:
        href = a.get('href')
        if href and href.startswith('/'):
            a['href'] = settings.ARXIV_BASE_URL + href
    return tag


def _get_date_from_new_submissions_title_or_none(tag):
    try:
        date_str = re.match(r'^New submissions for .*?, (.*)$', tag.text).group(1)
        date = datetime.strptime(date_str, '%d %b %y').date()
        return date
    except:
        return None


def run():
    logging.warning("Running 'fetch_new_articles' job at {}".format(datetime.now()))

    response = requests.get(settings.ARXIV_FEED_URL, headers={'User-Agent': settings.ARXIV_USER_AGENT})
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    dlpage = soup.select_one('#dlpage')
    section_titles = dlpage.select('h3')

    _assert_or_exit(len(section_titles) == 3,
                    'Did not have 3 section titles. section_titles: {}.'.format(section_titles))

    new_submissions_title = section_titles[0]
    _assert_or_exit(new_submissions_title.text.strip().lower().startswith('new submissions for'),
                    'The first section title was not for new submissions. section_titles: {}.'.format(section_titles))

    submission_date = _get_date_from_new_submissions_title_or_none(new_submissions_title)
    _assert_or_exit(submission_date,
                    'Could not determine the submission date.')

    new_articles_count = Article.objects.filter(date_submitted__gte=submission_date).count()
    _assert_or_exit(new_articles_count == 0,
                    'Articles with same ({}) or newer submission date already exist in db.'.format(submission_date))

    new_submissions_dl = _next_tag_sibling(new_submissions_title)
    _assert_or_exit(new_submissions_dl.name == 'dl',
                    'A `<dl>` did not follow the new submissions title.')

    new_submissions_pairings = _pair_dt_dd_tags(new_submissions_dl.children)
    _assert_or_exit(_validate_dt_dd_pairings(new_submissions_pairings),
                    'A `<dl>` did not contain valid parings of only `<dt>` + `<dd>`.')

    new_submissions_tags = [_append_tags(pair) for pair in new_submissions_pairings]
    _assert_or_exit(_validate_all_submissions_have_arxiv_ids(new_submissions_tags),
                    'A submission did not contain a valid arxiv id.')

    new_submissions = [_submission_tag_to_dict(s) for s in new_submissions_tags]
    logging.warning('Detected {} new submissions.'.format(len(new_submissions)))

    for submission in new_submissions:
        logging.warning('Creating submission: {}'.format(article))
        article = Article.objects.create(id_arxiv=submission['id_arxiv'],
                                         html_meta=submission['html_meta'],
                                         date_submitted=submission_date,
                                         date_updated=submission_date,
                                         is_processed=False)