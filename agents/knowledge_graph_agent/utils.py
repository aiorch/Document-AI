CYPHER_GENERATION_TEMPLATE = """
    Task: Generate Cypher statement to query a graph database.

    Instructions:
    - Use only the provided relationship types and properties in the schema.
    - Do not use any other relationship types or properties that are not provided.
    - Convert properties to the correct type if necessary (e.g., `toFloat` for numeric comparisons).
    - Use explicit type conversion in the WHERE clause to ensure proper filtering.

    Schema:
    {schema}
    Note: Do not include any explanations or apologies in your responses.
    Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
    Do not include any text except the generated Cypher statement.
    Examples: Here are a few examples of generated Cypher statements for particular questions:

    Q: Find documents where the raw materials have actual quantities within the allowed range
    Cypher:
    MATCH (j:JsonNode)
    WHERE toFloat(j.actual_quantity) > toFloat(j.allowed_range_min)
    AND toFloat(j.actual_quantity) < toFloat(j.allowed_range_max)
    RETURN j.raw_material, j.actual_quantity, j.allowed_range_min, j.allowed_range_max

    The question is:
    {question}
"""

CYPHER_QA_TEMPLATE = f"""You are an assistant that helps to form nice and human understandable answers.
        The information part contains the provided information that you must use to construct an answer.
        The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
        Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
        Here is an example:

        Information:
        {{context}}

        Question: {{question}}

        If the provided information contains any data, generate a direct and specific answer using it.
        Only if the provided information is empty, say that you don't know the answer.
        
        Helpful Answer:"""


import hashlib
from typing import Any, Union


def flatten_scalar(val: Any) -> str:
    """
    Convert a scalar value into a string representation.
    Handles None, numeric, and string types, ensuring consistent formatting.
    """
    if val is None:
        return "None"
    if isinstance(val, (float, int)):
        return str(val)
    if isinstance(val, str):
        try:
            return str(float(val))
        except ValueError:
            return val  # Fallback to original string
    return str(val)


def compute_signature(
    data: Any,
    parent_key: Union[str, None],
    depth: int = 0,
    doc_name: str = "",
) -> str:
    """
    Compute a stable signature (hash) for a JSON object/array/scalar based on its properties.
    Includes parent_key, depth, and document name for uniqueness.
    """
    if isinstance(data, dict):
        items = [
            f"{k}={flatten_scalar(v)}"
            for k, v in sorted(data.items())
            if not isinstance(v, (dict, list))
        ]
        context = f"parent_key={parent_key}|depth={depth}|dict|doc_name={doc_name}"
    elif isinstance(data, list):
        items = [flatten_scalar(v) for v in data if not isinstance(v, (dict, list))]
        context = f"parent_key={parent_key}|depth={depth}|list|doc_name={doc_name}"
    else:
        items = [flatten_scalar(data)]
        context = f"parent_key={parent_key}|depth={depth}|scalar|doc_name={doc_name}"

    signature_source = "|".join(items) + f"|{context}"
    return hashlib.sha256(signature_source.encode("utf-8")).hexdigest()


def create_relationship(
    tx,
    parent_internal_id: str,
    parent_label: str,
    child_internal_id: str,
    child_label: str,
    rel_type: str,
):
    """
    Create a relationship of type `rel_type` between two nodes identified by their unique `internal_id` properties.
    """
    query = f"""
    MATCH (p:{parent_label} {{internal_id: $parent_internal_id}})
    MATCH (c:{child_label} {{internal_id: $child_internal_id}})
    MERGE (p)-[:{rel_type}]->(c)
    """
    tx.run(
        query,
        parent_internal_id=parent_internal_id,
        child_internal_id=child_internal_id,
    )


def merge_document_node(tx, doc_name: str) -> str:
    """
    Merge a Document node by its doc_name, ensuring it has a unique internal_id.
    Return the internal_id of the node.
    """
    query = """
    MERGE (doc:Document {name: $doc_name})
    ON CREATE SET
        doc.created_at = timestamp(),
        doc.internal_id = $uuid
    SET doc.last_updated = timestamp()
    RETURN doc.internal_id AS doc_uuid
    """
    doc_uuid = hashlib.sha256(
        doc_name.encode("utf-8")
    ).hexdigest()  # Unique UUID for doc_name
    record = tx.run(query, doc_name=doc_name, uuid=doc_uuid).single()
    return record["doc_uuid"]


def attach_all_descendants(session, doc_id: str, root_uuid: str):
    """
    Recursively attach all descendant nodes to the document.
    """
    query = """
    MATCH (root:JsonNode {internal_id: $root_uuid})-[:HAS*]->(child:JsonNode)
    WITH DISTINCT child
    MATCH (doc:Document {internal_id: $doc_id})
    MERGE (doc)-[:HAS]->(child)
    """
    session.execute_write(lambda tx: tx.run(query, root_uuid=root_uuid, doc_id=doc_id))


def create_or_merge_json_node(
    tx,
    data: Any,
    parent_id: Union[int, None],
    parent_key: Union[str, None],
    depth: int,
    doc_name: str,
) -> int:
    """
    Create or MERGE a :JsonNode for the given data. We'll use the "signature" property
    as a stable key to unify duplicates across documents.
    Return the node's internal ID.
    """
    # 1) Compute the signature for this object/array/scalar
    signature = compute_signature(data, parent_key, depth, doc_name)

    # 2) MERGE a :JsonNode by that signature
    node_type = (
        "dict"
        if isinstance(data, dict)
        else "list"
        if isinstance(data, list)
        else "scalar"
    )

    merge_query = """
    MERGE (n:JsonNode {signature: $signature})
    ON CREATE SET
        n.created_at = timestamp(),
        n.node_type  = $node_type,
        n.internal_id = $signature
    SET
        n.parent_key = $pkey,
        n.last_updated = timestamp()
    RETURN n.internal_id AS node_uuid
    """
    record = tx.run(
        merge_query, signature=signature, node_type=node_type, pkey=parent_key
    ).single()
    node_id = record["node_uuid"]

    # 3) Handle nested objects/lists or scalar properties
    if isinstance(data, dict):
        scalar_props = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                child_id = create_or_merge_json_node(
                    tx, v, node_id, k, depth + 1, doc_name
                )
                create_relationship(
                    tx, node_id, "JsonNode", child_id, "JsonNode", "HAS"
                )
            else:
                scalar_props[k] = flatten_scalar(v)

        if scalar_props:
            set_clauses = [f"n.`{prop}`=$props.{prop}" for prop in scalar_props]
            set_cypher = "SET " + ", ".join(set_clauses)
            tx.run(
                f"""
                MATCH (n:JsonNode {{internal_id: $nid}})
                {set_cypher}
                """,
                nid=node_id,
                props=scalar_props,
            )

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            child_id = create_or_merge_json_node(
                tx,
                item,
                node_id,
                f"list_{idx}",
                depth + 1,
                doc_name,
            )
            create_relationship(tx, node_id, "JsonNode", child_id, "JsonNode", "HAS")

    else:
        update_query = """
        MATCH (n:JsonNode {internal_id: $nid})
        SET n.value = $val
        """
        tx.run(update_query, nid=node_id, val=flatten_scalar(data))

    return node_id
