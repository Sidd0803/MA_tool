from docx import Document
from docx.oxml.ns import qn
from lxml import etree

DOMAIN = "insidearbitrage.com"
FONT_NAME = "Roboto"
BLACK = "000000"
BLUE = "0000FF"


def remove_hyperlinks_by_domain(doc, domain):
    part = doc.part
    target_rids = {
        rId
        for rId, rel in part.rels.items()
        if rel.reltype == (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
        )
        and domain in rel.target_ref
    }

    if not target_rids:
        print(f"No hyperlinks found containing '{domain}'.")
        return 0

    body = doc.element.body
    hyperlinks = [
        el for el in body.iter(qn("w:hyperlink"))
        if el.get(qn("r:id")) in target_rids
    ]

    for hyperlink in hyperlinks:
        parent = hyperlink.getparent()
        idx = list(parent).index(hyperlink)
        for child in list(hyperlink):
            parent.insert(idx, child)
            idx += 1
        parent.remove(hyperlink)

    return len(hyperlinks)


def apply_formatting(doc):
    body = doc.element.body

    for run_el in body.iter(qn("w:r")):
        in_hyperlink = any(
            ancestor.tag == qn("w:hyperlink")
            for ancestor in run_el.iterancestors()
        )

        # Get or create w:rPr (must be first child of w:r)
        rPr = run_el.find(qn("w:rPr"))
        if rPr is None:
            rPr = etree.Element(qn("w:rPr"))
            run_el.insert(0, rPr)

        # Font: set or update w:rFonts
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = etree.SubElement(rPr, qn("w:rFonts"))
        rFonts.set(qn("w:ascii"), FONT_NAME)
        rFonts.set(qn("w:hAnsi"), FONT_NAME)
        rFonts.set(qn("w:cs"), FONT_NAME)

        # Color: blue for hyperlinks, black for everything else
        color_el = rPr.find(qn("w:color"))
        if color_el is None:
            color_el = etree.SubElement(rPr, qn("w:color"))
        color_el.set(qn("w:val"), BLUE if in_hyperlink else BLACK)

        # Remove any theme color override so explicit color takes effect
        color_el.attrib.pop(qn("w:themeColor"), None)
        color_el.attrib.pop(qn("w:themeShade"), None)
        color_el.attrib.pop(qn("w:themeTint"), None)


def main():
    doc = Document("MA_written_note.docx")

    count = remove_hyperlinks_by_domain(doc, DOMAIN)
    print(f"Removed {count} insidearbitrage.com hyperlink(s).")

    apply_formatting(doc)
    print(f"Applied '{FONT_NAME}' font, black for body text, blue for hyperlinks.")

    doc.save("MA_written_note_cleaned.docx")
    print("Saved to: MA_written_note_cleaned.docx")


if __name__ == "__main__":
    main()
