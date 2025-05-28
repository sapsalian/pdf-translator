import pymupdf

basic_font_family_map = {
    "한국어": "NotoSansKR",
}

font_family_list = [
    "NotoSansSymbols",
    "NotoSansSymbols2",
    "NotoSansMath",
    "NotoSans",
    "NotoSansKR",
]

has_bold_family_list = [
    "NotoSansSymbols",
    "NotoSans",
    "NotoSansKR",
]

has_italic_family_list = [
    "NotoSans",
]

codepoints_map = {}

for font_family in font_family_list:
    font = pymupdf.Font(fontfile=f"./static/{font_family}/{font_family}-Regular.ttf")
    codepoints = font.valid_codepoints()
    codepoints_map[font_family] = codepoints


def validCharInFontFamily(char: str, font_family: str):
    codepoints = codepoints_map[font_family]
    
    return ord(char) in codepoints


'''
target 언어, 문자하나 받아서 font_family를 문자열로 반환하는 함수
'''
def getFontFamily(char:str, target_languge: str):
    basic_font_family = basic_font_family_map[target_languge]
    
    if validCharInFontFamily(char, basic_font_family):
        return basic_font_family
    
    for font_family in font_family_list:
        if validCharInFontFamily(char, font_family):
            return font_family
        
    return "NotoSans"
    

def hasBold(font_family: str):
    
    return font_family in has_bold_family_list

def hasItalic(font_family: str):
    
    return font_family in has_italic_family_list