from concurrent.futures import ThreadPoolExecutor
from preprocess.paged_info import getPageInfos
from preprocess.preprocess import preProcessPageInfos
from styled_translate.draw_styled_blocks import replaceTranslatedFile
from styled_translate.translate_with_style import translateWithStyle
from draw.draw_blocks import drawBlocks
from draw.draw_yolo_objs import drawYoloObjects


def translatePdf(pdf_name):
    file_path = "inputFile/" + pdf_name

    page_infos = getPageInfos(file_path)
    page_infos = preProcessPageInfos(page_infos)

    for page_info in page_infos:
        translateWithStyle(page_info)

    output_path = "outputFile/output_" + pdf_name
    replaceTranslatedFile(page_infos, file_path, output_path)


def translatePdfInParallel(pdf_name):
    file_path = "inputFile/" + pdf_name

    # drawYoloObjects(file_path, pdf_name)

    page_infos = getPageInfos(file_path)
    page_infos = preProcessPageInfos(page_infos)

    with ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(translateWithStyle, page_infos)

    # drawBlocks(page_infos, file_path, pdf_name, block_mark= True, class_mark= True)

    output_path = "outputFile/output_" + pdf_name
    replaceTranslatedFile(page_infos, file_path, output_path)