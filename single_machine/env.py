import matplotlib.pyplot as plt
import numpy as np


def flatten(nested_list: list):
    return [x for xs in nested_list for x in xs]


class Env:
    def __init__(self) -> None:
        self.reset()

    def step(self, action: tuple, time: int) -> None:
        m_arrived = np.random.uniform(low=200, high=400, size=1).item()

        # update state infos
        self.m_speed = np.clip(self.m_speed + action[0], 0, 100000).item()

        m_departed = min(
            m_arrived + self.m_queued,
            int(self.m_speed * 0.005 + np.random.uniform(-2, 2)),
        )
        m_queued_after_action = max(0, m_arrived + self.m_queued - m_departed)
        self.m_queued_diff = (
            self.m_queued - m_queued_after_action
        )  # positive if pressure released, else negative
        # update reward after action
        reward = (m_arrived / 500) * m_departed / (m_arrived + self.m_queued)

        # update queue amount after m departed
        self.m_queued = m_queued_after_action

        self.state = {
            "m_speed": self.m_speed,
            "m_queued": self.m_queued // 10 * 10,
            "m_fault": self.m_fault_trend[time],
        }

        return reward

    def reset(self):
        self.m_fault_trend = flatten(
            [
                [np.random.choice(a=[0, 1], size=1, replace=False, p=[0.5, 0.5]).item()]
                * int(np.random.uniform(low=0, high=20))
                for _ in range(500)
            ]
        )
        self.m_speed = 50000

        self.m_queued = 0

        self.m_queued_diff = 0

        self.state = {
            "m_speed": self.m_speed,
            "m_queued": self.m_queued // 10 * 10,
            "m_fault": self.m_fault_trend[0],
        }
