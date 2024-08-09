import itertools

import numpy as np

kwargs = {
    # -------------------------------
    "action_mapping": {
        idx: combs
        for idx, combs in enumerate(
            itertools.product(
                [0, -10, -5, 5, 10],
            )
        )
    },
    # -------------------------------
    "init_speed": [60, 60],
    "min_speed": [0, 0],
    "max_speed": [180, 180],
    # -------------------------------
    "max_buffer": [1000, 1000],
    # -------------------------------
    "num_of_eqps": 2,
    # -------------------------------
    "learning_rate": 0.1,
    "explore_rate": 0.5,
    "learning_rate_min": 0.03,
    "explore_rate_min": 0.03,
    "learning_rate_decay": 0.999,
    "explore_rate_decay": 0.999,
    "discount_factor": 0.99,
    "fully_explore_step": 500,
}
