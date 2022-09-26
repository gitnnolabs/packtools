from lxml import etree
from packtools.sps.models.article_doi_with_lang import DoiWithLang
from packtools.sps.models.front_journal_meta import ISSN


class InvalidXMLTreeError(Exception):
    ...

def have_similar_issn_codes(xml1, xml2):
    a1_issn = ISSN(xml1)
    a2_issn = ISSN(xml2)
    
    if a1_issn.epub != a2_issn.epub:
        return False

    if a1_issn.ppub != a2_issn.ppub:
        return False

    return True
