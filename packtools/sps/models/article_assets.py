import os


class AssetReplacementError(Exception):
    ...


class ArticleAssets:
    ASSET_TAGS = (
        'graphic',
        'media',
        'inline-graphic',
        'supplementary-material',
        'inline-supplementary-material',
    )

    ASSET_EXTENDED_TAGS = ASSET_TAGS + (
        'disp-formula',
        'display-formula',
    )

    XPATH_FOR_IDENTIFYING_ASSETS = '|'.join([
        './/' + at + '[@xlink:href]' for at in ASSET_TAGS
    ])

    def __init__(self, xmltree):
        self.xmltree = xmltree
        self._create_parent_map()
        self._discover_assets()

    def _create_parent_map(self):
        self._parent_map = dict(
            (c, p) for p in self.xmltree.iter() for c in p
        )

    @property
    def article_assets(self):
        return self.article_assets_which_have_id + self.article_assets_which_have_no_id

    @property
    def article_assets_which_have_id(self):
        return self._assets_which_have_id

    @property
    def article_assets_which_have_no_id(self):
        return self._assets_which_have_no_id

    def _discover_assets(self):
        self._discover_assets_which_have_id()
        self._discover_assets_which_have_no_id()
    
    def _discover_assets_which_have_id(self):
        self._assets_which_have_id = []
        _visited_nodes = []
        
        for node in self.xmltree.xpath(".//*[@id]"):
            if node.tag == "sub-article":
                continue
        
            i = 0
            for child_node in self._asset_nodes(node):
                if child_node not in _visited_nodes:
                    self._assets_which_have_id.append(Asset(
                        node=child_node, 
                        parent_map=self._parent_map,
                        parent_node_with_id=node, 
                        number=i))
                    _visited_nodes.append(child_node)
                    i += 1

    def _discover_assets_which_have_no_id(self):
        self._assets_which_have_no_id = []
        _visited_nodes = []

        nodes_which_have_id = [i.node for i in self._assets_which_have_id]

        i = 0
        for child_node in self._asset_nodes():
            if child_node not in nodes_which_have_id:
                if child_node not in _visited_nodes:
                    self._assets_which_have_no_id.append(Asset(
                        node=child_node,
                        parent_map=self._parent_map,
                        number=i
                    ))
                    _visited_nodes.append(child_node)
                    i += 1

    def _asset_nodes(self, node=None):
        _assets = []

        source = node or self.xmltree

        for node in source.xpath(
            ArticleAssets.XPATH_FOR_IDENTIFYING_ASSETS,
            namespaces={"xlink": "http://www.w3.org/1999/xlink"}
        ):
            _assets.append(node)

        return _assets

    def replace_names(self, from_to):
        """
        Replace names

        Parameters
        ----------
        from_to : dict

        Returns
        -------
        str list : not found names to replace
        """
        not_found = []
        for asset in self.article_assets:
            try:
                asset.name = from_to[asset.name]
            except KeyError as e:
                not_found.append(asset.name)
        return not_found


class Asset:
    def __init__(self, node, parent_map, parent_node_with_id=None, number=None):
        self.node = node
        self._parent_map = parent_map
        self._parent_node_with_id = parent_node_with_id
        self._number = number


    @property
    def name(self):
        return self.node.attrib["{http://www.w3.org/1999/xlink}href"]

    @name.setter
    def name(self, value):
        self.node.set("{http://www.w3.org/1999/xlink}href", value)

    @property
    def _content_type(self):
        ct = self.node.get('content-type')
        if ct:
            return f'-{ct}'
        return ''

    @property
    def _category_name_code(self):
        """
        -g: figure graphic
        -i: inline graphic
        -e: equation
        -s: supplementary data file
        """
        if "display-formula" in self.node.tag:
            return "e"
        if "supplementary" in self.node.tag:
            return "s"
        if "inline" in self.node.tag:
            return "i"
        return "g"

    @property
    def _suffix(self):
        return f"-{self._category_name_code}{self._id_str}{self._content_type}"

    @property
    def _ext(self):
        _, ext = os.path.splitext(self.name)
        return ext

    @property
    def _lang(self):
        '''
        Tenta obter lang de assets associados a sub-article, caso contrário, retorna string.
        Assets cujo lang é representado por uma string vazia possuem um nome canônico sem o idioma.
        '''
        current_node = self.parent_map[self.node]
        while current_node.tag != 'sub-article':
            try:
                current_node = self.parent_map[current_node]
            except KeyError:
                return ''

        return f"-{current_node.get('{http://www.w3.org/XML/1998/namespace}lang')}" or ""

    def name_canonical(self, package_name):
        return f"{package_name}{self._suffix}{self._lang}{self._ext}"

    @property
    def id(self):
        current_node = self.node

        while current_node is not None and hasattr(current_node, 'attrib') and 'id' not in current_node.attrib:
            current_node = self.parent_map.get(current_node)

        if current_node is None or not hasattr(current_node, 'attrib'):
            return

        current_node_attrib = getattr(current_node, 'attrib')
        if current_node_attrib:
            return current_node_attrib.get('id')

    @property
    def _id_str(self):
        try:
            return ''.join([i for i in self.id if i.isdigit()]).zfill(2)
        except TypeError:
            return ''

    @property
    def type(self):
        """
        <alternatives>
            <graphic xlink:href="original.tif"/>
            <graphic xlink:href="padrao.png" specific-use="scielo-web"/>
            <graphic xlink:href="mini.jpg" specific-use="scielo-web" content-type="scielo-267x140"/>
        </alternatives>

        In the above case, this property returns 'original' for original.tif, 'optimised' for pattern.png and 'thumbnail' for mini.jpg'.
        """
        if 'content-type' in self.node.attrib:
            return 'thumbnail'
        elif 'specific-use' in self.node.attrib:
            return 'optimised'
        else:
            return 'original'


class SupplementaryMaterials:

    def __init__(self, xmltree):
        self.xmltree = xmltree
        self._assets = ArticleAssets(xmltree)

    @property
    def items(self):
        return [item
                for item in self._assets.article_assets
                if item.node.tag in ('supplementary-material',
                                     'inline-supplementary-material')
                ]

    @property
    def data(self):
        return [{"id": item.id, "name": item.name, }
                for item in self.items
                ]
