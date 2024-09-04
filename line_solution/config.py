num_of_machine = 3

simulate_setup_config = {
    "run_till": 5000,
    "seed": 1122,
    "trace_env": False,
}

simulate_machine_config = {
    f"machine_{i+1}": {
        "machine_speed": 1 / 3,
        "max_tail_buffer": 8,
        "max_head_buffer": 8,
    }
    for i in range(num_of_machine)
}

simulate_conveyer_config = {
    **{
        f"conveyer_{i}_{i+1}": {
            "conveyer_speed": 1 / 2,
        }
        for i in range(num_of_machine + 1)
    },
}
