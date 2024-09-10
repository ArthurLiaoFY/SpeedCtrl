# %%
import itertools
import json
from collections import defaultdict

# unity_config = json.loads(open("./unity_config.json").read())
# unity_config = json.loads(open("./line_solution/unity_config.json").read())
unity_config = json.loads(open("./unity_sub_config.json").read())
# unity_config = json.loads(open("./line_solution/unity_sub_config.json").read())

id_to_machine_map = {
    item.get("id"): item for item in unity_config.get("Layoutdata").get("Device")
}
source_to_target_map = defaultdict(list)
target_to_source_map = defaultdict(list)

for item in unity_config.get("Layoutdata").get("Contextdragconnection"):
    source_to_target_map[item.get("source")].append(item.get("target"))
    target_to_source_map[item.get("target")].append(item.get("source"))

sn_feeder_id = list(
    set(source_to_target_map.keys())
    - set([i for l in source_to_target_map.values() for i in l])
)[0]
sn_receiver_id = list(
    set([i for l in source_to_target_map.values() for i in l])
    - set(source_to_target_map.keys())
)[0]
simulate_setup_config = {
    "simulate_runs": 5000,
    "run_till": 8 * 60 * 60,
    "seed": 1122,
    "trace_env": False,
    "env_scan_interval": 10,
    "sn_feeder": {
        "name": "半成品發射器",
        "id": sn_feeder_id,
        "to_ids": source_to_target_map.get(sn_feeder_id),
    },
    "sn_receiver": {
        "name": "成品接收器",
        "id": sn_receiver_id,
    },
}

simulate_machine_config = {
    f"{id}": {
        "prev_machine_id": target_to_source_map.get(id)[0],
        "next_machine_id": source_to_target_map.get(id)[0],
        "machine_name": machine_infos.get("name"),
        "machine_cycletime": machine_infos.get("cycletime"),
        "max_head_buffer": machine_infos.get("max_head_buffer", 8),
        "max_tail_buffer": machine_infos.get("max_tail_buffer", 8),
    }
    for id, machine_infos in id_to_machine_map.items()
    if id
    not in (
        simulate_setup_config.get("sn_feeder").get("id"),
        simulate_setup_config.get("sn_receiver").get("id"),
    )
    and machine_infos.get("class") != "StraightConveyor"
}

simulate_conveyer_config = {
    **{
        f"{target}#{source}": {
            "conveyer_name": f"傳輸帶({simulate_machine_config.get(target, {}).get('machine_name')} --> {simulate_machine_config.get(source, {}).get('machine_name')})",
            "conveyer_cycletime": 0.5,
            "conveyer_from": target,
            "conveyer_to": source,
        }
        for target, source_list in source_to_target_map.items()
        for source in source_list
        if target != simulate_setup_config.get("sn_feeder").get("id")
    },
}

agent_config = {
    "action_mapping_dict": {
        idx: combs
        for idx, combs in enumerate(
            itertools.product(
                [0, -6, -3, -1, 1, 3, 6, 10, 20, 40],
            )
        )
    },
    "learning_rate": 0.1,
    "explore_rate": 0.5,
    "learning_rate_min": 0.03,
    "explore_rate_min": 0.03,
    "learning_rate_decay": 0.999,
    "explore_rate_decay": 0.999,
    "discount_factor": 0.99,
    "fully_explore_step": 0,
}
