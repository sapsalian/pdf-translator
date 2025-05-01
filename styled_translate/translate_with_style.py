from styled_translate.assign_style import assignSpanStyle
from styled_translate.find_primarystyle import assignPrimaryStyleId
from text_extract.text_extract import *

def translateWithStyle(blocks):
  style_dict = assignSpanStyle(blocks)
  assignPrimaryStyleId(blocks, style_dict)
  
  
  return style_dict
  
  
  

def translateWithStyleTest(blocks):
  style_dict = translateWithStyle(blocks)

  for style_id, style in style_dict.items():
      print(f"[{style_id}] {style}")

  for block in blocks:
      print(block["primary_style_id"])
      print(blockText(block))
    
  