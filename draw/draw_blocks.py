from draw.draw_alignment import drawAlignmentLabel
from draw.draw_class import drawClassNameLable
from draw.draw_bbox import drawBBox
from draw.draw_link import drawLinkNumLable
import pymupdf


def drawBlocks(page_infos, file_path, output_name, yolo_mark = False, block_mark = True, line_mark = False, span_mark = False, align_mark = False, class_mark = False, link_mark = False, links_mark = False):
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
                        if link_mark and s.get("link_num", None) is not None:
                            drawBBox(s["bbox"], page, 0.2)
                            drawLinkNumLable(page, s)
                            
                        elif span_mark:
                            drawBBox(s["bbox"], page, 0.2)
                
            yolo_objects = page_info.get("yolo_objects", [])
            for obj in yolo_objects:
                if yolo_mark:
                    drawBBox(obj["bbox"], page)
                    if class_mark:
                        drawClassNameLable(page, obj)
            
            links = page_info.get("links", [])
            if links_mark:
                for link in links:
                    rect = link["from"]
                    from_bbox = [rect.x0, rect.y0, rect.x1, rect.y1]
                    drawBBox(from_bbox, page, 0.1, color=(1,0,0))


        doc.save(output_path, garbage=3, clean=True, deflate=True)