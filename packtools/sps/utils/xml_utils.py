import logging
import re

from copy import deepcopy
from lxml import etree
from packtools.sps import exceptions
from packtools.sps.utils import file_utils


logger = logging.getLogger(__name__)


def formatted_text(title_node):
    if title_node is None:
        return

    node = deepcopy(title_node)

    for xref in node.findall(".//xref"):
        parent = xref.getparent()
        parent.remove(xref)

    return node_text(node)


def fix_xml(xml_str):
    return fix_namespace_prefix_w(xml_str)


def fix_namespace_prefix_w(content):
    """
    Convert os textos cujo padrão é `w:st="` em `w-st="`
    """
    pattern = r"\bw:[a-z]{1,}=\""
    found_items = re.findall(pattern, content)
    logger.debug("Found %i namespace prefix w", len(found_items))
    for item in set(found_items):
        new_namespace = item.replace(":", "-")
        logger.debug("%s -> %s" % (item, new_namespace))
        content = content.replace(item, new_namespace)
    return content


def _get_xml_content(xml):
    if isinstance(xml, str):
        try:
            content = read_file(xml)
        except (FileNotFoundError, OSError):
            content = xml
        content = fix_xml(content)
        return content.encode("utf-8")
    return xml


def get_xml_tree(content):
    parser = etree.XMLParser(remove_blank_text=True, no_network=True)
    try:
        content = _get_xml_content(content)
        xml_tree = etree.XML(content, parser)
        # if isinstance(content, str):
        #     # xml_tree = etree.parse(BytesIO(content.encode("utf-8")), parser)
        #     xml_tree = etree.parse(StringIO(content), parser)
        # else:
        #     # content == zipfile.read(sps_xml_file)
    # except ValueError as exc:
    #     xml_tree = etree.XML(content, parser)
    except etree.XMLSyntaxError as exc:
        raise LoadToXMLError(str(exc)) from None
    else:
        return xml_tree


def tostring(node, doctype=None, pretty_print=False):
    return etree.tostring(
        node,
        doctype=doctype,
        xml_declaration=True,
        method="xml",
        encoding="utf-8",
        pretty_print=pretty_print,
    ).decode("utf-8")


def node_text(node, doctype=None, pretty_print=False):
    items = [node.text or ""]
    for child in node.getchildren():
        items.append(
            etree.tostring(child, encoding="utf-8").decode("utf-8")
        )
    return "".join(items)


def get_year_month_day(node):
    """
    Retorna os valores respectivos dos elementos "year", "month", "day".

    Parameters
    ----------
    node : lxml.etree.Element
        Elemento do tipo _date_, que tem os elementos "year", "month", "day".

    Returns
    -------
    tuple of strings
        ("YYYY", "MM", "DD")
    None se node is None

    """
    if node is not None:
        return tuple(
            [(node.findtext(item) or "").zfill(2)
             for item in ["year", "month", "day"]]
        )
