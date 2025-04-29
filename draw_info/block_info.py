def drawAlignmentLabel(page, block, font_size=8):
    align = block.get("align", "")
    if not align:
        return

    x0, y0, _, _ = block["bbox"]
    label_pos = (x0, y0 - font_size - 1)  # 블럭 상단 바로 위

    page.insert_text(
        label_pos,
        align.upper(),  # 예: CENTER, LEFT, RIGHT
        fontsize=font_size,
        fill=(1, 0, 0),  # 빨간색
    )
    
def drawClassNameLable(page, block, font_size=8):
    class_name = block.get("class_name", "")
    if not class_name:
        return

    x0, y0, _, _ = block["bbox"]
    label_pos = (x0, y0 - font_size - 1)  # 블럭 상단 바로 위

    page.insert_text(
        label_pos,
        class_name.upper(),  
        fontsize=font_size,
        fill=(0, 1, 0),  # 초록색
    )