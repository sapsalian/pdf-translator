import pymupdf

doc = pymupdf.open("a.pdf")
for page in doc:
    text_to_delete = page.search_for("If you want to make money with this ebook, please see page 2!", quads=True)
    
    if(len(text_to_delete) > 0):
      p = text_to_delete[0].ll 
    
    if(text_to_delete):
        for quad in text_to_delete:
            page.add_redact_annot(quad)
        page.apply_redactions(0)

        
'''텍스트 쓰기'''


text = "I'm substitute Text."
# the same result is achievable by
# text = ["Some text", "spread across", "several lines."]

page = doc[0]
rc = page.insert_text(p,  # bottom-left of 1st char
                     text,  # the text (honors '\n')
                     fontname = "helv",  # the default font
                     fontsize = 20,  # the default font size
                     rotate = 0,  # also available: 90, 180, 270
                     )
print("%i lines printed on page %i." % (rc, page.number))

doc.save("new.pdf", garbage=3, clean=True, deflate=True)