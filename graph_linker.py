import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class EntityNode:
    entity_id: str          # e.g. "sig:rf_470mhz", "loc:point_a", "callsign:5Y-ABC"
    entity_type: str        # e.g. "signal", "location", "aircraft", "sensor"
    attributes: dict = field(default_factory=dict)
    lat: Optional[float] = None
    lon: Optional[float] = None
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

@dataclass
class RelationEdge:
    source_id: str
    target_id: str
    relation_type: str     # e.g. "co_located", "emits", "observed_near"
    confidence: float = 1.0
    attributes: dict = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


class InMemoryGraphLinker:
    def __init__(self, geo_proximity_km_threshold: float = 2.0, time_proximity_sec: float = 300.0):
        self.nodes: Dict[str, EntityNode] = {}
        # Adjacency map: source_id -> {target_id -> RelationEdge}
        self.adj: Dict[str, Dict[str, RelationEdge]] = {}
        self.geo_thresh_km = geo_proximity_km_threshold
        self.time_thresh_sec = time_proximity_sec

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def upsert_node(self, entity_id: str, entity_type: str, lat: Optional[float] = None, 
                    lon: Optional[float] = None, **attrs) -> EntityNode:
        now = time.time()
        if entity_id in self.nodes:
            node = self.nodes[entity_id]
            node.last_seen = now
            if lat is not None and lon is not None:
                node.lat = lat
                node.lon = lon
            node.attributes.update(attrs)
        else:
            node = EntityNode(
                entity_id=entity_id,
                entity_type=entity_type,
                lat=lat,
                lon=lon,
                attributes=attrs,
                first_seen=now,
                last_seen=now
            )
            self.nodes[entity_id] = node
            self.adj[entity_id] = {}

        # Run automated correlation against existing graph
        self._auto_correlate(node)
        return node

    def add_edge(self, src: str, dst: str, rel_type: str, confidence: float = 1.0, bidirectional: bool = True, **attrs):
        if src not in self.nodes or dst not in self.nodes:
            raise KeyError("Both nodes must exist before linking.")

        edge = RelationEdge(src, dst, rel_type, confidence, attrs, last_updated=time.time())
        self.adj[src][dst] = edge

        if bidirectional:
            back_edge = RelationEdge(dst, src, rel_type, confidence, attrs, last_updated=time.time())
            self.adj[dst][src] = back_edge

    def _auto_correlate(self, new_node: EntityNode):
        """Rules engine: correlates on geo-temporal proximity and shared identifiers."""
        for target_id, target_node in self.nodes.items():
            if target_id == new_node.entity_id:
                continue

            # 1. Geo-Temporal Proximity Rule
            if (new_node.lat is not None and new_node.lon is not None and
                target_node.lat is not None and target_node.lon is not None):
                
                time_delta = abs(new_node.last_seen - target_node.last_seen)
                if time_delta <= self.time_thresh_sec:
                    dist = self._haversine_km(new_node.lat, new_node.lon, target_node.lat, target_node.lon)
                    if dist <= self.geo_thresh_km:
                        # Closer dist/time = higher confidence
                        conf = round(max(0.1, (1.0 - (dist / self.geo_thresh_km)) * (1.0 - (time_delta / self.time_thresh_sec))), 2)
                        self.add_edge(new_node.entity_id, target_id, "spatiotemporal_proximity", 
                                      confidence=conf, distance_km=round(dist, 3))

            # 2. Identifier Overlap Rule (e.g. same network SSID, shared MAC prefix, or group tag)
            common_keys = set(new_node.attributes.keys()) & set(target_node.attributes.keys())
            for key in ("group", "cluster", "operator_id", "bssid"):
                if key in common_keys and new_node.attributes[key] == target_node.attributes[key]:
                    self.add_edge(new_node.entity_id, target_id, f"shared_{key}", confidence=0.9)

    def get_cluster(self, entity_id: str, max_depth: int = 2) -> Dict[str, List[Tuple[str, str, float]]]:
        """Traverse relationships to pull immediate multi-hop context for an entity."""
        if entity_id not in self.nodes:
            return {}

        visited: Set[str] = set()
        queue = [(entity_id, 0)]
        subgraph = {}

        while queue:
            curr, depth = queue.pop(0)
            if curr in visited or depth > max_depth:
                continue
            visited.add(curr)

            subgraph[curr] = [
                (target, edge.relation_type, edge.confidence)
                for target, edge in self.adj[curr].items()
            ]

            if depth < max_depth:
                for target in self.adj[curr]:
                    if target not in visited:
                        queue.append((target, depth + 1))

        return subgraph