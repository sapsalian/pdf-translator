from draw.draw_alignment import drawAlignmentLabel
from draw.draw_class import drawClassNameLable
from draw.draw_bbox import drawBBox
from yolo.yolo_inference.detection import detectObjectsFromFile
import pymupdf

def drawYoloObjects(file_path, output_name):
    paged_yolo = {item["page_num"]: item["objects"] for item in detectObjectsFromFile(file_path)}
    output_path = "outputFile/yolo_result_" + output_name

    with pymupdf.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_objs = paged_yolo[page_num]

                
            for obj in page_objs:
                drawBBox(obj["bbox"], page)
            
                drawClassNameLable(page, obj)


        doc.save(output_path, garbage=3, clean=True, deflate=True)