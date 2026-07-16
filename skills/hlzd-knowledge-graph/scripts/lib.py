"""hlzd-knowledge-graph shared library.

B2B entity extraction + lightweight in-memory graph.

Use cases:
  - 从 inquiry-qualify 输出抽实体 (customer / product / cert / country)
  - 从 buyer-finder 输出合并 (customer <-> country <-> product links)
  - 从 quotation-gen 输出抽 (product -certified_by-> cert links)
  - query: "找所有对 OCTG 有兴趣的沙特买家 + 他们的关系"
  - output: JSON adjacency / DOT for graphviz render

设计: 纯 dict-based graph, stdlib only. v0.2 接真 graph DB.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-knowledge-graph") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# Errors
# ================================================================

class GraphError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-knowledge-graph",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


# ================================================================
# Node + Edge types
# ================================================================

NODE_TYPES = {"customer", "product", "certification", "country", "hs_code", "supplier"}
EDGE_TYPES = {
    "interested_in",     # customer -interested_in-> product
    "sourced_from",      # customer -sourced_from-> country
    "hosted_in",         # customer -hosted_in-> country
    "certified_by",      # product -certified_by-> certification
    "classified_under",  # product -classified_under-> hs_code
    "ordered_from",      # customer -ordered_from-> supplier
    "complies_with",     # product -complies_with-> standard
}


@dataclass
class Node:
    id: str                  # unique id
    type: str                # one of NODE_TYPES
    name: str                # display name
    attrs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "type": self.type, "name": self.name, **self.attrs}


@dataclass
class Edge:
    src: str                 # node id
    dst: str                 # node id
    type: str                # one of EDGE_TYPES
    attrs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"src": self.src, "dst": self.dst, "type": self.type, **self.attrs}


class Graph:
    """Lightweight graph: nodes (dict[id -> Node]) + edges (list[Edge])."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adj_out: Dict[str, List[Edge]] = defaultdict(list)
        self._adj_in: Dict[str, List[Edge]] = defaultdict(list)

    def add_node(self, node: Node) -> None:
        if node.type not in NODE_TYPES:
            raise GraphError(f"unknown node type: {node.type!r}")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.type not in EDGE_TYPES:
            raise GraphError(f"unknown edge type: {edge.type!r}")
        if edge.src not in self.nodes:
            raise GraphError(f"src node not found: {edge.src}")
        if edge.dst not in self.nodes:
            raise GraphError(f"dst node not found: {edge.dst}")
        self.edges.append(edge)
        self._adj_out[edge.src].append(edge)
        self._adj_in[edge.dst].append(edge)

    def neighbors_out(self, node_id: str) -> List[Edge]:
        return self._adj_out.get(node_id, [])

    def neighbors_in(self, node_id: str) -> List[Edge]:
        return self._adj_in.get(node_id, [])

    def bfs(self, start_id: str, *, max_depth: int = 3) -> Dict[str, int]:
        """BFS from start. Returns {node_id: depth} for reachable nodes."""
        if start_id not in self.nodes:
            raise GraphError(f"start node not found: {start_id}")
        visited: Dict[str, int] = {start_id: 0}
        queue: deque = deque([(start_id, 0)])
        while queue:
            cur, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in self.neighbors_out(cur):
                if edge.dst not in visited:
                    visited[edge.dst] = depth + 1
                    queue.append((edge.dst, depth + 1))
        return visited

    def find(self, node_type: str, name: Optional[str] = None) -> List[Node]:
        out: List[Node] = []
        for n in self.nodes.values():
            if n.type != node_type:
                continue
            if name and n.name.lower() != name.lower():
                continue
            out.append(n)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "by_type": self._node_type_counts(),
            },
        }

    def _node_type_counts(self) -> Dict[str, int]:
        out: Dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            out[n.type] += 1
        return dict(out)


# ================================================================
# Entity extraction (deterministic regex)
# ================================================================

# 常见认证 keyword (复用 hlzd-inquiry-qualify 的 cert list)
CERT_KEYWORDS = [
    "API 5CT", "API 5L", "ISO 11960", "ISO 9001", "ISO 14001",
    "NACE MR0175", "EN 1090", "CE", "IEC 61215", "IEC 61730",
    "UL 1703", "RoHS", "REACH", "ASTM A53", "ASTM A106",
    "ASME B16.9", "ASME B31.3",
]
CERT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in CERT_KEYWORDS) + r")\b"
)

# 常见工业品 product keyword (复用 hlzd-solution-match 的 catalog)
PRODUCT_KEYWORDS = [
    "OCTG", "Casing", "Steel Pipe", "Steel Structure", "Container House",
    "Solar Panel", "Cement", "Valve", "Pump", "Bearing",
    "Fastener", "Cable", "Transformer",
]
PRODUCT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in PRODUCT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Country 简表 (与 hlzd-b2b-research / hlzd-trade-compliance 共享)
COUNTRY_KEYWORDS = [
    "Saudi Arabia", "UAE", "Iran", "North Korea", "Syria", "Cuba",
    "Russia", "Belarus", "China", "Vietnam", "India", "Brazil",
    "Mexico", "Argentina", "Chile", "Peru", "Egypt", "Nigeria",
    "Kenya", "South Africa", "United States", "Canada", "Germany",
    "France", "United Kingdom", "Italy", "Spain", "Netherlands",
    "Poland", "Turkey", "Indonesia", "Malaysia", "Thailand",
    "Singapore", "Philippines", "Vietnam",
]
COUNTRY_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in COUNTRY_KEYWORDS) + r")\b"
)


def extract_entities(text: str) -> Dict[str, List[str]]:
    """从自由文本抽 (product, country, cert) entities。

    Returns dict {"products": [...], "countries": [...], "certifications": [...]}
    去重保持顺序。
    """
    out: Dict[str, List[str]] = {"products": [], "countries": [], "certifications": []}

    for match in PRODUCT_PATTERN.finditer(text):
        token = match.group(1)
        if token.lower() not in {p.lower() for p in out["products"]}:
            out["products"].append(token)

    for match in COUNTRY_PATTERN.finditer(text):
        token = match.group(1)
        if token.lower() not in {c.lower() for c in out["countries"]}:
            out["countries"].append(token)

    for match in CERT_PATTERN.finditer(text):
        token = match.group(1)
        if token not in out["certifications"]:
            out["certifications"].append(token)

    return out


# ================================================================
# Build graph from entity dict + context
# ================================================================

def build_graph_from_entities(
    entities: Dict[str, List[str]],
    *,
    customer_name: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> Graph:
    """把 extract_entities 的输出 + 可选 customer 转成 Graph。"""
    g = Graph()

    # customer node
    cid = customer_id or _slugify(customer_name or "unknown-customer")
    g.add_node(Node(
        id=cid,
        type="customer",
        name=customer_name or "Unknown Customer",
    ))

    # country nodes
    for i, c in enumerate(entities.get("countries", [])):
        nid = _slugify(c)
        g.add_node(Node(id=nid, type="country", name=c))
        g.add_edge(Edge(src=cid, dst=nid, type="hosted_in"))
        g.add_edge(Edge(src=cid, dst=nid, type="sourced_from"))

    # product nodes
    for i, p in enumerate(entities.get("products", [])):
        nid = _slugify(p)
        g.add_node(Node(id=nid, type="product", name=p))
        g.add_edge(Edge(src=cid, dst=nid, type="interested_in"))

    # cert nodes
    for c in entities.get("certifications", []):
        nid = _slugify(c)
        g.add_node(Node(id=nid, type="certification", name=c))
        # product -> cert: only if product present
        products = entities.get("products", [])
        if products:
            for p in products:
                g.add_edge(Edge(src=_slugify(p), dst=nid, type="certified_by"))
        else:
            g.add_edge(Edge(src=cid, dst=nid, type="complies_with"))

    return g


def _slugify(s: str) -> str:
    """简单 slug: lowercase + non-alphanum -> '_'"""
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "node"


# ================================================================
# Query helpers
# ================================================================

def query_related_customers(graph: Graph, *, product: str) -> List[Node]:
    """找所有对 product 感兴趣 (interested_in) 的 customer。"""
    prod_id = _slugify(product)
    out: List[Node] = []
    for edge in graph.neighbors_in(prod_id):
        if edge.type == "interested_in" and edge.src in graph.nodes:
            n = graph.nodes[edge.src]
            if n.type == "customer":
                out.append(n)
    return out


def query_products_in_country(graph: Graph, *, country: str) -> List[Node]:
    """找所有 customer 在 country 中 host 过的 product。"""
    cid = _slugify(country)
    # hosted_in: customer -> country. 我们要 incoming 边（dst = country）
    customer_ids = {e.src for e in graph.neighbors_in(cid) if e.type == "hosted_in"}
    out: List[Node] = []
    for cust_id in customer_ids:
        for e in graph.neighbors_out(cust_id):
            if e.type == "interested_in" and e.dst in graph.nodes:
                p = graph.nodes[e.dst]
                if p.type == "product":
                    out.append(p)
    # 去重保序
    seen: Set[str] = set()
    uniq: List[Node] = []
    for p in out:
        if p.id not in seen:
            uniq.append(p)
            seen.add(p.id)
    return uniq


def export_dot(graph: Graph) -> str:
    """生成 Graphviz DOT 字符串 (for `dot -Tpng > out.png`)。"""
    lines = ["digraph HLZD {"]
    lines.append('  rankdir=LR;')
    lines.append('  node [shape=box, style=rounded];')
    # type-specific node shapes
    type_shape = {
        "customer": "box", "product": "ellipse", "country": "diamond",
        "certification": "hexagon", "hs_code": "note", "supplier": "box3d",
    }
    for n in graph.nodes.values():
        shape = type_shape.get(n.type, "box")
        lines.append(f'  "{n.id}" [label="{_dot_escape(n.name)}", shape={shape}];')
    for e in graph.edges:
        lines.append(f'  "{e.src}" -> "{e.dst}" [label="{_dot_escape(e.type)}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def _dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


# ================================================================
# Pipeline
# ================================================================

def run_pipeline(text: str, *, customer_name: Optional[str] = None,
                  customer_id: Optional[str] = None,
                  query_product: Optional[str] = None,
                  query_country: Optional[str] = None) -> Dict[str, Any]:
    """End-to-end: extract → build graph → query → return dict."""
    entities = extract_entities(text)
    graph = build_graph_from_entities(entities, customer_name=customer_name,
                                       customer_id=customer_id)

    related_customers: List[Dict[str, Any]] = []
    if query_product:
        related_customers = [
            n.to_dict() for n in query_related_customers(graph, product=query_product)
        ]

    products_in_country: List[Dict[str, Any]] = []
    if query_country:
        products_in_country = [
            n.to_dict() for n in query_products_in_country(graph, country=query_country)
        ]

    return {
        "$schema": "hlzd/knowledge-graph/v1",
        "extracted_entities": entities,
        "graph": graph.to_dict(),
        "queries": {
            "related_customers_for_product": related_customers,
            "products_in_country": products_in_country,
        },
    }
