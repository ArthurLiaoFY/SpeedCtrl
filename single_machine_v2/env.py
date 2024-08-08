import numpy as np
import plotly
import plotly.graph_objects as go
from config import kwargs
from plotly.subplots import make_subplots


def flatten(nested_list: list):
    return [x for xs in nested_list for x in xs]


class Env:
    def __init__(self, **kwargs) -> None:
        self.num_of_eqps = kwargs.get("num_of_eqps")
        self.init_speed = kwargs.get("init_speed")
        self.min_speed = kwargs.get("min_speed")
        self.max_speed = kwargs.get("max_speed")
        self.reset()

    def step(self, action: tuple, eqp_idx: int, m_arrived: int) -> tuple | float:
        # 操作動作後，當前設備速度
        m_speed_after_action = np.clip(
            a=self.m_speed[eqp_idx] + action[0], a_min=0, a_max=60
        ).item()

        m_queued_after_arrive = max(0, m_arrived + self.m_queued[eqp_idx])

        # 當前速度預期應該要有的產量
        m_depart_ability = m_speed_after_action * 3
        # 實際的產量
        m_departed_actual = min(
            m_queued_after_arrive,
            int(m_depart_ability + np.random.uniform(-2, 2)),
        )
        expectation_gap = m_departed_actual - m_depart_ability
        serious_gap = expectation_gap < -10
        # new m queued
        m_queued_after_department = max(0, m_queued_after_arrive - m_departed_actual)
        # new m queued speed
        current_m_queued_diff = self.m_queued[eqp_idx] - m_queued_after_department
        # reward
        no_queued = m_queued_after_department > 0

        part1 = (1 if no_queued else 0) * (
            current_m_queued_diff - self.m_queued_diff[eqp_idx]
        )
        part2 = (
            (0.2 if no_queued else 0.7) * (1 if serious_gap else 0) * expectation_gap
        )

        reward = part1 + part2

        # update state
        self.m_action[eqp_idx] = action[0]
        self.m_speed[eqp_idx] = m_speed_after_action
        self.m_queued[eqp_idx] = m_queued_after_department
        self.m_queued_diff[eqp_idx] = current_m_queued_diff

        self.state = {
            "m_action": self.m_action[eqp_idx],
            "m_speed": self.m_speed[eqp_idx],
            "m_queued": min(400, self.m_queued[eqp_idx] // 3 * 3),
            "m_queued_diff": self.m_queued_diff[eqp_idx] // 3 * 3,
        }
        return reward, m_departed_actual

    def reset(self):
        self.m_action = [0] * self.num_of_eqps
        self.m_speed = [self.init_speed] * self.num_of_eqps
        self.m_queued = [0] * self.num_of_eqps
        self.m_queued_diff = [0] * self.num_of_eqps

        self.state = {
            "m_action": self.m_action[0],
            "m_speed": self.m_speed[0],
            "m_queued": min(400, self.m_queued[0] // 3 * 3),
            "m_queued_diff": self.m_queued_diff[0] // 3 * 3,
        }
