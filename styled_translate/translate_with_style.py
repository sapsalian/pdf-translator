from styled_translate.assign_style import assignSpanStyle
from styled_translate.find_primarystyle import assignPrimaryStyleId
from styled_translate.translate_block import translateBlock, blockTextWithStyleTags
from styled_translate.translate_blocks import makeTranslatedStyledSpans
from styled_translate.draw_styled_blocks import replaceTranslatedBlocks
from styled_translate.mark_to_be_translated import assignToBeTranslated

def translateWithStyle(page_info, term_dict, src_lang, target_lang):
    blocks = page_info.get("blocks", [])
    page_num = page_info["page_num"]
    
    assignToBeTranslated(blocks, src_lang, target_lang)
    
    page_info["style_dict"] = assignSpanStyle(blocks, src_lang, target_lang)
    assignPrimaryStyleId(blocks, page_info["style_dict"])
    
    makeTranslatedStyledSpans(blocks, page_info["style_dict"], page_info["summary"], page_num, term_dict, src_lang, target_lang)
        
    return page_info["style_dict"]
  
  
  

def translateWithStyleTest(blocks, page, src_lang, target_lang):
  style_dict = translateWithStyle(blocks, page, src_lang, target_lang)

  for style_id, style in style_dict.items():
      print(f"[{style_id}] {style}")

  for block in blocks:
      # print(block["primary_style_id"])
      print(blockTextWithStyleTags(block, style_dict))
      print(translateBlock(block, style_dict))
      print("--------------------------")
    
  