# DaouDraft

- 다우오피스 (Daou Office) 전자결재 문서를 수정 및 PDF로 변환
- 현재 (작성자 포함) 결재자가 4명인 경우만 지원 (5명 이상에도 적용 가능하도록 수정 예정)

## 실제 기안 문서의 PDF 변환

다우오피스를 통해 결재받은 실제 기안을 정보 변경 및 PDF 변환

### 실행 방법

1. 다우오피스 전자결재 문서를 다운로드 받고 파일을 `./documents` 폴더에 저장
2. `./run_draft.bat` 파일 실행 (혹은 cmd에서 `run --mode=draft` 입력)
3. `./pdf` 폴더에 변환된 HTML 문서와 PDF 문서가 생성됨

하단의 옵션 설정에 따라 문서 번호, 기안 날짜, 부서, 작성자, 결재자, 결재일 정보가 수정됨. 전결 문서인 경우 마지막 결재자까지 결재 표시가 나타나도록 수정.

기본 설정은 **(작성자 포함) 결재자가 4명인 경우에 맞춰저 있음**

프로그램 실행 관련 정보, 에러 메세지는 `./log.txt`에 저장됨.

### 옵션 설정 방법

`./option_draft.yaml` 문서를 통해 옵션을 설정함 (YAML 포맷에 대한 설명은 [위키피디아](https://ko.wikipedia.org/wiki/YAML) 참조).

기본 설정/예시 구문은 다음과 같음.

```yaml
---
- ".*":
    signName:
      -
      -
      -
      - 대표이사이름 # 결재자가 4명인 경우 마지막 (대표이사) 이름 변경
- example_blank:
    docNo: 문서 번호
    draftDate: 2015-10-21(수)
    draftDept: 부서
    draftUser: 기안 작성자
    signName:
      - 작성자
      - 결재자1
      - 결재자2
      - 결재자3
    signRank:
      - 직급1
      - 직급2
      - 직급3
      - 직급3
    signDate:
      - 2015/10/21
      - 2016/10/21
      - 2017/10/21
      - 2018/10/21
- example_five:
    signName:
      # 원본 문서는 5명이지만 4명 정보를 입력했기 때문에 경고 발생
      - 작성자
      - 결재자1
      - 결재자2
      - 결재자3
- 친환경:
    draftUser: 작성자2
    signName:
      - 작성자2
      -
      -
      - 대표이사이름
    wrongOption: null # 잘못된 설정 (경고 발생)
```

- `".*"`, `example`, `친환경`: 옵션을 적용할 파일 설정
  - `".*"`은 모든 파일에 적용되는 옵션을 뜻함 (기본적으로 마지막 결재자 (대표이사)의 이름 변경 옵션이 적용되어 있음).
  - 예를 들어 `친환경`을 입력할 경우, `./documents`에 있는 html 파일 중 이름에 `친환경`이 포함되는 파일에만 하단의 옵션이 적용됨.
  - 여러 옵션이 해당되는 경우, 위부터 순차적으로 적용됨 (따라서 `".*"` 옵션을 제일 먼저 적용).
- `docNo`: 표시될 문서 번호
- `draftDate`: 작성자가 결재를 요청한 날짜
- `draftDept`: 부서 이름
- `draftUser`: 기안 작성자 (좌측 표에 표기되는 작성자 이름)
- `signName`: 결재자 정보
  - `- "작성자/결재자 이름"` 형식으로 입력
  - `-` 다음이 공백인 경우 원본 HTML 문서의 해당 작성자/결재자를 변경하지 않음
  - 기본 기안 양식과 동일하게 4명만 지정 가능
- `signRank`: 기안 작성자/결재자의 직급

  - 설정/작동 방식은 `signName`과 동일

- `signDate`: 기안 작성/결재 날짜

  - 설정/작동 방식은 `signName`과 동일

- 입력 방식에 어긋나여 적용되지 않은 옵션이 존재하는 경우 실행 시 경고가 표시됨

  - 예시: `wrongOption: null`를 입력한 경우

    > `[2020-09-08 16:18:58,875][WARNING] draft.daou_draft.DaouDraft:L178 잘못된 옵션: "wrongOption: None"`

## 템플릿으로부터 PDF 생성

실제 다우오피스를 통한 결재를 받지 않는 연구비 증빙 문서 (야근식대, 인쇄비 결재)를 템플릿으로부터 생성.

### 실행 방법

1. `./option_draft.yaml`을 통해 과제 기본 정보 입력
2. `./option_template.yaml`을 통해 생성할 문서의 정보 입력
3. `./run_template.bat` 파일 실행 (혹은 cmd에서 `run --mode=template` 입력)
4. `./pdf` 폴더에 HTML 문서와 PDF 문서가 생성됨

**과제별 기안 작성자, 결재자 이름, 직급 등의 정보는 실제 기안 문서를 변경할 때와 마찬가지로 `./option_draft.yaml` 설정을 따름**

**템플릿은 결재자 4인 기준으로 작성되어 있음. 결재 정보 등 기타 수정사항이 있으면 `./src/template/`에 위치한 템플릿 직접 수정**

프로그램 실행 관련 정보, 에러 메세지는 `./log.txt`에 저장됨.

### 옵션 설정 방법

`./option_template.yaml` 문서를 통해 개별 증빙의 옵션을 설정함 (YAML 포맷에 대한 설명은 [위키피디아](https://ko.wikipedia.org/wiki/YAML) 참조).

예시 구문은 다음과 같음.

```yaml
---
야근식대:
  사업: 사업명
  과제: 과제명
  연차: 1차 연도
  연구 기간:
    - 2019.04.19
    - 2019.12.31
  기안 제목: 야근 식대 지출의 건

  목록:
    - 2019.08.01:
        인력:
          - 야근자 1
          - 야근자 2
        업무: 야근 내용

    - 2019.09.01:
        인력:
          - 야근자 3
          - 야근자 4
          - 야근자 5
        업무: 야근 내용2

인쇄비:
  사업: 사업명
  과제: 과제명
  연차: 1차 연도
  연구 기간:
    - 2019.04.19
    - 2019.12.31
  기안 제목: 인쇄비 지출의 건

  목록:
    - 2019.08.01:
        구매 목적: 연구 참조 자료 인쇄
        구매 내역: 인쇄 출력비
```

- 생성하려는 문서 종류 (`야근식대`, `인쇄비`) 항목 아래에 과제/사용 정보를 입력
- `사업`, `과제`, `연차`, `연구기간`, `기안 제목`: _더 이상의 자세한 설명은 생략한다._
- `목록`: 생성하는 개별 문서의 정보 입력
  - 날짜 (`yyyy.mm.dd` 포맷): 지출 날짜. 각 날짜별로 문서가 생성되며, 개수 제한 없음.
  - `인력`, `업무`, `구매 목적`, `구매 내역`: 내부 결재문서 증빙에 필요한 개별 항목들

## 기타

`./logging.yaml` 파일 설정에 따라 `./log.txt`에 저장되는 정보 수준이 결정됨. 문제 발생 시 `level` 항목을 모두 `level:DEBUG`로 바꾸고 입력·옵션·로그 파일을 제보...해주세요.

기본 설정:

```yaml
version: 1
formatters:
  basic:
    format: "[%(asctime)s][%(levelname)s] %(name)s:L%(lineno)d %(message)s"
  message:
    formate: "%(message)s"
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: message
    stream: ext://sys.stdout
  file_handler:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: basic
    filename: log.txt
    encoding: UTF-8-sig
    maxBytes: 102400
    backupCount: 1
root:
  level: DEBUG
  handlers:
    - file_handler
```

## License

```text
/*
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * gypark wrote this file.  As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.
 * ----------------------------------------------------------------------------
 */
```
