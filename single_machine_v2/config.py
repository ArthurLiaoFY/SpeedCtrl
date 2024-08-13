import itertools

import numpy as np

kwargs = {
    # -------------------------------
    "action_mapping": {
        0: 0,
        1: -10,
        2: -5,
        3: 5,
        4: 10,
    },
    # -------------------------------
    "init_speed": [60, 60, 60],
    "min_speed": [0, 0, 0],
    "max_speed": [180, 180, 180],
    # -------------------------------
    "max_head_buffer": [np.inf, 500, 500],
    "max_tail_buffer": [500, 500, np.inf],
    # -------------------------------
    "num_of_eqps": 3,
    # -------------------------------
    "learning_rate": 0.1,
    "explore_rate": 0.5,
    "learning_rate_min": 0.03,
    "explore_rate_min": 0.03,
    "learning_rate_decay": 0.999,
    "explore_rate_decay": 0.999,
    "discount_factor": 0.99,
    "fully_explore_step": 1000,
}
