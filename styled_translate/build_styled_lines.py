from typing import List, Dict
from styled_translate.get_font import getFont
from styled_translate.assign_style import SpanStyle, dirToRotation


class NoMoreLinesError(Exception):
    """더 이상 글자를 넣을 line이 존재하지 않을 때 발생"""
    def __init__(self, message="더 이상 글자를 삽입할 줄이 없습니다."):
        super().__init__(message)


def getCharWidths(styled_span: Dict, style_dict: Dict[int, 'SpanStyle']) -> List[float]:
    """
    styled_span과 style_dict를 사용해 char_widths를 반환하는 함수.

    Parameters:
        styled_span (dict): {"text": ..., "style_id": ...} 형식의 span
        style_dict (dict): style_id -> SpanStyle 객체를 매핑한 딕셔너리

    Returns:
        List[float]: 글자 하나하나의 너비 리스트
    """
    text = styled_span["text"]
    style_id = styled_span["style_id"]
    font_family = styled_span["font_family"]
    style = style_dict[style_id]
    font = getFont(style, font_family)  # SpanStyle 기반 폰트 객체 반환 함수
    char_widths = font.char_lengths(text, fontsize=style.font_size)  # tuple로 반환됨
    return list(char_widths)

def getXgap(styled_span: Dict, style_dict: Dict[int, 'SpanStyle']) -> float:
    style_id = styled_span["style_id"]
    style = style_dict[style_id]
    
    return style.x_gap_with_prev

def getLineXLimit(lines: List[Dict], line_idx: int) -> float:
  line = lines[line_idx]
  rotate = dirToRotation(line["dir"])
  
  x0, y0, x1, y1 = line["bbox"]
  
  if rotate == 0 or rotate == 180:
      return x1 - x0
  elif rotate == 90 or rotate == 270:
      return y1 - y0
  
  return x1 - x0 

def getSpanChar(styled_span: Dict, char_idx: int) -> str:
    text = styled_span["text"]
   
    return text[char_idx]
  
def countLinesByLineBreak(styled_spans: List[Dict]):
    text = ""
    for span in styled_spans:
        text += span["text"]
        
    return len(text.splitlines())
  
  


def buildStyledLines(styled_spans: List[Dict], style_dict: Dict[int, 'SpanStyle'], lines: List[Dict]) -> List[Dict]:
    positioned_lines = []  # line 객체들의 list. 반환될 값
    
    # line 하나 꺼내기
    line_idx = 0
    if  line_idx >= len(lines):
        # 넣을 line이 없다면 예외 발생시키기.
        raise NoMoreLinesError()
    x_limit = getLineXLimit(lines, line_idx) 
    cur_x = 0 # 현재 line에서 char 넣은데까지 x좌표 (line 시작점에서의 상대적인 좌표)
    span_start_x = 0  # 현재 span의 시작 x좌표 (line 시작점에서의 상대적인 좌표)
    positioned_spans = []
    
    
    # span 하나 꺼내기( 이후 새로 꺼낼때는 먼저 현재 span부터 저장해야함.)
    span_idx = 0 # style_spans 인덱스
    if span_idx >= len(styled_spans):
        # span이 아예 없는 것이므로 빈 리스트 반환
        return positioned_lines
    cur_span = styled_spans[span_idx]  # 현재 탐색중인 span
    char_widths = getCharWidths(cur_span, style_dict)  # 현재 탐색중인 span에서 얻은 char_widths
    char_idx = 0  # 현재 넣을 문자 index(cur_sapn에서)
    new_span_text = ""  # 현재 positioned_span에 들어가기 위해 쌓인 text
    cur_x += getXgap(cur_span, style_dict)
    span_start_x = cur_x
    
    
    # styled_spans 전체 text를 개행으로 나눴을 때 나오는 줄 수가 lines 줄 수랑 같은지 미리 확인해놓기.
    # 같은 경우에는 bbox 넘어가는거 상관없이 개행에서만 다음 line으로 넘어가도록 적용해야함.
    is_line_fixed = (countLinesByLineBreak(styled_spans) == len(lines))
    
    while True:
        
        if getSpanChar(cur_span, char_idx) == "\n":
            # 현재 character가 개행이면, 현재 line 저장하고 다음 line bbox로 갱신.
            # 그 후 char_idx 증가시켜주기
            
            # positioned span 만들어 positioned spans에 저장
            if new_span_text:
                positioned_spans.append({
                    'style_id': cur_span['style_id'],
                    'font_family': cur_span['font_family'],
                    'rel_x': span_start_x,
                    'text': new_span_text,
                    'width': cur_x - span_start_x
                })
            
            # positioned line 객체 만들어 positioned lines에 넣기
            positioned_lines.append({
                'positioned_spans': positioned_spans,
                'line_width': cur_x
            })
            
            # line 하나 꺼내기
            line_idx += 1
            if  line_idx >= len(lines):
                # line 다 쓴거면 char 하나 넘겨서 더 넣을 문자 있는지 확인하기.
                # line은 다 썼는데 더 넣을 char 이나 span 남아 있으면 오류 발생
                if (char_idx + 1 < len(char_widths)) or (span_idx + 1 < len(styled_spans)):
                    # char이나 span 더 넣을 거 남아 있으면 오류 발생
                    raise NoMoreLinesError()
                
                # 개행이 블락의 마지막 문자였다면, 다 넣은거니까 positioned_lines 반환
                return positioned_lines
            x_limit = getLineXLimit(lines, line_idx) 
            cur_x = 0 # 현재 line에서 char 넣은데까지 x좌표
            span_start_x = 0  # 현재 span의 시작 x좌표 (line 시작점에서의 상대적인 좌표)
            new_span_text = ""
            positioned_spans = []
        
        elif (not is_line_fixed) and (cur_x + char_widths[char_idx] > x_limit):
            # 현재 character 더했을 때 bbox를 넘어가면, 현재 line 저장하고 다음 line bbox로 갱신.
            # 개행에 따라서만 line 나눠줘야 하는 경우는 그냥 넘어가기
            # 그 후 char_idx 갱신되지 않고 그대로 두기 위해 continue
            
            # positioned span 만들어 positioned spans에 저장
            if new_span_text:
                positioned_spans.append({
                    'style_id': cur_span['style_id'],
                    'font_family': cur_span['font_family'],
                    'rel_x': span_start_x,
                    'text': new_span_text,
                    'width': cur_x - span_start_x
                })
            
            # positioned line 객체 만들어 positioned lines에 넣기
            positioned_lines.append({
                'positioned_spans': positioned_spans,
                'line_width': cur_x
            })
            
            # line 하나 꺼내기
            line_idx += 1
            if  line_idx >= len(lines):
                # bbox 넘어갔는데 line 다 썼으면, 아직 넣을 문자 있는데 line이 부족한 것이므로 무조건 오류 발생
                raise NoMoreLinesError()
            x_limit = getLineXLimit(lines, line_idx) 
            cur_x = 0 # 현재 line에서 char 넣은데까지 x좌표
            span_start_x = 0  # 현재 span의 시작 x좌표 (line 시작점에서의 상대적인 좌표)
            new_span_text = ""
            positioned_spans = []
            
            # char_idx 증가시키지 않도록 다음 반복으로 바로 넘김.
            continue
        
        else:
            # character 더했을 때 bbox를 안넘어가는 경우에만, character 더해주기
            # 현재 character 더해주기
            
            new_span_text += cur_span["text"][char_idx]
            cur_x += char_widths[char_idx]
        
        
        # char 하나 증가시키기(span 다 썼으면, 현재 span 저장하고 새로운 span으로 갱신)
        char_idx += 1
        
        if char_idx >= len(char_widths):
            # char 다 꺼내 썼을 때는, 현재 span positioned span 만들어 저장하고 span 새로 하나 꺼내기
            
            # 쌓인거 positioned span 만들어 positioned spans에 저장
            if new_span_text:
                positioned_spans.append({
                    'style_id': cur_span['style_id'],
                    'font_family': cur_span['font_family'],
                    'rel_x': span_start_x,
                    'text': new_span_text,
                    'width': cur_x - span_start_x
                })
            
            # span 새로 하나 꺼내기
            span_idx += 1
            
            if span_idx >= len(styled_spans):
                # span 다 썼으면, positioned_line 만들어 lines에 저장해주고 반환.
                
                # positioned line 객체 만들어 positioned lines에 넣기
                positioned_lines.append({
                    'positioned_spans': positioned_spans,
                    'line_width': cur_x
                })
                
                return positioned_lines
            
            cur_span = styled_spans[span_idx]  # 현재 탐색중인 span
            char_widths = getCharWidths(cur_span, style_dict)  # 현재 탐색중인 span에서 얻은 char_widths
            char_idx = 0  # 현재 넣을 문자 index(cur_sapn에서)
            new_span_text = ""  # 현재 positioned_span에 들어가기 위해 쌓인 text
            cur_x += getXgap(cur_span, style_dict)
            span_start_x = cur_x
  