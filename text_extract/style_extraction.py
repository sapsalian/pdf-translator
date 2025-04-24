import pymupdf


def flags_decomposer(flags):
    """Make font flags human readable."""
    l = []
    if flags & 2 ** 0:
        l.append("superscript")
    if flags & 2 ** 1:
        l.append("italic")
    if flags & 2 ** 2:
        l.append("serifed")
    else:
        l.append("sans")
    if flags & 2 ** 3:
        l.append("monospaced")
    else:
        l.append("proportional")
    if flags & 2 ** 4:
        l.append("bold")
    return ", ".join(l)


doc = pymupdf.open("b.pdf")
page = doc[6]

# read page text as a dictionary, suppressing extra spaces in CJK fonts
blocks = page.get_text("dict", flags=11)["blocks"] 
for b in blocks:  # iterate through the text blocks # b = 하나의 블락 잡아주는 듯
    for l in b["lines"]:  # iterate through the text lines # line = 한 줄에 있는 텍스트 모두
        for s in l["spans"]:  # iterate through the text spans # s = 한 줄 내에서도 글꼴이 달라지거나 하면 span으로 잡히는 듯
            print("")
            font_properties = "Font: '%s' (%s), size %g, color #%06x" % (
                s["font"],  # font name
                flags_decomposer(s["flags"]),  # readable font flags
                s["size"],  # font size
                s["color"],  # font color
            )
            print("Text: '%s'" % s["text"])  # simple print of text
            print(font_properties)