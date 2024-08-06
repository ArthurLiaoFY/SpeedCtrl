import numpy as np
import plotly
import plotly.graph_objects as go

# from config import kwargs
from plotly.subplots import make_subplots


def flatten(nested_list: list):
    return [x for xs in nested_list for x in xs]


class Env:

    def __init__(
        self,
        num_of_eqps: int = 3,
        init_queued_amount: int = 10000,
        init_speed: int = 20,
    ) -> None:
        self.reset(
            num_of_eqps,
            init_queued_amount,
            init_speed,
        )

    def reset(
        self,
        num_of_eqps: int = 3,
        init_queued_amount: int = 10000,
        init_speed: int = 20,
    ):
        self.m_action = [None] + [0 for _ in range(num_of_eqps)] + [None]
        self.m_speed = [None] + [init_speed for _ in range(num_of_eqps)] + [None]
        self.m_queued = [init_queued_amount] + [0 for _ in range(num_of_eqps + 1)]
        self.m_queued_diff = [None] + [0 for _ in range(num_of_eqps)] + [None]
        self.state = {
            # -----------------
            "pm_action": self.m_action[0],
            "pm_speed": self.m_speed[0],
            "pm_queued": self.m_queued[0],
            "pm_queued_diff": self.m_queued_diff[0],
            # -----------------
            "m_action": self.m_action[1],
            "m_speed": self.m_speed[1],
            "m_queued": min(400, self.m_queued[1] // 3 * 3),
            "m_queued_diff": self.m_queued_diff[1] // 3 * 3,
            # -----------------
            "nm_action": self.m_action[2],
            "nm_speed": self.m_speed[2],
            "nm_queued": self.m_queued[2],
            "nm_queued_diff": self.m_queued_diff[2],
            # -----------------
        }
        self.fault_trend = [
            flatten(
                [
                    [
                        np.random.choice(
                            a=[1, 0], size=1, replace=False, p=[0.75, 0.25]
                        ).item()
                    ]
                    * y
                    for y in np.random.choice(
                        a=np.arange(start=20, stop=30, step=1),
                        size=5,
                        replace=True,
                    )
                ]
            )
            for _ in range(num_of_eqps + 2)
        ]

    def step(
        self, action: tuple, time: int, eqp_idx: int, m_arrived: int | None = None
    ) -> tuple | float:
        # 操作動作後，當前設備速度
        m_speed_after_action = (
            np.clip(a=self.m_speed[eqp_idx] + action[0], a_min=0, a_max=60).item()
            * self.fault_trend[eqp_idx][time % len(self.fault_trend[eqp_idx])]
        )
        if eqp_idx == 1:
            m_queued_after_prev_arrive = max(0, self.m_queued[eqp_idx])
        else:
            m_queued_after_prev_arrive = max(0, m_arrived + self.m_queued[eqp_idx])

        # 當前速度預期應該要有的產量
        m_depart_ability = int(m_speed_after_action * 5)
        # 實際的產量
        m_departed_actual = min(
            m_queued_after_prev_arrive,
            m_depart_ability,
        )
        expectation_gap = m_departed_actual - m_depart_ability
        # new m queued
        m_queued_after_department = max(
            0, m_queued_after_prev_arrive - m_departed_actual
        )
        # new m queued speed
        current_m_queued_diff = self.m_queued[eqp_idx] - m_queued_after_department
        # reward

        part1 = (1 if m_queued_after_department > 0 else 0) * (
            current_m_queued_diff - self.m_queued_diff[eqp_idx]
        )
        part2 = (
            (0.2 if m_queued_after_department > 0 else 0.7) * expectation_gap
            if expectation_gap < -5
            else 0
        )
        part3 = 0.05 * (self.m_action[eqp_idx] * action[0])

        reward = part1 + part2 + part3

        # update state
        self.m_action[eqp_idx] = action[0]
        self.m_speed[eqp_idx] = m_speed_after_action
        self.m_queued[eqp_idx] = m_queued_after_department
        self.m_queued_diff[eqp_idx] = current_m_queued_diff

        self.state = {
            # -----------------
            "pm_action": self.m_action[eqp_idx - 1],
            "pm_speed": self.m_speed[eqp_idx - 1],
            "pm_queued": self.m_queued[eqp_idx - 1],
            "pm_queued_diff": self.m_queued_diff[eqp_idx - 1],
            # -----------------
            "m_action": self.m_action[eqp_idx],
            "m_speed": self.m_speed[eqp_idx],
            "m_queued": min(400, self.m_queued[eqp_idx] // 3 * 3),
            "m_queued_diff": self.m_queued_diff[eqp_idx] // 3 * 3,
            # -----------------
            "nm_action": self.m_action[eqp_idx + 1],
            "nm_speed": self.m_speed[eqp_idx + 1],
            "nm_queued": self.m_queued[eqp_idx + 1],
            "nm_queued_diff": self.m_queued_diff[eqp_idx + 1],
            # -----------------
        }

        return reward, m_departed_actual
