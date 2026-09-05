"""
Tegaki Manga Interaction Resolver and Canonical Contract (Phase 3L)
===================================================================
Provides:
- normalize_interaction: Converts legacy string ("handshake") or partial dict into canonical interaction dict.
- generate_stable_instance_id: Deterministic instance ID generation.
- resolve_interaction_pairs: Pure logic resolving interaction pairings across character instances with strict validation.
"""

from typing import Dict, Any, List, Optional, Tuple, Set


VALID_INTERACTION_TYPES = {
    "handshake",
    "facing",
    "look_away",
    "hug",
    "fight",
    "holding_hands",
    "conversation",
    "generic"
}

VALID_INTERACTION_ROLES = {
    "initiator",
    "receiver",
    "left_participant",
    "right_participant",
    "mutual",
    "primary",
    "secondary"
}


def generate_stable_instance_id(panel_id: Any, char_id: str, subscene_id: Optional[str] = None, index: int = 1) -> str:
    """Generates a stable, deterministic character instance ID."""
    p_str = f"p{panel_id}" if str(panel_id).isdigit() else str(panel_id)
    c_clean = str(char_id).replace("char_", "")
    if subscene_id:
        s_clean = str(subscene_id).replace("subscene_", "sub_").replace("sub_", "sub_")
        return f"{p_str}_{s_clean}_{c_clean}_{index:02d}"
    return f"{p_str}_{c_clean}_{index:02d}"


def normalize_interaction(
    interaction: Any,
    source_instance_id: Optional[str] = None,
    default_interaction_id: Optional[str] = None,
    context: str = "Interaction"
) -> Optional[Dict[str, Any]]:
    """
    Normalizes legacy string or dict interaction representation into canonical format.
    Canonical format:
    {
        "interaction_id": str,
        "type": str,
        "role": str,
        "target_instance_id": Optional[str]
    }
    """
    if interaction is None or interaction == "":
        return None

    if isinstance(interaction, str):
        itype = interaction.strip().lower()
        if not itype:
            return None
        int_id = default_interaction_id or (f"int_{source_instance_id}" if source_instance_id else "int_default")
        return {
            "interaction_id": int_id,
            "type": itype,
            "role": "mutual",
            "target_instance_id": None
        }

    if not isinstance(interaction, dict):
        raise ValueError(f"[{context}] 'interaction' must be a string or dictionary, got {type(interaction).__name__}")

    raw_type = interaction.get("type") if "type" in interaction else interaction.get("interaction_type", "generic")
    if not isinstance(raw_type, str) or not raw_type.strip():
        raise ValueError(f"[{context}] 'interaction.type' must be a non-empty string")
    itype = raw_type.strip().lower()

    raw_id = interaction.get("interaction_id") or interaction.get("id")
    if raw_id:
        int_id = str(raw_id).strip()
    else:
        int_id = default_interaction_id or (f"int_{source_instance_id}" if source_instance_id else "int_default")

    raw_role = interaction.get("role", "mutual")
    role = str(raw_role).strip().lower() if raw_role else "mutual"

    raw_target = interaction.get("target_instance_id") or interaction.get("target_id")
    target_id = str(raw_target).strip() if raw_target else None

    return {
        "interaction_id": int_id,
        "type": itype,
        "role": role,
        "target_instance_id": target_id
    }


def resolve_interaction_pairs(
    instances: List[Dict[str, Any]],
    panel_id: Optional[Any] = None,
    context: str = "PairResolver"
) -> List[Dict[str, Any]]:
    """
    Pure logic function that resolves paired interactions between character instances.
    Enforces strict rules:
    - Target instance must exist in instances
    - Rejects missing target (when a target is specified)
    - Rejects self target
    - Rejects cross-panel target (if panel_id is specified on instances)
    - Rejects duplicate roles for the same interaction_id (e.g. both 'left_participant')
    """
    if not instances:
        return []

    instance_map: Dict[str, Dict[str, Any]] = {}
    for inst in instances:
        iid = inst.get("instance_id") or inst.get("character_instance_id")
        if not iid:
            continue
        instance_map[iid] = inst

    interactions_by_id: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}

    for iid, inst in instance_map.items():
        raw_inter = inst.get("interaction")
        if not raw_inter:
            continue
        canon = normalize_interaction(raw_inter, source_instance_id=iid, context=f"{context}.{iid}")
        if not canon:
            continue

        target_id = canon.get("target_instance_id")
        if target_id:
            if target_id == iid:
                raise ValueError(f"[{context}] Self-targeting interaction rejected: instance '{iid}' targets itself.")
            if target_id not in instance_map:
                raise ValueError(
                    f"[{context}] Missing interaction target: instance '{iid}' references target '{target_id}' which does not exist in the candidate pool."
                )

            # Check cross-panel
            target_inst = instance_map[target_id]
            s_pid = inst.get("panel_id")
            t_pid = target_inst.get("panel_id")
            if s_pid is not None and t_pid is not None and s_pid != t_pid:
                raise ValueError(
                    f"[{context}] Cross-panel interaction rejected: '{iid}' in panel {s_pid} targets '{target_id}' in panel {t_pid}."
                )

        int_id = canon["interaction_id"]
        interactions_by_id.setdefault(int_id, []).append((iid, canon))

    resolved_pairs: List[Dict[str, Any]] = []

    for int_id, participant_entries in interactions_by_id.items():
        if len(participant_entries) > 2:
            raise ValueError(f"[{context}] Interaction '{int_id}' has more than 2 participants ({len(participant_entries)}).")

        roles_seen: Set[str] = set()
        for iid, inter in participant_entries:
            role = inter.get("role", "mutual")
            if role != "mutual" and role in roles_seen:
                raise ValueError(
                    f"[{context}] Duplicate role '{role}' detected in interaction '{int_id}' between instances."
                )
            roles_seen.add(role)

        if len(participant_entries) == 2:
            p1_id, p1_inter = participant_entries[0]
            p2_id, p2_inter = participant_entries[1]
            resolved_pairs.append({
                "interaction_id": int_id,
                "type": p1_inter["type"],
                "participants": [p1_id, p2_id],
                "participant_roles": {
                    p1_id: p1_inter.get("role", "mutual"),
                    p2_id: p2_inter.get("role", "mutual")
                },
                "panel_id": panel_id or instance_map[p1_id].get("panel_id")
            })
        elif len(participant_entries) == 1:
            p1_id, p1_inter = participant_entries[0]
            target_id = p1_inter.get("target_instance_id")
            if target_id and target_id in instance_map:
                p2_role = "right_participant" if p1_inter.get("role") == "left_participant" else (
                    "receiver" if p1_inter.get("role") == "initiator" else "mutual"
                )
                resolved_pairs.append({
                    "interaction_id": int_id,
                    "type": p1_inter["type"],
                    "participants": [p1_id, target_id],
                    "participant_roles": {
                        p1_id: p1_inter.get("role", "mutual"),
                        target_id: p2_role
                    },
                    "panel_id": panel_id or instance_map[p1_id].get("panel_id")
                })

    return resolved_pairs
