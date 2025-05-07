from styled_translate.assign_style import assignSpanStyle
from styled_translate.find_primarystyle import assignPrimaryStyleId
from styled_translate.translate_block import translateBlock, blockTextWithStyleTags, makeTranslatedStyledSpans
from styled_translate.draw_styled_blocks import replaceTranslatedBlocks
from styled_translate.mark_to_be_translated import assignToBeTranslated

def translateWithStyle(blocks, page):
  assignToBeTranslated(blocks)
  
  style_dict = assignSpanStyle(blocks)
  assignPrimaryStyleId(blocks, style_dict)
  
  makeTranslatedStyledSpans(blocks, style_dict, page)
    
  replaceTranslatedBlocks(blocks, style_dict, page)
    
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
    
  