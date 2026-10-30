#!/usr/bin/env python3
"""Write a .pptx with the Python standard library.

The slide canvas gets a title and the given photos. Body text goes in speaker
notes. PowerPoint, Keynote, and a Microsoft account are not used.

  python3 scripts/pptx.py --out OUT.pptx --slides slides.json

slides.json:
  {"slides": [{"title": "...", "notes": "...", "images": ["/abs/photo.jpg"]}]}

Refuses to overwrite --out. Exits 2 when that file already exists.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
NS_VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"

SLIDE_CX = 12192000
SLIDE_CY = 6858000
EMU = 914400

REL_SLIDE = f"{NS_R}/slide"
REL_SLIDE_MASTER = f"{NS_R}/slideMaster"
REL_SLIDE_LAYOUT = f"{NS_R}/slideLayout"
REL_NOTES = f"{NS_R}/notesSlide"
REL_NOTES_MASTER = f"{NS_R}/notesMaster"
REL_THEME = f"{NS_R}/theme"
REL_IMAGE = f"{NS_R}/image"
REL_PRES_PROPS = f"{NS_R}/presProps"
REL_VIEW_PROPS = f"{NS_R}/viewProps"
REL_TABLE_STYLES = f"{NS_R}/tableStyles"


def xml_decl(body: str) -> str:
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + body


def content_types(slide_count: int, media: list[tuple[str, str]]) -> str:
    defaults = {
        "rels": "application/vnd.openxmlformats-package.relationships+xml",
        "xml": "application/xml",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "tiff": "image/tiff",
    }
    for _name, kind in media:
        defaults[kind] = {
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "tiff": "image/tiff",
        }[kind]
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
    ]
    for ext, value in sorted(defaults.items()):
        lines.append(f'  <Default Extension="{ext}" ContentType="{value}"/>')
    overrides = [
        ("/ppt/presentation.xml", "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"),
        ("/ppt/slideMasters/slideMaster1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"),
        ("/ppt/slideLayouts/slideLayout1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"),
        ("/ppt/notesMasters/notesMaster1.xml", "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"),
        ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
        ("/ppt/presProps.xml", "application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"),
        ("/ppt/viewProps.xml", "application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"),
        ("/ppt/tableStyles.xml", "application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
    ]
    for index in range(1, slide_count + 1):
        overrides.append((f"/ppt/slides/slide{index}.xml", "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"))
        overrides.append((f"/ppt/notesSlides/notesSlide{index}.xml", "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"))
    for name, value in overrides:
        lines.append(f'  <Override PartName="{name}" ContentType="{value}"/>')
    lines.append("</Types>")
    return "\n".join(lines)


def relationships(pairs: list[tuple[str, str, str]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        f'<Relationships xmlns="{NS_REL}">',
    ]
    for rel_id, rel_type, target in pairs:
        lines.append(f'  <Relationship Id="{rel_id}" Type="{rel_type}" Target="{target}"/>')
    lines.append("</Relationships>")
    return "\n".join(lines)


def paragraphs(text: str, size_hundredths: int, bold: bool) -> str:
    chunks = text.split("\n") if text else [""]
    bold_attr = ' b="1"' if bold else ""
    parts = []
    for chunk in chunks:
        parts.append(
            "<a:p>"
            "<a:r>"
            f'<a:rPr lang="en-US" sz="{size_hundredths}"{bold_attr} dirty="0">'
            '<a:latin typeface="Arial"/>'
            "</a:rPr>"
            f"<a:t>{escape(chunk)}</a:t>"
            "</a:r>"
            "</a:p>"
        )
    return "".join(parts)


def title_shape(title: str) -> str:
    return f"""<p:sp>
      <p:nvSpPr>
        <p:cNvPr id="2" name="Title"/>
        <p:cNvSpPr txBox="1"/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm>
          <a:off x="457200" y="274320"/>
          <a:ext cx="11277600" cy="822960"/>
        </a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:noFill/>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="b"/>
        <a:lstStyle/>
        {paragraphs(title, 3200, True)}
      </p:txBody>
    </p:sp>"""


def picture_shape(shape_id: int, rel_id: str, x: int, y: int, cx: int, cy: int) -> str:
    return f"""<p:pic>
      <p:nvPicPr>
        <p:cNvPr id="{shape_id}" name="Photo {shape_id}"/>
        <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
        <p:nvPr/>
      </p:nvPicPr>
      <p:blipFill>
        <a:blip r:embed="{rel_id}"/>
        <a:stretch><a:fillRect/></a:stretch>
      </p:blipFill>
      <p:spPr>
        <a:xfrm>
          <a:off x="{x}" y="{y}"/>
          <a:ext cx="{cx}" cy="{cy}"/>
        </a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
      </p:spPr>
    </p:pic>"""


def slide_xml(title: str, pictures: list[str]) -> str:
    body = f"""<p:sld xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      {title_shape(title)}
      {''.join(pictures)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""
    return xml_decl(body)


def notes_xml(notes: str) -> str:
    body = f"""<p:notes xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Notes Placeholder"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="body" idx="1"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          {paragraphs(notes, 1400, False)}
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:notes>"""
    return xml_decl(body)


def presentation_xml(slide_count: int) -> str:
    slides = []
    for index in range(slide_count):
        slides.append(f'<p:sldId id="{256 + index}" r:id="rId{3 + index}"/>')
    body = f"""<p:presentation xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}" saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:notesMasterIdLst>
    <p:notesMasterId r:id="rId2"/>
  </p:notesMasterIdLst>
  <p:sldIdLst>
    {''.join(slides)}
  </p:sldIdLst>
  <p:sldSz cx="{SLIDE_CX}" cy="{SLIDE_CY}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""
    return xml_decl(body)


THEME = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{NS_A}" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F4E79"/></a:dk2>
      <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="5B9BD5"/></a:accent1>
      <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
      <a:accent3><a:srgbClr val="A9D08E"/></a:accent3>
      <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
      <a:accent5><a:srgbClr val="4472C4"/></a:accent5>
      <a:accent6><a:srgbClr val="70AD47"/></a:accent6>
      <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
      <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont>
        <a:latin typeface="Arial"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Arial"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>
"""


def master_xml() -> str:
    body = f"""<p:sldMaster xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
  <p:cSld name="Office Theme">
    <p:bg>
      <p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle><a:lvl1pPr algn="l"><a:defRPr sz="3200" b="1"><a:latin typeface="Arial"/></a:defRPr></a:lvl1pPr></p:titleStyle>
    <p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"><a:latin typeface="Arial"/></a:defRPr></a:lvl1pPr></p:bodyStyle>
    <p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"><a:latin typeface="Arial"/></a:defRPr></a:lvl1pPr></p:otherStyle>
  </p:txStyles>
</p:sldMaster>"""
    return xml_decl(body)


def layout_xml() -> str:
    body = f"""<p:sldLayout xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}" type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""
    return xml_decl(body)


def notes_master_xml() -> str:
    body = f"""<p:notesMaster xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
  <p:cSld name="Notes Master">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Notes Placeholder"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="body" idx="1"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:notesStyle>
    <a:lvl1pPr><a:defRPr sz="1400"><a:latin typeface="Arial"/></a:defRPr></a:lvl1pPr>
  </p:notesStyle>
</p:notesMaster>"""
    return xml_decl(body)


PROPS = xml_decl(
    f"""<p:presentationPr xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}"/>"""
)
VIEW = xml_decl(
    f"""<p:viewPr xmlns:a="{NS_A}" xmlns:r="{NS_R}" xmlns:p="{NS_P}">
  <p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/></p:normalViewPr>
  <p:slideViewPr>
    <p:cSldViewPr>
      <p:cViewPr varScale="1">
        <p:scale><a:sx n="100" d="100"/><a:sy n="100" d="100"/></p:scale>
        <p:origin x="0" y="0"/>
      </p:cViewPr>
      <p:guideLst/>
    </p:cSldViewPr>
  </p:slideViewPr>
</p:viewPr>"""
)
TABLE_STYLES = xml_decl(
    f'<a:tblStyleLst xmlns:a="{NS_A}" def="{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}"/>'
)
CORE = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="{NS_CP}" xmlns:dc="{NS_DC}" xmlns:dcterms="{NS_DCTERMS}" xmlns:xsi="{NS_XSI}">
  <dc:title>Slides from a design file</dc:title>
  <dc:creator>OmniMarkz</dc:creator>
</cp:coreProperties>
"""
APP = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="{NS_EP}" xmlns:vt="{NS_VT}">
  <Application>OmniMarkz</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
</Properties>
"""


def sniff_image(path: Path) -> tuple[str, int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return "png", width, height
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return "gif", width, height
    if data.startswith(b"\xff\xd8\xff"):
        width, height = jpeg_size(data)
        return "jpeg", width, height
    if data.startswith(b"II*\x00") or data.startswith(b"MM\x00*"):
        width, height = tiff_size(data)
        return "tiff", width, height
    raise ValueError(f"unsupported image: {path}")


def jpeg_size(data: bytes) -> tuple[int, int]:
    index = 2
    while index + 8 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[index + 5 : index + 9])
            return width, height
        if marker == 0xD8 or marker == 0xD9:
            index += 2
            continue
        if index + 4 > len(data):
            break
        length = struct.unpack(">H", data[index + 2 : index + 4])[0]
        index += 2 + length
    raise ValueError("jpeg has no size")


def tiff_size(data: bytes) -> tuple[int, int]:
    endian = "<" if data.startswith(b"II") else ">"
    offset = struct.unpack(endian + "I", data[4:8])[0]
    count = struct.unpack(endian + "H", data[offset : offset + 2])[0]
    width = height = 0
    entry = offset + 2
    for _ in range(count):
        tag, _typ, _n, value = struct.unpack(endian + "HHII", data[entry : entry + 12])
        if tag == 256:
            width = value
        elif tag == 257:
            height = value
        entry += 12
    if width and height:
        return width, height
    raise ValueError("tiff has no size")


def fit_boxes(sizes: list[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    count = len(sizes)
    if count == 0:
        return []
    left = 457200
    top = 1280160
    right = SLIDE_CX - 457200
    bottom = SLIDE_CY - 365760
    gap = 182880
    area_w = right - left
    area_h = bottom - top
    cell_w = (area_w - gap * (count - 1)) // count
    boxes = []
    for index, (pixel_w, pixel_h) in enumerate(sizes):
        cell_x = left + index * (cell_w + gap)
        if pixel_w <= 0 or pixel_h <= 0:
            boxes.append((cell_x, top, cell_w, area_h))
            continue
        scale = min(cell_w / pixel_w, area_h / pixel_h)
        cx = max(1, int(pixel_w * scale))
        cy = max(1, int(pixel_h * scale))
        x = cell_x + (cell_w - cx) // 2
        y = top + (area_h - cy) // 2
        boxes.append((x, y, cx, cy))
    return boxes


def load_slides(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    slides = payload.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("slides.json needs a non-empty slides array")
    cleaned = []
    for slide in slides:
        if not isinstance(slide, dict):
            raise ValueError("each slide must be an object")
        title = slide.get("title", "")
        notes = slide.get("notes", "")
        images = slide.get("images", [])
        if not isinstance(title, str) or not isinstance(notes, str) or not isinstance(images, list):
            raise ValueError("title and notes are strings; images is a list of paths")
        cleaned.append({"title": title, "notes": notes, "images": [str(item) for item in images]})
    return cleaned


def build(out: Path, slides: list[dict]) -> None:
    if out.exists():
        raise FileExistsError(out)
    media: list[tuple[str, str]] = []
    slide_parts: list[str] = []
    slide_rels: list[str] = []
    notes_parts: list[str] = []
    notes_rels: list[str] = []
    image_blobs: list[tuple[str, bytes]] = []
    for index, slide in enumerate(slides, start=1):
        sniffed = []
        for image_path in slide["images"]:
            path = Path(image_path)
            if not path.is_file():
                raise ValueError(f"missing image: {path}")
            kind, width, height = sniff_image(path)
            sniffed.append((path, kind, width, height))
        boxes = fit_boxes([(width, height) for _path, _kind, width, height in sniffed])
        pictures = []
        rels = [( "rId1", REL_SLIDE_LAYOUT, "../slideLayouts/slideLayout1.xml" )]
        rels.append(("rId2", REL_NOTES, f"../notesSlides/notesSlide{index}.xml"))
        for image_index, ((path, kind, _width, _height), box) in enumerate(zip(sniffed, boxes), start=1):
            rel_id = f"rId{2 + image_index}"
            media_name = f"image{len(image_blobs) + 1}.{kind if kind != 'jpeg' else 'jpeg'}"
            if kind == "jpeg":
                media_name = f"image{len(image_blobs) + 1}.jpeg"
            image_blobs.append((media_name, path.read_bytes()))
            media.append((media_name, kind))
            rels.append((rel_id, REL_IMAGE, f"../media/{media_name}"))
            pictures.append(picture_shape(2 + image_index, rel_id, *box))
        slide_parts.append(slide_xml(slide["title"], pictures))
        slide_rels.append(relationships(rels))
        notes_parts.append(notes_xml(slide["notes"]))
        notes_rels.append(
            relationships(
                [
                    ("rId1", REL_NOTES_MASTER, "../notesMasters/notesMaster1.xml"),
                    ("rId2", REL_SLIDE, f"../slides/slide{index}.xml"),
                ]
            )
        )
    pres_rels = [
        ("rId1", REL_SLIDE_MASTER, "slideMasters/slideMaster1.xml"),
        ("rId2", REL_NOTES_MASTER, "notesMasters/notesMaster1.xml"),
    ]
    for index in range(1, len(slides) + 1):
        pres_rels.append((f"rId{2 + index}", REL_SLIDE, f"slides/slide{index}.xml"))
    next_id = 3 + len(slides)
    pres_rels.extend(
        [
            (f"rId{next_id}", REL_PRES_PROPS, "presProps.xml"),
            (f"rId{next_id + 1}", REL_VIEW_PROPS, "viewProps.xml"),
            (f"rId{next_id + 2}", REL_TABLE_STYLES, "tableStyles.xml"),
        ]
    )
    files = {
        "[Content_Types].xml": content_types(len(slides), media),
        "_rels/.rels": relationships(
            [
                ("rId1", f"{NS_R}/officeDocument", "ppt/presentation.xml"),
                ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
                ("rId3", f"{NS_R}/extended-properties", "docProps/app.xml"),
            ]
        ),
        "ppt/presentation.xml": presentation_xml(len(slides)),
        "ppt/_rels/presentation.xml.rels": relationships(pres_rels),
        "ppt/slideMasters/slideMaster1.xml": master_xml(),
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": relationships(
            [
                ("rId1", REL_SLIDE_LAYOUT, "../slideLayouts/slideLayout1.xml"),
                ("rId2", REL_THEME, "../theme/theme1.xml"),
            ]
        ),
        "ppt/slideLayouts/slideLayout1.xml": layout_xml(),
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": relationships(
            [("rId1", REL_SLIDE_MASTER, "../slideMasters/slideMaster1.xml")]
        ),
        "ppt/notesMasters/notesMaster1.xml": notes_master_xml(),
        "ppt/notesMasters/_rels/notesMaster1.xml.rels": relationships(
            [("rId1", REL_THEME, "../theme/theme1.xml")]
        ),
        "ppt/theme/theme1.xml": THEME,
        "ppt/presProps.xml": PROPS,
        "ppt/viewProps.xml": VIEW,
        "ppt/tableStyles.xml": TABLE_STYLES,
        "docProps/core.xml": CORE,
        "docProps/app.xml": APP,
    }
    for index, (part, rels, notes, notes_rel) in enumerate(
        zip(slide_parts, slide_rels, notes_parts, notes_rels), start=1
    ):
        files[f"ppt/slides/slide{index}.xml"] = part
        files[f"ppt/slides/_rels/slide{index}.xml.rels"] = rels
        files[f"ppt/notesSlides/notesSlide{index}.xml"] = notes
        files[f"ppt/notesSlides/_rels/notesSlide{index}.xml.rels"] = notes_rel
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(out.suffix + ".partial")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text.encode("utf-8"))
        for name, blob in image_blobs:
            archive.writestr(f"ppt/media/{name}", blob)
    temporary.replace(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a local PowerPoint file.")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--slides", required=True, type=Path)
    args = parser.parse_args()
    try:
        slides = load_slides(args.slides)
        build(args.out, slides)
    except FileExistsError as exc:
        print(f"refusing to overwrite {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
