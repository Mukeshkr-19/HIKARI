"""Entity and relationship extraction from text."""

import json
import logging
import re
from pathlib import Path
from typing import List, Tuple

from .config import config
from .extraction_filters import filter_entity_triples, filter_preference_subject
from .models import MemoryEdge, MemoryNode, NodeType, EdgeType
from .storage import storage

logger = logging.getLogger(__name__)


class MemoryCompiler:
    PROJECT_PATTERNS = [
        r"(?:working on|project|codebase|repo)[:\s]+([A-Za-z0-9_\-./]+)",
        r"\b([a-z]+-[a-z]+-\d+)\b",  # JIRA-style: s26-fixflow
        r"\b([A-Za-z0-9_]+/[A-Za-z0-9_]+)\b",  # GitHub style: user/repo
    ]

    SKILL_KEYWORDS = {
        "python": NodeType.SKILL.value,
        "javascript": NodeType.SKILL.value,
        "typescript": NodeType.SKILL.value,
        "docker": NodeType.TOOL.value,
        "git": NodeType.TOOL.value,
        "vim": NodeType.TOOL.value,
        "tmux": NodeType.TOOL.value,
        "fastapi": NodeType.TOOL.value,
        "react": NodeType.TOOL.value,
        "sql": NodeType.SKILL.value,
    }

    def __init__(self):
        self.storage = storage

    def compile(
        self, user_message: str, assistant_message: str, metadata: dict = None
    ) -> Tuple[List[MemoryNode], List[MemoryEdge]]:
        metadata = metadata or {}
        user_id = metadata.get("user_id") or config.user_id

        raw_entities: List[Tuple[str, str, str]] = []
        text = f"{user_message or ''} {assistant_message or ''}"
        text_lower = text.lower()

        for project_match in re.finditer(self.PROJECT_PATTERNS[0], text, re.IGNORECASE):
            raw_entities.append(
                (
                    NodeType.PROJECT.value,
                    project_match.group(1).strip(),
                    "Mentioned as project/repo context",
                )
            )

        for jira_match in re.finditer(self.PROJECT_PATTERNS[1], text):
            raw_entities.append(
                (
                    NodeType.PROJECT.value,
                    jira_match.group(1).strip(),
                    "JIRA-style project id",
                )
            )

        for gh_match in re.finditer(self.PROJECT_PATTERNS[2], text):
            raw_entities.append(
                (
                    NodeType.PROJECT.value,
                    gh_match.group(1).strip(),
                    "GitHub-style slug",
                )
            )

        for keyword, node_type in self.SKILL_KEYWORDS.items():
            if keyword in text_lower:
                raw_entities.append(
                    (node_type, keyword.title(), "Mentioned in conversation")
                )

        filtered = filter_entity_triples(raw_entities)
        nodes: List[MemoryNode] = []
        for node_type, name, content in filtered:
            nodes.append(
                MemoryNode(
                    node_type=node_type,
                    name=name,
                    content=content,
                    salience=0.55,
                    user_id=user_id,
                )
            )

        return nodes, []

    def extract_relationships(
        self, text: str, user_id: str
    ) -> List[Tuple[str, str, str]]:
        """
        Returns tuples: (object_name, edge_type, context)
        User is implicit (anchor person node == user_id).
        """
        relationships: List[Tuple[str, str, str]] = []
        text_lower = text.lower()

        preference_patterns = [
            (r"prefer[s]?\s+([A-Za-z0-9\s\-_./]+)", EdgeType.PREFERS.value),
            (r"like[s]?\s+([A-Za-z0-9\s\-_./]+)", EdgeType.PREFERS.value),
            (r"hate[s]?\s+([A-Za-z0-9\s\-_./]+)", EdgeType.OPPOSES.value),
        ]

        for pattern, edge_type in preference_patterns:
            for match in re.finditer(pattern, text_lower):
                subject = filter_preference_subject(match.group(1))
                if not subject:
                    continue
                relationships.append(
                    (subject, edge_type, f"Extracted from: {text[:120]}")
                )

        return relationships

    def compile_and_store(
        self, user_message: str, assistant_message: str, metadata: dict = None
    ) -> dict:
        metadata = metadata or {}
        user_id = metadata.get("user_id") or config.user_id

        nodes, _ = self.compile(user_message, assistant_message, metadata)
        stored_nodes: List[int] = []
        stored_edges: List[int] = []

        for node in nodes:
            stored_nodes.append(self.storage.upsert_node(node))

        combined = f"{user_message or ''} {assistant_message or ''}"
        person = self.storage.get_node_by_name(user_id, NodeType.PERSON.value, user_id)
        if not person:
            logger.warning("No anchor PERSON node for user_id=%s; skipping edges", user_id)
            return {"nodes": stored_nodes, "edges": stored_edges}

        for obj_name, edge_type, ctx in self.extract_relationships(combined, user_id):
            pref = MemoryNode(
                node_type=NodeType.PREFERENCE.value,
                name=obj_name[:80],
                content=f"Inferred preference ({edge_type})",
                salience=0.45,
                user_id=user_id,
            )
            tid = self.storage.upsert_node(pref)
            edge = MemoryEdge(
                source_id=person.id,
                target_id=tid,
                edge_type=edge_type,
                weight=0.65,
                context=ctx,
                user_id=user_id,
            )
            stored_edges.append(self.storage.upsert_edge(edge))

        return {"nodes": stored_nodes, "edges": stored_edges}

    def seed_initial_data(self):
        """
        Optional local seed file (never committed): ~/.hikari/brain/seed_nodes.json
        Schema: { "nodes": [ {"node_type":"PROJECT","name":"...","content":"...", "salience": 0.7 }, ... ] }
        """
        seed_path: Path = config.BRAIN_DIR / "seed_nodes.json"
        if not seed_path.is_file():
            logger.info(
                "No seed_nodes.json at %s — skipping seed (add file locally to seed graph).",
                seed_path,
            )
            return

        try:
            data = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to read seed_nodes.json: %s", e)
            return

        nodes_spec = data.get("nodes") or []
        uid = config.user_id
        for spec in nodes_spec:
            try:
                node = MemoryNode(
                    node_type=str(spec.get("node_type", NodeType.FACT.value)),
                    name=str(spec.get("name", "")).strip(),
                    alias=spec.get("alias"),
                    content=spec.get("content"),
                    salience=float(spec.get("salience", 0.6)),
                    user_id=str(spec.get("user_id", uid)),
                )
                if not node.name:
                    continue
                if self.storage.get_node_by_name(
                    node.name, node.node_type, node.user_id
                ):
                    continue
                self.storage.insert_node(node)
                logger.info("Seeded node from file: %s (%s)", node.name, node.node_type)
            except Exception as e:
                logger.warning("Skip bad seed entry %r: %s", spec, e)


compiler = MemoryCompiler()
