import re
import os
from datetime import datetime
from typing import List, Dict, Optional

import networkx as nx
from pypdf import PdfReader


class CitationNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.paper_years: Dict[str, int] = {}

    def add_paper(self, paper_id: str, year: Optional[int] = None):
        self.graph.add_node(paper_id)
        if year:
            self.paper_years[paper_id] = year

    def add_citation(self, citing_paper: str, cited_paper: str):
        """Add a citation edge (citing → cited)."""
        self.graph.add_edge(citing_paper, cited_paper)

    def get_citations(self, paper):
        return list(self.graph.successors(paper))

    def get_cited_by(self, paper):
        return list(self.graph.predecessors(paper))

    def get_all_papers(self):
        return list(self.graph.nodes)

    def get_citation_count(self, paper):
        return self.graph.in_degree(paper)

    def get_most_cited_papers(self, n=10):
        return sorted(
            self.graph.in_degree(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

    def weighted_pagerank(
        self,
        alpha: float = 0.85,
        recency_boost: float = 1.5,
        self_citation_penalty: float = 0.2,
        current_year: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        PageRank with:
        - Boost for recent papers
        - Penalty for self-citations
        """

        if current_year is None:
            current_year = datetime.now().year

        weighted_graph = nx.DiGraph()

        for u, v in self.graph.edges():
            weight = 1.0

            # Penalize self-citation
            if u == v:
                weight *= self_citation_penalty

            # Boost recent cited papers
            cited_year = self.paper_years.get(v)
            if cited_year:
                age = max(current_year - cited_year, 0)
                recency_weight = 1 + (recency_boost / (1 + age))
                weight *= recency_weight

            weighted_graph.add_edge(u, v, weight=weight)

        return nx.pagerank(
            weighted_graph,
            alpha=alpha,
            weight="weight",
        )

    @staticmethod
    def extract_references_from_pdf(pdf_path: str) -> List[str]:
        """
        Very lightweight reference extractor.
        Assumes references are listed under a 'References' or 'Bibliography' section.
        """
        reader = PdfReader(pdf_path)
        full_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

        match = re.split(
            r"\nreferences\n|\nbibliography\n",
            full_text,
            flags=re.IGNORECASE,
        )

        if len(match) < 2:
            return []

        refs_text = match[1]

        references = [
            line.strip()
            for line in refs_text.split("\n")
            if len(line.strip()) > 20
        ]

        return references

    def build_from_pdfs(
        self,
        pdf_files: List[str],
        paper_metadata: Dict[str, Dict],
    ):
        """
        pdf_files: list of pdf paths
        paper_metadata:
            {
                paper_id: {
                    "year": 2021,
                    "references": [paper_id1, paper_id2]
                }
            }
        """

        for paper_id, meta in paper_metadata.items():
            self.add_paper(paper_id, meta.get("year"))

            for cited in meta.get("references", []):
                self.add_paper(cited)
                self.add_citation(paper_id, cited)

if __name__ == "__main__":
    cn = CitationNetwork()

    cn.build_from_pdfs(
        pdf_files=[],
        paper_metadata={
            "paper_A": {
                "year": 2023,
                "references": ["paper_B", "paper_C"],
            },
            "paper_B": {
                "year": 2019,
                "references": ["paper_C"],
            },
            "paper_C": {
                "year": 2015,
                "references": [],
            },
        },
    )

    scores = cn.weighted_pagerank()

    for paper, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"{paper}: {score:.4f}")
