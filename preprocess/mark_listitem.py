from util.line_utils import startsWithBullet, startsWithNumberedList

def markListItems(blocks):

    for block in blocks:
        lines = block.get("lines", [])
        if not lines:
            continue
        first_line = lines[0]
        if startsWithBullet(None, first_line) or startsWithNumberedList(None, first_line):
            block["class_name"] = "List-item"
