from typing import List, Dict

from rdflib import Graph

convert: Dict[str, List[str]] = {
    "example1_step5.json": ["example1_step5.ttl"],
    "final.nt": ["final.ttl", "final.xml"]
}


for source, targets in convert.items():
    g = Graph()
    g.load(source, format='json-ld' if source.endswith(".json") else "n3" if source.endswith(".nt") else None)
    for target in targets:
        g.serialize(target, format="turtle" if target.endswith(".ttl") else "xml")
