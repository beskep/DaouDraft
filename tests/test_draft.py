import os
import sys
from datetime import datetime

import bs4
import pytest

sys.path.append(os.path.join(__file__, '../../src'))

from draft import daou_draft


@pytest.fixture
def draft_blank():
  html_path = './documents/example_blank.html'
  d = daou_draft.DaouDraft(html_path)
  return d


@pytest.fixture
def draft_five_members():
  html_path = './documents/example_five members.html'
  d = daou_draft.DaouDraft(html_path)
  return d


def test_draft_label(draft_blank):
  test: bs4.Tag = draft_blank.soup.find(
      name='span', attrs={'data-dsl': '{{label:draftUser}}'})
  test.string.replace_with('test')

  res_path = './pdf/test.html'
  draft_blank.save(res_path)
  assert os.path.exists(res_path)


def test_draft_user(draft_blank):
  members = draft_blank.soup.find_all(name='span',
                                      attrs={'class': 'sign_member'})
  sign_rank_wrap = draft_blank.soup.find_all(name='span',
                                             attrs={'class': 'sign_rank_wrap'
                                                   })[0]
  children = list(members[0].children)
  assert sign_rank_wrap in children


def test_draft_fill_sign_member(draft_blank: daou_draft.DaouDraft):
  sign_member, sign_rank, sign_name, sign_date = draft_blank._sign_members()
  assert any(x is None for x in sign_name)

  draft_blank._fill_sign_member()
  sign_member = draft_blank.soup.find_all(name='span',
                                          attrs={'class': 'sign_member'})
  sign_rank, sign_name, sign_date = draft_blank._sign_members_helper(
      sign_member)

  assert id(sign_member[2]) != id(sign_member[3])
  assert all(x.string.strip() for x in sign_rank)
  assert all(x.string.strip() for x in sign_name)
  assert all(x.string.strip() for x in sign_date)


def test_fix_sign_date(draft_five_members: daou_draft.DaouDraft):
  members, ranks, names, dates = draft_five_members._sign_members()

  draft_five_members._fill_sign_member()
  members = draft_five_members.soup.find_all(name='span',
                                             attrs={'class': 'sign_member'})
  ranks, names, dates = draft_five_members._sign_members_helper(members)

  draft_five_members._fix_sign_date()
  for d in draft_five_members._date:
    assert d.string
    datetime.strptime(d.string.strip(), draft_five_members._ymd_format)


def test_img(draft_blank: daou_draft.DaouDraft):
  draft_blank.change_image_source()


def test_runner():
  runner = daou_draft.Runner()
  runner.run()


if __name__ == "__main__":
  pytest.main(['--verbose', '-k', ''])
