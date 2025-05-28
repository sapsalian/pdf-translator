from styled_translate.assign_style import SpanStyle
from styled_translate.get_font_family import hasBold, hasItalic
import pymupdf

# 스타일에 따라 알맞은 폰트 경로를 선택하고 fitz.Font 인스턴스를 반환
font_cache = {}  # 캐싱하여 중복 로딩 방지

def getFont(style: SpanStyle, font_family: str) -> pymupdf.Font:
    path = getFontPath(style, font_family)

    if path not in font_cache:
        font_cache[path] = pymupdf.Font(fontfile=path)
    return font_cache[path]
  
  
def getFontPath(style: SpanStyle, font_family: str) -> str:
    key = (style.is_bold and hasBold(font_family), style.is_italic and hasItalic(font_family))
    path_map = {
        (False, False): f"./static/{font_family}/{font_family}-Regular.ttf",
        (True, False): f"./static/{font_family}/{font_family}-Bold.ttf",
        (False, True):  f"./static/{font_family}/{font_family}-Italic.ttf",
        (True, True): f"./static/{font_family}/{font_family}-BoldItalic.ttf"
    }
    path = path_map.get(key, f"./static/{font_family}/{font_family}-Regular.ttf")

    return path
  

def getFontName(style: SpanStyle, font_family:str) -> str:
    key = (style.is_bold and hasBold(font_family), style.is_italic and hasItalic(font_family))
    name_map = {
        (False, False): f"{font_family.lower()}-regular",
        (True, False): f"{font_family.lower()}-bold",
        (False, True): f"{font_family.lower()}-italic",
        (True, True): f"{font_family.lower()}-bolditalic"
    }
    name = name_map.get(key, f"{font_family.lower()}-regular")

    return name