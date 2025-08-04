import pymupdf
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.console_utils import print_error

def lineText(line) :
  text = ""
  prev_span = None

  for span in line["spans"]:
    if prev_span is not None:
      # 현재 span과 이전 span의 x좌표 간격 계산
      prev_end = prev_span["bbox"][2]  # 이전 span의 끝 x좌표
      curr_start = span["bbox"][0]     # 현재 span의 시작 x좌표
      gap = curr_start - prev_end

      # 평균 글자 너비 계산
      prev_width = prev_span["bbox"][2] - prev_span["bbox"][0]
      curr_width = span["bbox"][2] - span["bbox"][0]
      prev_char_width = prev_width / max(len(prev_span["text"]), 1)
      curr_char_width = curr_width / max(len(span["text"]), 1)
      avg_char_width = (prev_char_width + curr_char_width) / 2

      # 공백 조건 확인: 간격이 평균 글자 너비의 0.9배 이상이면 공백 추가
      if gap >= avg_char_width * 0.9:
        text += " "

    text += span["text"]
    prev_span = span

  return text

def blockText(block):
  text = ""
  for line in block["lines"]:
    text += lineText(line) + '\n'
  return text


def getBlockTextsWithUnicodeEscape(blocks):
    blockTexts = []
    for block in blocks:
        text = blockText(block)
        escapedText = ''.join(
            c if c.isascii() and (c.isalpha() or c.isspace()) else f'\\u{ord(c):04x}' for c in text
        )
        blockTexts.append(escapedText)
    return blockTexts

def printEscapedBlocksFromPdf(filePath, pageNum):
    doc = pymupdf.open(filePath)
    if pageNum < 0 or pageNum >= len(doc):
        print_error(f"페이지 번호 {pageNum}는 유효하지 않습니다. 총 페이지 수: {len(doc)}")
        return

    page = doc[pageNum]
    blocks = page.get_text("dict")["blocks"]
    escapedBlocks = getBlockTextsWithUnicodeEscape(blocks)

    for block_text in escapedBlocks:
        print(block_text)
        print("\n")  # 엔터 두 번

