def splitBlocksByLineGap(blocks):
    """
    각 block의 line들을 분석해 y축 겹침 비율이 50% 이상이고
    x축 간격이 작은 폰트크기 * 6을 초과할 경우 block을 분리합니다.

    각 분리된 block에는 lines, bbox, type, class_name이 반드시 포함됩니다.
    class_name이 없으면 "Text"로 명시합니다.
    """
    new_blocks = []

    for block in blocks:
        if "lines" not in block or not block["lines"]:
            new_blocks.append({
                "lines": [],
                "bbox": block.get("bbox", [0, 0, 0, 0]),
                "type": block.get("type"),
                "class_name": block.get("class_name", "Text")
            })
            continue

        lines = block["lines"]
        current_block = {
            "type": block.get("type"),
            "class_name": block.get("class_name", "Text"),
            "bbox": list(lines[0]["bbox"]),
            "lines": [lines[0]]
        }

        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            curr_line = lines[i]

            # y축 겹침 계산
            y0_prev, y1_prev = prev_line["bbox"][1], prev_line["bbox"][3]
            y0_curr, y1_curr = curr_line["bbox"][1], curr_line["bbox"][3]
            y_overlap = max(0, min(y1_prev, y1_curr) - max(y0_prev, y0_curr))
            y_min_height = min(y1_prev - y0_prev, y1_curr - y0_curr)
            y_overlap_ratio = y_overlap / y_min_height if y_min_height else 0

            # x 간격 계산 (음수 보정)
            x_gap = curr_line["bbox"][0] - prev_line["bbox"][2]
            if x_gap < 0:
                x_gap = prev_line["bbox"][0] - curr_line["bbox"][2]

            # 폰트 크기 계산
            def get_font_size(line):
                spans = line.get("spans", [])
                return sum(span["size"] for span in spans) / len(spans) if spans else 0

            font_size = min(get_font_size(prev_line), get_font_size(curr_line))

            # 분리 조건: y축 50% 이상 겹침 and x간격 > font_size * 6
            if y_overlap_ratio >= 0.5 and x_gap > font_size * 6:
                new_blocks.append(current_block)
                current_block = {
                    "type": block.get("type"),
                    "class_name": block.get("class_name", "Text"),
                    "bbox": list(curr_line["bbox"]),
                    "lines": [curr_line]
                }
            else:
                current_block["lines"].append(curr_line)
                # bbox 확장
                current_block["bbox"][0] = min(current_block["bbox"][0], curr_line["bbox"][0])
                current_block["bbox"][1] = min(current_block["bbox"][1], curr_line["bbox"][1])
                current_block["bbox"][2] = max(current_block["bbox"][2], curr_line["bbox"][2])
                current_block["bbox"][3] = max(current_block["bbox"][3], curr_line["bbox"][3])

        new_blocks.append(current_block)

    return new_blocks
