from collections import defaultdict

import numpy as np


class Agent:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.action_size = len(kwargs.get("action_mapping_dict"))
        self.start_explore

        self.q_table = defaultdict(lambda: np.zeros(self.action_size))

    def select_action_idx(self, state_tuple: tuple) -> int:
        if self.explore and np.random.uniform(low=0, high=1) <= self.explore_rate:
            action_idx = np.random.choice(self.action_size)

        else:
            action_idx = np.argmax(self.q_table.get(state_tuple))
        return action_idx

    def action_idx_to_action(self, action_idx: int) -> tuple:
        return self.action_mapping_dict.get(action_idx)

    def update_policy(
        self,
        state_tuple: tuple,
        action_idx: int,
        reward: float,
        next_state_tuple: tuple,
    ) -> None:
        td_target = (
            reward
            + self.discount_factor
            * self.q_table[next_state_tuple][np.argmax(self.q_table[next_state_tuple])]
        )

        td_error = td_target - self.q_table[state_tuple][action_idx]
        self.q_table[state_tuple][action_idx] += self.learning_rate * td_error

    def update_lr_er(self, episode: int = 0) -> None:
        if episode > self.fully_explore_step:
            self.explore_rate = max(
                self.explore_rate_min, self.explore_rate * self.explore_rate_decay
            )
        self.learning_rate = max(
            self.learning_rate_min, self.learning_rate * self.learning_rate_decay
        )

    @property
    def shutdown_explore(self) -> None:
        self.explore = False

    @property
    def start_explore(self) -> None:
        self.explore = True

    def save_table(
        self,
        file_path: str = ".",
        prefix: str = "",
        suffix: str = "",
        table_name: str = "q_table",
    ) -> None:
        np.save(
            f"{file_path}/{prefix}{table_name}{suffix}.npy",
            np.array(dict(self.q_table)),
        )

    def load_table(
        self,
        file_path: str = ".",
        prefix: str = "",
        suffix: str = "",
        table_name: str = "q_table",
    ) -> None:

        self.q_table = np.load(
            f"{file_path}/{prefix}{table_name}{suffix}.npy", allow_pickle=True
        ).item()
