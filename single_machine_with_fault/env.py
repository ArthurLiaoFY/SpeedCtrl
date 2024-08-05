import numpy as np
import plotly
import plotly.graph_objects as go
from config import kwargs
from plotly.subplots import make_subplots


def flatten(nested_list: list):
    return [x for xs in nested_list for x in xs]


class Env:
    def __init__(self) -> None:
        self.reset()

    def step(self, action: tuple, time: int, keep_info: bool = False) -> tuple | float:
        # 前方設備抵達數量
        m_arrived = (
            np.sin(time / 30) * 20
            + 100
            + np.random.uniform(low=-7, high=7, size=1).item() // 1
        ) * self.fault_trend[time % len(self.fault_trend)]
        # 操作動作後，當前設備速度
        m_speed_after_action = np.clip(
            a=self.state.get("m_speed") + action[0], a_min=0, a_max=40
        ).item()
        m_queued_after_action = max(0, m_arrived + self.state.get("m_queued"))

        # 當前速度預期應該要有的產量
        m_depart_ability = m_speed_after_action * 5
        # 實際的產量
        m_departed_actual = min(
            m_queued_after_action,
            int(m_depart_ability + np.random.uniform(-2, 2)),
        )
        # 實際與期望的落差
        expectation_gap = m_departed_actual - m_depart_ability
        # 累計堆積產能數量（出貨後）
        m_queued_after_department = max(0, m_queued_after_action - m_departed_actual)
        # 堆積產能遞減 / 遞增加速度
        current_m_queued_diff = self.state.get("m_queued") - m_queued_after_department
        # reward

        part2 = current_m_queued_diff - self.state.get("m_queued_diff")
        part1 = (
            (0.2 if m_queued_after_department > 0 else 0.7) * expectation_gap
            if abs(expectation_gap) > 5
            else 0
        )

        reward = part1 + part2

        # update state

        self.state = {
            "m_speed": m_speed_after_action,
            "m_queued": min(2000, m_queued_after_department // 3 * 3),
            "m_queued_diff": current_m_queued_diff // 3 * 3,
        }
        if keep_info:
            return reward, part1, part2
        else:
            return reward

    def reset(self):
        self.state = {
            "m_speed": 20,
            "m_queued": 0,
            "m_queued_diff": 0,
        }

        self.fault_trend = flatten([[x] * y for y in [20, 30, 40] for x in [1, 0]])
