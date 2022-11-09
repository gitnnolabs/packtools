from unittest import TestCase

from packtools.sps.utils.xml_utils import get_xml_tree
from packtools.sps.validation.article_and_subarticles import validate_language


class ArticleTest(TestCase):        
    def test_article_has_valid_language(self):
        xml_str = """
        <article xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article" xml:lang="en">
            <front>
                <article-meta>
                    <article-id pub-id-type="publisher-id" specific-use="scielo-v3">zTn4sYXBrfSTMNVPF5Dm7jr</article-id>
                    <article-id pub-id-type="publisher-id" specific-use="scielo-v2">S0103-50532014001202258</article-id>
                    <article-id pub-id-type="doi">10.5935/0103-5053.20140192</article-id>
                </article-meta>
            </front>
        </article>
        """
        xml_tree = get_xml_tree(xml_str)

        result, _ = validate_language(xml_tree)
        self.assertTrue(result)


    def test_article_has_invalid_language(self):
        xml_str = """
        <article xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article" xml:lang="e">
            <front>
                <article-meta>
                    <article-id pub-id-type="publisher-id" specific-use="scielo-v3">zTn4sYXBrfSTMNVPF5Dm7jr</article-id>
                    <article-id pub-id-type="publisher-id" specific-use="scielo-v2">S0103-50532014001202258</article-id>
                    <article-id pub-id-type="doi">10.5935/0103-5053.20140192</article-id>
                </article-meta>
            </front>
        </article>
        """
        xml_tree = get_xml_tree(xml_str)

        result, errors = validate_language(xml_tree)

        # Assegura que um problema de idioma foi identificado
        self.assertFalse(result)

        # Assegura que a mensagem relacionada ao problema identicado é a esperada
        self.assertListEqual(
            ['XML research-article has an invalid language: e'],
            [e.message for e in errors]
        )

        # Assegura que a linha em que o problema foi identicado é a esperada
        self.assertListEqual(
            [2],
            [e.line for e in errors]
        )
