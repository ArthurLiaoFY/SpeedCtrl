import itertools

import numpy as np

kwargs = {
    # -------------------------------
    "action_mapping": {
        idx: combs
        for idx, combs in enumerate(
            itertools.product(
                [0, -1, 1],
            )
        )
    },
    # -------------------------------
    "init_speed": 35,
    "min_speed": 0,
    "max_speed": 180,
    # -------------------------------
    "num_of_eqps": 1,
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
