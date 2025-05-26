def drawLinkNumLable(page, span, font_size=4):
    link_num = span.get("link_num", None)
    if link_num is None:
        return

    x0, y0, _, _ = span["bbox"]
    label_pos = (x0, y0 - 1)  # 블럭 상단 바로 위

    page.insert_text(
        label_pos,
        f'{link_num}',
        fontsize=font_size,
        fill=(0, 1, 0),  # 초록색
    )