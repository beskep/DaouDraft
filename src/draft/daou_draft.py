from pathlib import Path
from subprocess import run
import datetime
import logging
import os
import re
import sys

import bs4

ROOT_DIR = Path(__file__).parents[2]
SRC_DIR = ROOT_DIR / 'src'
if str(SRC_DIR) not in sys.path:
  sys.path.append(str(SRC_DIR))

from draft.read_option import read_option

WKHTMLTOX_PATH = ROOT_DIR / 'src/wkhtmltox/bin/wkhtmltopdf.exe'
STAMP_PATH = ROOT_DIR / 'src/stamp_approved.png'


class DaouDraft:

  _label = {'docNo', 'draftDate', 'draftDept', 'draftUser'}
  _ymd_format = '%Y/%m/%d'
  _md_format = '%m/%d'

  def __init__(self, path) -> None:
    self._path = path
    self._soup = self.read_soup(self._path)

    self._logger = logging.getLogger('{}.{}'.format(
        __name__, self.__class__.__qualname__))

    self._member, self._rank, self._name, self._date = self._sign_members()
    self._sign_count = len(self._member)

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

    return sign_rank, sign_name, sign_date

  def _sign_members(self):
    sign_members = self.soup.find_all(name='span',
                                      attrs={'class': 'sign_member'})

    sign_ranks, sign_names, sign_dates = self._sign_members_helper(sign_members)

    # sign_rank_string = [str(x.string).strip() for x in sign_ranks]
    # if sign_rank_string != list(self.__default_rank):
    #   self._logger.debug('직급 순서가 예상과 다름: {}'.format(sign_rank_string))

    return sign_members, sign_ranks, sign_names, sign_dates

  def _fill_sign_member(self):
    """전결이 존재하는 경우 빈 결재자 형식을 채워넣음"""

    sign_member, _, sign_name, _ = self._sign_members()

    assert sign_name[0] is not None
    doc = self.soup.decode(False)

    for idx in range(1, self._sign_count):
      # TODO: 그냥 bs4.Tag.replace_with로 바꿀 수 없나...
      if sign_name[idx] is None:
        sm1 = sign_member[idx].decode()
        sm0 = sign_member[idx - 1].decode()

        assert sm1 in doc
        doc = doc.replace(sm1, sm0)

    self._soup = bs4.BeautifulSoup(markup=doc, features='html.parser')
    self._member, self._rank, self._name, self._date = self._sign_members()

  def _fix_sign_date(self):
    """전결이 존재하는 경우 빈 날짜 형식을 채워넣음"""

    _, _, _, sign_date = self._sign_members()

    first_date = datetime.datetime.strptime(sign_date[0].string.strip(),
                                            self._ymd_format)

    for idx in range(1, self._sign_count):
      text = sign_date[idx].string.strip()
      if '전결' in text:
        date = datetime.datetime.strptime(text.replace('(전결)', ''),
                                          self._md_format)
        fixed_date = datetime.date(first_date.year, date.month, date.day)
        fixed_text = datetime.date.strftime(fixed_date, self._ymd_format)
        sign_date[idx].string.replace_with(fixed_text)

    self._member, self._rank, self._name, self._date = self._sign_members()

  def fix_sign(self):
    if any(x is None for x in self._name):
      self._logger.debug('fix_sign (names: {})'.format(self._name))
      self._fill_sign_member()
      self._fix_sign_date()

  def save(self, path):
    with open(path, 'w', encoding='utf-8-sig') as f:
      f.write(str(self._soup.prettify()))

  def change_label(self, label: str, text: str):
    if label not in self._label:
      raise ValueError('Invalid label: {}'.format(label))

    tag = self.soup.find(name='span',
                         attrs={'data-dsl': '{{label:' + str(label) + '}}'})
    tag.string.replace_with(text)

  def _warn_sign_count(self, label, values):
    self._logger.warning('''결재 정보 불일치
기안 원본의 결재자 수: {0}
입력받은 {1} 수: {2} {3}
순서대로 {1} 정보를 채웁니다.'''.format(self._sign_count, label, len(values),
                             str(tuple(values))))
    return

  def change_sign_rank(self, ranks: list):
    if self._sign_count != len(ranks):
      self._warn_sign_count(label='결재자 직급', values=ranks)

    for tag, rank in zip(self._rank, ranks):
      if tag and rank:
        tag.string.replace_with(rank)

  def change_sign_name(self, names: list):
    if self._sign_count != len(names):
      self._warn_sign_count(label='결재자 이름', values=names)

    for tag, name in zip(self._name, names):
      if tag and name:
        tag.string.replace_with(name)

  def change_sign_date(self, dates: list):
    if self._sign_count != len(dates):
      self._warn_sign_count(label='결재일', values=dates)

    for tag, date in zip(self._date, dates):
      if tag and date:
        tag.string.replace_with(date)

  def change_image_source(self):
    if os.path.exists(STAMP_PATH):
      imgs = self.soup.find_all(name='img')
      for img in imgs:
        img.attrs['src'] = 'file:///{}'.format(STAMP_PATH)

  def change_by_dict(self, options: dict):
    for key, value in options.items():
      if key.startswith('doc') or key.startswith('draft'):
        self.change_label(key, value)
      elif key == 'signName':
        self.change_sign_name(value)
      elif key == 'signRank':
        self.change_sign_rank(value)
      elif key == 'signDate':
        self.change_sign_date(value)
      else:
        self._logger.warning('잘못된 옵션: "{}: {}"'.format(key, value))


class Runner:
  _option_file = 'option_draft.yaml'

  def __init__(self) -> None:
    self._logger = logging.getLogger('{}.{}'.format(
        __name__, self.__class__.__qualname__))

    doc_dir = ROOT_DIR / 'documents'
    if not doc_dir.exists():
      self._logger.error('documents 폴더가 없습니다')
      raise FileNotFoundError(doc_dir)

    lstdir = os.listdir(doc_dir)
    drafts = [doc_dir / x for x in lstdir if x.endswith('html')]
    if not drafts:
      self._logger.warn('변환할 문서가 없습니다')
    else:
      self._logger.info('변환할 문서 목록')
      for x in drafts:
        self._logger.info(str(x))
    self._drafts = drafts
    self._option = read_option(self._option_file)

  def run(self, drafts=None):
    if drafts is None:
      drafts = self._drafts

    res_dir = ROOT_DIR / 'pdf'
    if not os.path.exists(res_dir):
      os.makedirs(res_dir)

    for path in drafts:
      draft = DaouDraft(path)
      draft.fix_sign()
      # draft.change_image_source()

      fname = os.path.split(path)[1]

      for options in self._option:
        if len(options) != 1:
          self._logger.error('Option 형식 오류: {}'.format(options))
        pattern, opts = options.copy().popitem()

        if not pattern.startswith('.*'):
          pattern = '.*' + pattern

        if pattern == '.*' or re.match(pattern, fname):
          self._logger.info('문서 "{}"에 옵션 "{}" 적용'.format(fname, pattern))
          draft.change_by_dict(options=opts)

      res_path = os.path.normpath(os.path.join(res_dir, fname))
      draft.save(res_path)
      to_pdf(res_path)


def to_pdf(html_path):
  if not WKHTMLTOX_PATH.exists():
    logger = logging.getLogger(__name__)
    logger.error('PDF 변환 불가. {} 미발견'.format(WKHTMLTOX_PATH))
    raise FileNotFoundError(WKHTMLTOX_PATH)

  dir_, fname = os.path.split(html_path)
  fname = os.path.splitext(fname)[0]
  pdf_path = os.path.join(dir_, fname + '.pdf')

  args = [
      WKHTMLTOX_PATH, '-L', '20', '-R', '20', '-T', '20', html_path, pdf_path
  ]
  run(args, capture_output=True)
