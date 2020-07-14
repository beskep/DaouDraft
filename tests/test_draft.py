import pytest
import bs4
import os
from datetime import datetime

from daou_draft import daou_draft


@pytest.fixture
def draft():
  html_path = './documents/example.html'
  d = daou_draft.DaouDraft(html_path)
  return d


def test_draft_label(draft):
  test: bs4.Tag = draft.soup.find(name='span',
                                  attrs={'data-dsl': '{{label:draftUser}}'})
  test.string.replace_with('test')

  res_path = './pdf/test.html'
  draft.save(res_path)
  assert os.path.exists(res_path)


def test_draft_user(draft):
  members = draft.soup.find_all(name='span', attrs={'class': 'sign_member'})
  sign_rank_wrap = draft.soup.find_all(name='span',
                                       attrs={'class': 'sign_rank_wrap'})[0]
  children = list(members[0].children)
  assert sign_rank_wrap in children


def test_draft_fill_sign_member(draft: daou_draft.DaouDraft):
  sign_member, sign_rank, sign_name, sign_date = draft._sign_members()
  assert any(x is None for x in sign_name)

  draft._fill_sign_member()
  sign_member = draft.soup.find_all(name='span', attrs={'class': 'sign_member'})
  sign_rank, sign_name, sign_date = draft._sign_members_helper(sign_member)

  assert id(sign_member[2]) != id(sign_member[3])
  assert all(x.string.strip() for x in sign_rank)
  assert all(x.string.strip() for x in sign_name)
  assert all(x.string.strip() for x in sign_date)


def test_fix_sign_date(draft: daou_draft.DaouDraft):
  sign_member, sign_rank, sign_name, sign_date = draft._sign_members()
  assert any(x is None for x in sign_name)

  draft._fill_sign_member()
  sign_member = draft.soup.find_all(name='span', attrs={'class': 'sign_member'})
  sign_rank, sign_name, sign_date = draft._sign_members_helper(sign_member)

  draft._fix_sign_date()
  for d in draft._date:
    assert d.string
    datetime.strptime(d.string.strip(), draft._DaouDraft__ymd_format)


def test_img(draft: daou_draft.DaouDraft):
  draft.change_image_source()


def test_runner():
  runner = daou_draft.Runner()
  # runner.run([
  #     r'D:\Python\etc\DaouDraft\documents\연구 계획 변경 건 (신규 연구원 참여, 한국연구재단 친환경 통합 과제)_2020-07-13_14-39.html'
  # ])
  runner.run()


if __name__ == "__main__":
  pytest.main(['--verbose', '-k', 'test_fix_sign_date'])
