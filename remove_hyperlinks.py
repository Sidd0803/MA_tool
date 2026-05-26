from docx import Document
from docx.oxml.ns import qn
from lxml import etree

DOMAIN = "insidearbitrage.com"
FONT_NAME = "Roboto"
_MARKER = "data-removed-hyperlink"


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
            if child.tag == qn("w:r"):
                child.set(_MARKER, "1")
            parent.insert(idx, child)
            idx += 1
        parent.remove(hyperlink)

    return len(hyperlinks)


def _set_color(rPr, hex_color):
    color_el = rPr.find(qn("w:color"))
    if color_el is None:
        color_el = etree.SubElement(rPr, qn("w:color"))
    color_el.set(qn("w:val"), hex_color)


def _set_underline(rPr, val):
    u_el = rPr.find(qn("w:u"))
    if u_el is None:
        u_el = etree.SubElement(rPr, qn("w:u"))
    u_el.set(qn("w:val"), val)


def apply_formatting(doc):
    body = doc.element.body

    for run_el in body.iter(qn("w:r")):
        in_hyperlink = any(
            ancestor.tag == qn("w:hyperlink")
            for ancestor in run_el.iterancestors()
        )
        was_removed_hyperlink = run_el.get(_MARKER) == "1"
        if was_removed_hyperlink:
            del run_el.attrib[_MARKER]

        rPr = run_el.find(qn("w:rPr"))
        if rPr is None:
            rPr = etree.Element(qn("w:rPr"))
            run_el.insert(0, rPr)

        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = etree.SubElement(rPr, qn("w:rFonts"))
        rFonts.set(qn("w:ascii"), FONT_NAME)
        rFonts.set(qn("w:hAnsi"), FONT_NAME)
        rFonts.set(qn("w:cs"), FONT_NAME)

        if was_removed_hyperlink:
            _set_color(rPr, "000000")
            _set_underline(rPr, "none")
            rStyle = rPr.find(qn("w:rStyle"))
            if rStyle is not None:
                rPr.remove(rStyle)
        elif in_hyperlink:
            _set_color(rPr, "0563C1")
            rStyle = rPr.find(qn("w:rStyle"))
            if rStyle is not None:
                rPr.remove(rStyle)


def main():
    doc = Document("MA_written_note.docx")

    count = remove_hyperlinks_by_domain(doc, DOMAIN)
    print(f"Removed {count} insidearbitrage.com hyperlink(s).")

    apply_formatting(doc)
    print(f"Applied '{FONT_NAME}' font.")

    doc.save("MA_written_note_cleaned.docx")
    print("Saved to: MA_written_note_cleaned.docx")


if __name__ == "__main__":
    main()
