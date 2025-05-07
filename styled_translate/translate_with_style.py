from styled_translate.assign_style import assignSpanStyle
from styled_translate.find_primarystyle import assignPrimaryStyleId
from styled_translate.translate_block import translateBlock, blockTextWithStyleTags
from styled_translate.draw_styled_blocks import renderStyledSpans
from text_edit.text_delete import deleteTextBlocks
from text_extract.text_extract import blockText

def translateWithStyle(blocks, page):
  deleteTextBlocks(page, blocks)
  
  style_dict = assignSpanStyle(blocks)
  assignPrimaryStyleId(blocks, style_dict)
  
  for block in blocks:
    # 호출되고 나면 내부에 styled_lines 들어가 있음.
    while True:
        try:
            translateBlock(block, style_dict)
            break  # 성공하면 반복 종료
        except Exception as e:
            print(f"오류 발생: {e}, 재시도합니다...")
            print(f"오류 발생 위치: ")
            print(f"page: {page.number + 1}, block: {blockText(block)}")
    
  renderStyledSpans(blocks, style_dict, page)
    
  return style_dict
  
  
  

def translateWithStyleTest(blocks, page):
  style_dict = translateWithStyle(blocks, page)

  for style_id, style in style_dict.items():
      print(f"[{style_id}] {style}")

  for block in blocks:
      # print(block["primary_style_id"])
      print(blockTextWithStyleTags(block, style_dict))
      print(translateBlock(block, style_dict))
      print("--------------------------")
    
  