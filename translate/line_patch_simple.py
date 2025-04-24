from translate.block_translate import translateBlock
from preprocess.preprocess import preProcess
from text_edit.text_delete import deleteTextBlocks
import pymupdf

font_path = "./static/NotoSansKR-Regular.ttf"
font = pymupdf.Font(fontfile=font_path)

def draw_text_within_line_fast(page, line, text, char_widths, start_index):
    """
    텍스트 배열 중 start_index부터 시작해서, line에 맞는 범위까지만 삽입하고
    개행 문자('\n')가 있으면 그 전까지만 출력.
    다음 시작 인덱스를 반환.
    """
    bbox = line["bbox"]
    x, y = bbox[0], bbox[3]
    max_width = bbox[2] - bbox[0]

    fontsize = line["spans"][0].get("size", 12) * 0.8

    acc_width = 0
    end_index = start_index

    for i in range(start_index, len(char_widths)):
        if text[i] == '\n':
            end_index = i  # 개행 앞까지만 출력
            break

        acc_width += char_widths[i]
        if acc_width > max_width:
            break

        end_index = i + 1

    fitting_text = text[start_index:end_index]

    page.insert_text(
        (x, y),
        fitting_text,
        fontfile=font_path,
        fontname="dynamic-hangul",
        fontsize=fontsize,
        fill=(0, 0, 0)
    )

    # 다음 줄로 넘어갈 때는 개행도 넘겨줘야 하므로 +1
    if end_index < len(text) and text[end_index] == '\n':
        end_index += 1

    return end_index



def draw_text_in_block(page, block, text):
    """
    block 내 line들에 맞춰서 text를 index 기반으로 잘라가며 삽입.
    """
    fontsize = block["lines"][0]["spans"][0].get("size", 12) * 0.8
    char_widths = font.char_lengths(text, fontsize=fontsize)

    index = 0
    for line in block.get("lines", []):
        if index >= len(text.strip()):
            break
        index = draw_text_within_line_fast(page, line, text, char_widths, index)

        

if __name__ == "__main__":
  doc = pymupdf.open("b.pdf")
  
  for page in doc:
    # read page text as a dictionary, suppressing extra spaces in CJK fonts
    blocks = preProcess(page)
    deleteTextBlocks(page, blocks)
        
    for b in blocks:
        draw_text_in_block(page, b, translateBlock(b))
        
  doc.save("draw_bbox_b.pdf", garbage=3, clean=True, deflate=True)
        


