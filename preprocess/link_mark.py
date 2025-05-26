
def markLinkToSpan(blocks, links):
    """
    링크 사각형과 span bbox의 교집합 면적 / 더 작은 면적 비율이 0.8 이상이면
    해당 span에 'link_num' 키를 할당.
    """

    for link_idx, link in enumerate(links):
        link_bbox = link.get("from")  # [x0, y0, x1, y1]

        if not link_bbox or len(link_bbox) != 4:
            continue

        lx0, ly0, lx1, ly1 = link_bbox
        if lx0 > lx1:
            lx0, lx1 = lx1, lx0
        if ly0 > ly1:
            ly0, ly1 = ly1, ly0

        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    sx0, sy0, sx1, sy1 = span.get("bbox", [0, 0, 0, 0])
                    
                    if sx0 > sx1:
                        sx0, sx1 = sx1, sx0
                    if sy0 > sy1:
                        sy0, sy1 = sy1, sy0

                    # 교집합 영역 계산
                    x_overlap = max(0, min(lx1, sx1) - max(lx0, sx0))
                    y_overlap = max(0, min(ly1, sy1) - max(ly0, sy0))

                    link_width = (lx1 - lx0)
                    link_height = (ly1 - ly0)
                    
                    span_width = (sx1 - sx0)
                    span_height = (sy1 - sy0)

                    if min(link_width, span_width) == 0 or min(link_height, span_height) == 0:
                        continue

                    width_coverage_ratio = x_overlap / min(link_width, span_width)
                    height_coverage_ratio = y_overlap / min(link_height, span_height)

                    if width_coverage_ratio >= 0.8 and height_coverage_ratio >= 0.8:
                        span["link_num"] = link_idx

