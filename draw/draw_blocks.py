from draw.draw_alignment import drawAlignmentLabel
from draw.draw_class import drawClassNameLable
from draw.draw_bbox import drawBBox
import pymupdf


def drawBlocks(page_infos, file_path, output_name, yolo_mark = False, block_mark = True, line_mark = False, span_mark = False, align_mark = False, class_mark = False):
    output_path = "outputFile/drawBbox_" + output_name
    page_info_map = {page_info["page_num"]: page_info for page_info in page_infos}

    with pymupdf.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_info = page_info_map[page_num]

            blocks = page_info["blocks"]
            for b in blocks:
                if block_mark:
                    drawBBox(b["bbox"], page)
                if align_mark:
                    drawAlignmentLabel(page, b)
                if class_mark:
                        drawClassNameLable(page, b)

                for l in b["lines"]:
                    if line_mark:
                        drawBBox(l["bbox"], page, 0.1)

                    for s in l["spans"]:
                        if span_mark:
                            drawBBox(s["bbox"], page, 0.2)
                
            yolo_objects = page_info.get("yolo_objects", [])
            for obj in yolo_objects:
                if yolo_mark:
                    drawBBox(obj["bbox"], page)
                    if class_mark:
                        drawClassNameLable(page, obj)


        doc.save(output_path, garbage=3, clean=True, deflate=True)