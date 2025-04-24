import pymupdf
import math

def dir_to_rotation(dir):
    x, y = dir
    # 벡터 (cos, -sin) 기반 → 각도 계산 (역으로 원래 각도로 돌리기)
    angle_rad = math.atan2(-y, x)
    angle_deg = (math.degrees(angle_rad)) % 360

    # 가장 가까운 90의 배수로 반올림
    closest_90 = int(round(angle_deg / 90.0)) * 90 % 360
    return closest_90

def int_to_rgb(color_int):
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r / 255, g / 255, b / 255)

def flag_to_font(flags):
    if flags & 2 ** 4 and flags & 2 ** 1:
      # return 'notosbi' 
      return 'Helvetica-BoldOblique'
    if flags & 2 ** 4:
      # return 'notosbo'
      return 'Helvetica-Bold'
    if flags & 2 ** 1:
      # return 'notosit'
      return 'Helvetica-Oblique'
    # return 'notos'
    return 'helv'


doc = pymupdf.open("b.pdf")

for page in doc[6:8]:
  # read page text as a dictionary, suppressing extra spaces in CJK fonts
  blocks = page.get_text("dict")["blocks"] 
  for b in blocks:  # iterate through the text blocks # b = 하나의 블락 잡아주는 듯
      for l in b.get("lines", []):  # iterate through the text lines # line = 한 줄에 있는 텍스트 모두

          deg = dir_to_rotation(l["dir"])

          for s in l["spans"]:  # iterate through the text spans # s = 한 줄 내에서도 글꼴이 달라지거나 하면 span으로 잡히는 듯
              print("")
              
              [left,up,right,low] = s["bbox"]
              
              quad = pymupdf.Quad(pymupdf.Point(left,up),pymupdf.Point(right, up), pymupdf.Point(left, low), pymupdf.Point(right, low))
              page.add_redact_annot(quad)
              
          page.apply_redactions(0)
          
          
          for s in l["spans"]:
              print(s)
              
              p = s["origin"]
              print(s["color"])
              rc = page.insert_text(p,  # bottom-left of 1st char
                      s["text"],  # the text (honors '\n')
                      fontname = flag_to_font(s["flags"]),
                      fontsize = s["size"],
                      color= int_to_rgb(s["color"]),
                      rotate=deg
                      )
            
doc.save("new2.pdf", garbage=3, clean=True, deflate=True)
            