import datetime
import json
import os
import re
from collections import OrderedDict
from subprocess import run
from warnings import warn

import bs4

_FILE_DIR = os.path.dirname(__file__)
_WKHTMLTOX_PATH = os.path.abspath(
    os.path.join(_FILE_DIR, '../wkhtmltox/bin/wkhtmltopdf.exe'))
_STAMP_PATH = os.path.abspath(os.path.join(_FILE_DIR, '../stamp_approved.png'))

if not os.path.exists(_WKHTMLTOX_PATH):
  raise FileNotFoundError(_WKHTMLTOX_PATH)


class DaouDraft:

  __label = {'docNo', 'draftDate', 'draftDept', 'draftUser'}
  __sign_member_count = 4
  __default_rank = ('사원', '과장', '본부장', '대표이사')
  __ymd_format = '%Y/%m/%d'
  __md_format = '%m/%d'

  def __init__(self, path) -> None:
    self._path = path
    self._soup = self.read_soup(self._path)
    self._member, self._rank, self._name, self._date = self._sign_members()

  @property
  def soup(self):
    return self._soup

  def read_soup(self, path):
    doc = open(path, 'r', encoding='utf-8').readlines()
    doc_join = ''.join(doc)
    soup = bs4.BeautifulSoup(markup=doc_join, features='html.parser')
    return soup

  def _sign_members_helper(self, sign_member):

    def _find(tag, cls_):
      return tag.findChild(name='span', attrs={'class': cls_})

    sign_rank = [_find(x, 'sign_rank') for x in sign_member]

    # <span class="sign_name"> 밑에 <strong> 태그가 있음
    # sign_name = [_find(x, 'sign_name') for x in sign_member]
    sign_name = [x.findChild(name='strong') for x in sign_member]

    sign_date = [_find(x, 'sign_date') for x in sign_member]

    assert len(sign_rank) == self.__sign_member_count
    assert len(sign_name) == self.__sign_member_count
    assert len(sign_date) == self.__sign_member_count

    return sign_rank, sign_name, sign_date

  def _fill_sign_member(self):
    sign_member, _, sign_name, _ = self._sign_members()

    assert sign_name[0] is not None
    doc = self.soup.decode(False)

    for idx in range(1, self.__sign_member_count):
      # TODO: 그냥 bs4.Tag.replace_with로 바꿀 수 없나...
      if sign_name[idx] is None:
        sm1 = sign_member[idx].decode()
        sm0 = sign_member[idx - 1].decode()

        assert sm1 in doc
        doc = doc.replace(sm1, sm0)

    self._soup = bs4.BeautifulSoup(markup=doc, features='html.parser')
    self._member, self._rank, self._name, self._date = self._sign_members()

  def _fix_sign_date(self):
    _, _, _, sign_date = self._sign_members()

    first_date = datetime.datetime.strptime(sign_date[0].string.strip(),
                                            self.__ymd_format)

    for idx in range(1, self.__sign_member_count):
      text = sign_date[idx].string.strip()
      if '전결' in text:
        date = datetime.datetime.strptime(text.replace('(전결)', ''),
                                          self.__md_format)
        fixed_date = datetime.date(first_date.year, date.month, date.day)
        fixed_text = datetime.date.strftime(fixed_date, self.__ymd_format)
        sign_date[idx].string.replace_with(fixed_text)

    self._member, self._rank, self._name, self._date = self._sign_members()

  def _sign_members(self):
    sign_member = self.soup.find_all(name='span',
                                     attrs={'class': 'sign_member'})
    assert len(sign_member) == self.__sign_member_count

    sign_rank, sign_name, sign_date = self._sign_members_helper(sign_member)

    # sign_rank_string = [str(x.string).strip() for x in sign_rank]
    # if sign_rank_string != list(self.__default_rank):
    #   warn('직급 순서가 예상과 달라 오류가 발생할 수 있음: {}'.format(sign_rank_string))

    assert len(sign_rank) == self.__sign_member_count
    assert len(sign_name) == self.__sign_member_count
    assert len(sign_date) == self.__sign_member_count

    return sign_member, sign_rank, sign_name, sign_date

  def fix_sign(self):
    if any(x is None for x in self._name):
      self._fill_sign_member()
      self._fix_sign_date()

  def save(self, path):
    with open(path, 'w', encoding='utf-8-sig') as f:
      f.write(str(self._soup.prettify()))

  def change_label(self, label: str, text: str):
    if label not in self.__label:
      raise ValueError('Invalid label: {}'.format(label))

    tag = self.soup.find(name='span',
                         attrs={'data-dsl': '{{label:' + str(label) + '}}'})
    tag.string.replace_with(text)

  def change_sign_rank(self, ranks: list):
    for tag, rank in zip(self._rank, ranks):
      if tag and rank:
        tag.string.replace_with(rank)

  def change_sign_name(self, names: list):
    for tag, name in zip(self._name, names):
      if tag and name:
        tag.string.replace_with(name)

  def change_sign_date(self, dates: list):
    for tag, date in zip(self._date, dates):
      if tag and date:
        tag.string.replace_with(date)

  def change_image_source(self):
    if os.path.exists(_STAMP_PATH):
      imgs = self.soup.find_all(name='img')
      for img in imgs:
        img.attrs['src'] = 'file:///{}'.format(_STAMP_PATH)


class Runner:

  def __init__(self) -> None:
    doc_dir = os.path.abspath(os.path.join(_FILE_DIR, '../../documents'))
    lstdir = os.listdir(doc_dir)

    drafts = [os.path.join(doc_dir, x) for x in lstdir if x.endswith('html')]
    if not drafts:
      warn('변환할 문서가 없습니다.')

    self._drafts = drafts

    option_path = os.path.abspath(os.path.join(_FILE_DIR, '../../option.json'))
    if not os.path.exists(option_path):
      raise FileNotFoundError('Option 파일이 없습니다: {}'.format(option_path))

    with open(option_path, 'r', encoding='utf-8') as f:
      self._option: OrderedDict = json.load(f, object_pairs_hook=OrderedDict)

  def run(self, drafts=None):
    if drafts is None:
      drafts = self._drafts

    res_dir = os.path.normpath(os.path.join(_FILE_DIR, '../../pdf'))
    if not os.path.exists(res_dir):
      os.makedirs(res_dir)

    for path in drafts:
      draft = DaouDraft(path)
      draft.fix_sign()
      draft.change_image_source()

      fname = os.path.split(path)[1]
      print('\n\n' + fname)

      for pattern, options in self._option.items():
        if not pattern.startswith('.*'):
          pattern = '.*' + pattern

        if pattern == '.*' or re.match(pattern, fname):
          print('{}: 옵션 "{}"'.format(fname, pattern))

          for key, value in options.items():
            if key.startswith('doc') or key.startswith('draft'):
              draft.change_label(key, value)
            elif key == 'signName':
              draft.change_sign_name(value)
            elif key == 'signRank':
              draft.change_sign_rank(value)
            elif key == 'signDate':
              draft.change_sign_date(value)
            else:
              warn('잘못된 옵션: {}: {}'.format(key, value))

      res_path = os.path.normpath(os.path.join(res_dir, fname))
      draft.save(res_path)
      to_pdf(res_path)


def to_pdf(html_path):
  dir_, fname = os.path.split(html_path)
  fname = os.path.splitext(fname)[0]
  pdf_path = os.path.join(dir_, fname + '.pdf')

  args = [
      _WKHTMLTOX_PATH, '-L', '20', '-R', '20', '-T', '20', html_path, pdf_path
  ]
  run(args)
