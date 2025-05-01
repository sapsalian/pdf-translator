from styled_translate.assign_style import SpanStyle
import pymupdf

# 스타일에 따라 알맞은 폰트 경로를 선택하고 fitz.Font 인스턴스를 반환
font_cache = {}  # 캐싱하여 중복 로딩 방지

def getFont(style: SpanStyle) -> pymupdf.Font:
    key = (style.is_bold, style.is_italic)
    path_map = {
        (False, False): "./static/NotoSansKR-Regular.ttf",
        (True, False): "./static/NotoSansKR-Bold.ttf",
        (False, True): "./static/NotoSansKR-Regular.ttf",
        (True, True): "./static/NotoSansKR-Bold.ttf"
    }
    path = path_map.get(key, "./static/NotoSansKR-Regular.ttf")

    if path not in font_cache:
        font_cache[path] = pymupdf.Font(fontfile=path)
    return font_cache[path]
  
  
def getFontPath(style: SpanStyle) -> str:
    key = (style.is_bold, style.is_italic)
    path_map = {
        (False, False): "./static/NotoSansKR-Regular.ttf",
        (True, False): "./static/NotoSansKR-Bold.ttf",
        (False, True): "./static/NotoSansKR-Regular.ttf",
        (True, True): "./static/NotoSansKR-Bold.ttf"
    }
    path = path_map.get(key, "./static/NotoSansKR-Regular.ttf")

    return path
  

def getFontName(style: SpanStyle) -> str:
    key = (style.is_bold, style.is_italic)
    name_map = {
        (False, False): "kr-regular",
        (True, False): "kr-bold",
        (False, True): "kr-regular",
        (True, True): "kr-bold"
    }
    name = name_map.get(key, "./static/NotoSansKR-Regular.ttf")

    return name