import itertools

import numpy as np

# eqp_kwargs = {
#     # -------------------------------
#     "num_of_eqps": 5,
#     # -------------------------------
#     "action_mapping_dict": {
#         idx: action
#         for idx, action in enumerate([0, -60, -30, -10, -5, -3, 3, 5, 10, 30, 60])
#     },
#     # -------------------------------
#     "init_status_dict": {
#         0: 1,
#         # 1: 1,
#         # 2: 1,
#         # 3: 1,
#         # 4: 1,
#     },
#     # -------------------------------
#     "init_speed_dict": {
#         0: 0,
#         # 1: 0,
#         # 2: 0,
#         # 3: 0,
#         # 4: 0,
#     },
#     "min_speed_dict": {
#         0: 0,
#         # 1: 0,
#         # 2: 0,
#         # 3: 0,
#         # 4: 0,
#     },
#     "max_speed_dict": {
#         0: 180,
#         # 1: 180,
#         # 2: 180,
#         # 3: 180,
#         # 4: 180,
#     },
#     # -------------------------------
#     "max_head_buffer_dict": {
#         0: 400,
#         # 1: 400,
#         # 2: 400,
#         # 3: 400,
#         # 4: 400,
#     },
#     "max_tail_buffer_dict": {
#         0: 400,
#         # 1: 400,
#         # 2: 400,
#         # 3: 400,
#         # 4: 400,
#     },
#     # -------------------------------
#     "balancing_coef_dict": {
#         0: 0.7,
#         # 1: 0.7,
#         # 2: 0.7,
#         # 3: 0.7,
#         # 4: 0.7,
#     },
#     # -------------------------------
#     "feeding_speed": 60,
#     "shipping_speed": 60,
# }


line_kwargs = {
    # -------------------------------
    "action_mapping_dict": {
        idx: combs
        for idx, combs in enumerate(
            itertools.product(
                [0, -0.3, -0.1, 0.1, 0.3],
                [0, -0.3, -0.1, 0.1, 0.3],
                [0, -0.3, -0.1, 0.1, 0.3],
                [0, -0.3, -0.1, 0.1, 0.3],
                [0, -0.3, -0.1, 0.1, 0.3],
            )
        )
    },
    # -------------------------------
    "num_of_eqps": 5,
    # -------------------------------
    "sim_production_quantity": 20000,
    # -------------------------------
    "feeding_speed": 60,
    "shipping_speed": 60,
}
line_kwargs["eqp_balancing_coef"] = {
    eqp_idx: 0.7 for eqp_idx in range(line_kwargs.get("num_of_eqps"))
}

eqp_kwargs = {
    # -------------------------------
    "action_mapping_dict": {
        idx: action
        for idx, action in enumerate([0, -60, -30, -10, -5, -3, 3, 5, 10, 30, 60])
    },
    # -------------------------------
    "init_status": 1,
    # -------------------------------
    "init_speed": 0,
    "min_speed": 0,
    "max_speed": 180,
    # -------------------------------
    "max_head_buffer": 400,
    "max_tail_buffer": 400,
    # -------------------------------
    "balancing_coef": None,
}

q_learning_kwargs = {
    # -------------------------------
    "learning_rate": 0.1,
    "explore_rate": 0.5,
    "learning_rate_min": 0.03,
    "explore_rate_min": 0.03,
    "learning_rate_decay": 0.999,
    "explore_rate_decay": 0.999,
    "discount_factor": 0.99,
    "fully_explore_step": 0,
}
