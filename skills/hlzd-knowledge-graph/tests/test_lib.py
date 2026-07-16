"""Unit tests for hlzd-knowledge-graph."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lib  # noqa: E402


# ================================================================
# Node / Edge / Graph basic ops
# ================================================================

class TestNodeEdgeGraph:
    def test_add_node(self):
        g = lib.Graph()
        n = lib.Node(id="c1", type="customer", name="Aramco")
        g.add_node(n)
        assert "c1" in g.nodes

    def test_add_invalid_node_type(self):
        g = lib.Graph()
        with pytest.raises(lib.GraphError):
            g.add_node(lib.Node(id="x", type="alien", name="X"))

    def test_add_edge_requires_nodes_exist(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name="C"))
        g.add_node(lib.Node(id="p1", type="product", name="P"))
        g.add_edge(lib.Edge(src="c1", dst="p1", type="interested_in"))
        assert len(g.edges) == 1

    def test_add_edge_with_missing_node_raises(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name="C"))
        with pytest.raises(lib.GraphError):
            g.add_edge(lib.Edge(src="c1", dst="missing", type="interested_in"))

    def test_neighbors_out_in(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name="C"))
        g.add_node(lib.Node(id="p1", type="product", name="P"))
        g.add_node(lib.Node(id="p2", type="product", name="Q"))
        g.add_edge(lib.Edge(src="c1", dst="p1", type="interested_in"))
        g.add_edge(lib.Edge(src="c1", dst="p2", type="interested_in"))
        outs = g.neighbors_out("c1")
        assert len(outs) == 2

    def test_bfs(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name="C"))
        g.add_node(lib.Node(id="p1", type="product", name="P"))
        g.add_node(lib.Node(id="h1", type="hs_code", name="H"))
        g.add_edge(lib.Edge(src="c1", dst="p1", type="interested_in"))
        g.add_edge(lib.Edge(src="p1", dst="h1", type="classified_under"))
        reached = g.bfs("c1", max_depth=3)
        assert reached["c1"] == 0
        assert reached["p1"] == 1
        assert reached["h1"] == 2

    def test_bfs_max_depth_limits(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name="C"))
        g.add_node(lib.Node(id="p1", type="product", name="P"))
        g.add_node(lib.Node(id="h1", type="hs_code", name="H"))
        g.add_edge(lib.Edge(src="c1", dst="p1", type="interested_in"))
        g.add_edge(lib.Edge(src="p1", dst="h1", type="classified_under"))
        reached = g.bfs("c1", max_depth=1)
        assert "h1" not in reached

    def test_to_dict_stats(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name="C"))
        g.add_node(lib.Node(id="p1", type="product", name="P"))
        g.add_node(lib.Node(id="c2", type="customer", name="C2"))
        g.add_edge(lib.Edge(src="c1", dst="p1", type="interested_in"))
        d = g.to_dict()
        assert d["stats"]["node_count"] == 3
        assert d["stats"]["edge_count"] == 1
        assert d["stats"]["by_type"]["customer"] == 2


# ================================================================
# extract_entities
# ================================================================

class TestExtractEntities:
    def test_product_extraction(self):
        text = "We need OCTG and Steel Pipe for our project."
        ents = lib.extract_entities(text)
        assert "OCTG" in ents["products"]
        assert "Steel Pipe" in ents["products"]

    def test_country_extraction(self):
        text = "From Saudi Arabia to United States, our team serves 12 countries."
        ents = lib.extract_entities(text)
        assert "Saudi Arabia" in ents["countries"]
        assert "United States" in ents["countries"]

    def test_cert_extraction(self):
        text = "We need API 5CT and ISO 9001 certified materials."
        ents = lib.extract_entities(text)
        assert "API 5CT" in ents["certifications"]
        assert "ISO 9001" in ents["certifications"]

    def test_no_match(self):
        ents = lib.extract_entities("Random plain text without keywords.")
        assert ents == {"products": [], "countries": [], "certifications": []}

    def test_dedup(self):
        text = "OCTG OCTG OCTG"
        ents = lib.extract_entities(text)
        assert len(ents["products"]) == 1


# ================================================================
# build_graph_from_entities
# ================================================================

class TestBuildGraph:
    def test_basic(self):
        entities = {"products": ["OCTG"], "countries": ["Saudi Arabia"]}
        g = lib.build_graph_from_entities(entities, customer_name="Aramco")
        assert "aramco" in g.nodes
        assert "saudi_arabia" in g.nodes
        assert "octg" in g.nodes
        # customer-hosted_in-country
        assert any(e.type == "hosted_in" for e in g.neighbors_out("aramco"))

    def test_with_certs(self):
        entities = {"products": ["OCTG"], "certifications": ["API 5CT", "ISO 9001"]}
        g = lib.build_graph_from_entities(entities, customer_name="Aramco")
        # product -> cert
        for cert in ["api_5ct", "iso_9001"]:
            assert any(e.type == "certified_by" for e in g.neighbors_out("octg"))

    def test_query_related_customers(self):
        entities = {"products": ["OCTG"], "countries": ["Saudi Arabia"]}
        g = lib.build_graph_from_entities(entities, customer_name="Aramco")
        related = lib.query_related_customers(g, product="OCTG")
        assert any(n.id == "aramco" for n in related)

    def test_query_products_in_country(self):
        entities = {"products": ["OCTG", "Valve"], "countries": ["Saudi Arabia"]}
        g = lib.build_graph_from_entities(entities, customer_name="Aramco")
        products = lib.query_products_in_country(g, country="Saudi Arabia")
        assert len(products) == 2

    def test_customer_name_with_special_chars(self):
        entities = {}
        g = lib.build_graph_from_entities(entities, customer_name="Mr. Ahmed / Acme!")
        assert "mr_ahmed_acme" in g.nodes


# ================================================================
# export_dot
# ================================================================

class TestExportDot:
    def test_basic(self):
        entities = {"products": ["OCTG"], "countries": ["SA"]}
        g = lib.build_graph_from_entities(entities, customer_name="Aramco")
        dot = lib.export_dot(g)
        assert "digraph HLZD" in dot
        assert '"aramco"' in dot
        assert "interested_in" in dot

    def test_escapes_quotes(self):
        g = lib.Graph()
        g.add_node(lib.Node(id="c1", type="customer", name='Acme "Inc"'))
        dot = lib.export_dot(g)
        assert '\\"Inc\\"' in dot


# ================================================================
# run_pipeline (end-to-end)
# ================================================================

class TestRunPipeline:
    def test_full(self):
        text = ("We need OCTG and Steel Pipe from Saudi Arabia with API 5CT and ISO 9001.")
        result = lib.run_pipeline(text, customer_name="Aramco",
                                    query_product="OCTG",
                                    query_country="Saudi Arabia")
        assert result["extracted_entities"]["products"] == ["OCTG", "Steel Pipe"]
        assert "Aramco" in result["extracted_entities"]["countries"] or "Saudi Arabia" in result["extracted_entities"]["countries"]
        assert "graph" in result
        assert "queries" in result

    def test_no_query(self):
        text = "OCTG inquiry"
        result = lib.run_pipeline(text, customer_name="X")
        assert result["queries"]["related_customers_for_product"] == []
        assert result["queries"]["products_in_country"] == []


# ================================================================
# _slugify
# ================================================================

class TestSlugify:
    def test_basic(self):
        assert lib._slugify("Hello World") == "hello_world"

    def test_special_chars(self):
        assert lib._slugify("Mr. Ahmed / Acme!") == "mr_ahmed_acme"

    def test_empty_fallback(self):
        assert lib._slugify("///") == "node"
