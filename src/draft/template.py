from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
import json
import logging
import os
import re
import sys

ROOT_DIR = Path(__file__).parents[2]
SRC_DIR = ROOT_DIR / 'src'
if str(SRC_DIR) not in sys.path:
  sys.path.append(str(SRC_DIR))

from draft.daou_draft import DaouDraft, to_pdf, read_option

TEMPLATES = ('야근식대', '인쇄비')
DATE_PATTERN = re.compile('\d{4}\.\d{2}\.\d{2}')


def read_options(fname='option.json'):
  option_path = ROOT_DIR / fname
  try:
    with open(option_path, 'r', encoding='utf-8') as f:
      option: OrderedDict = json.load(f, object_pairs_hook=OrderedDict)
  except FileNotFoundError as e:
    logger = logging.getLogger('{}.read_options'.format(__name__))
    logger.error('Option 파일이 없습니다: {}'.format(option_path))
    raise e

  return option


class DraftTemplate:

  def __init__(self, template, global_option: dict, template_option: dict):
    self._logger = logging.getLogger('{}.{}'.format(
        __name__, self.__class__.__qualname__))

    if template not in TEMPLATES:
      self._logger.error('잘못된 템플릿 이름: {}'.format(template))
      self._logger.info('가능한 템플릿 리스트: {}'.format(TEMPLATES))
      raise ValueError(template)

    if template not in template_option:
      self._logger.error('템플릿 옵션이 존재하지 않음: {}'.format(template))
      raise ValueError(template)

    path = ROOT_DIR / 'src/template/{}.html'.format(template)
    if not path.exists():
      self._logger.error('템플릿 파일 존재하지 않음: {}'.format(path))
      raise FileNotFoundError(path)

    self._template = template
    self._draft = DaouDraft(path)
    self._goption = global_option
    self._toption: dict = template_option[template]
    self.global_change()

  @property
  def goption(self):
    return deepcopy(self._goption)

  @property
  def toption(self):
    return deepcopy(self._toption)

  def global_change(self):
    project = self.toption['과제']

    for options in self.goption:
      if len(options) != 1:
        self._logger.error('Option 형식 오류: {}'.format(options))
      pattern, opts = options.popitem()

      if not pattern.startswith('.*'):
        pattern = '.*' + pattern

      if pattern == '.*' or re.match(pattern, project):
        self._logger.info('"{}" 과제에 옵션 "{}" 적용'.format(project, pattern))
        self._draft.change_by_dict(opts)

  def change_template(self):
    pass


class DraftTemplateOvertime(DraftTemplate):

  def __init__(self, global_option: dict, template_option: dict):
    super(DraftTemplateOvertime, self).__init__(template='야근식대',
                                                global_option=global_option,
                                                template_option=template_option)

  def change_template(self):
    draft = self._draft.soup.decode(pretty_print=False)
    res_dir = ROOT_DIR / 'pdf'
    if not res_dir.exists():
      os.makedirs(res_dir)

    toption = self.toption

    for key in ['사업', '과제', '연차', '기안 제목']:
      draft = draft.replace('[[{}]]'.format(key), toption[key])

    period = toption['연구 기간']
    draft = draft.replace('[[시작일]]', period[0])
    draft = draft.replace('[[종료일]]', period[1])

    for dateopt in toption['목록']:
      date, options = dateopt.popitem()
      if not DATE_PATTERN.match(date):
        self._logger.warn('일자 형식 불일치: {}'.format(date))

      draft_ = draft[:]
      draft_ = draft_.replace('[[draftDate]]', date)
      draft_ = draft_.replace('[[docNo]]',
                              '미래환경플랜건축사사무소-' + date.replace('.', ''))
      draft_ = draft_.replace('[[people]]', ', '.join(options['인력']))
      draft_ = draft_.replace('[[work]]', options['업무'])

      res_path = res_dir / '{}_{}.html'.format(self._template, date)
      with open(res_path, 'w', encoding='utf-8-sig') as f:
        f.write(draft_)

      to_pdf(res_path)


class DraftTemplatePrint(DraftTemplate):

  def __init__(self, global_option: dict, template_option: dict):
    super(DraftTemplatePrint, self).__init__(template='인쇄비',
                                             global_option=global_option,
                                             template_option=template_option)

  def change_template(self):
    draft = self._draft.soup.decode(pretty_print=False)
    res_dir = ROOT_DIR / 'pdf'
    if not res_dir.exists():
      os.makedirs(res_dir)

    toption = self.toption

    for key in ['사업', '과제', '연차', '기안 제목']:
      draft = draft.replace('[[{}]]'.format(key), toption[key])

    period = toption['연구 기간']
    draft = draft.replace('[[시작일]]', period[0])
    draft = draft.replace('[[종료일]]', period[1])

    for dateopt in toption['목록']:
      date, options = dateopt.popitem()
      if not DATE_PATTERN.match(date):
        self._logger.warn('일자 형식 불일치: {}'.format(date))

      draft_ = draft[:]
      draft_ = draft_.replace('[[draftDate]]', date)
      draft_ = draft_.replace('[[docNo]]',
                              '미래환경플랜건축사사무소-' + date.replace('.', ''))
      draft_ = draft_.replace('[[purpose]]', options['구매 목적'])
      draft_ = draft_.replace('[[item]]', options['구매 내역'])

      res_path = res_dir / '{}_{}.html'.format(self._template, date)
      with open(res_path, 'w', encoding='utf-8-sig') as f:
        f.write(draft_)

      to_pdf(res_path)


def run():
  # goption = read_options('option.json')
  # toption = read_options('option_template.json')
  goption = read_option('option_draft.yaml')
  toption = read_option('option_template.yaml')
  DraftTemplateOvertime(goption, toption).change_template()
  DraftTemplatePrint(goption, toption).change_template()
