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

    def step(self, action: tuple, eqp_idx: int, m_arrived: int) -> tuple | float:
        # 操作動作後，當前設備速度
        m_speed_after_action = np.clip(
            a=self.state.get("m_speed") + action[0], a_min=0, a_max=60
        ).item()

        m_queued_after_arrive = max(0, m_arrived + self.m_queued[eqp_idx])

        # 當前速度預期應該要有的產量
        m_depart_ability = m_speed_after_action * 5
        # 實際的產量
        m_departed_actual = min(
            m_queued_after_arrive,
            int(m_depart_ability + np.random.uniform(-2, 2)),
        )
        expectation_gap = m_departed_actual - m_depart_ability
        # new m queued
        m_queued_after_department = max(0, m_queued_after_arrive - m_departed_actual)
        # new m queued speed
        current_m_queued_diff = self.state.get("m_queued") - m_queued_after_department
        # reward

        part1 = (1 if m_queued_after_department > 0 else 0) * (
            current_m_queued_diff - self.state.get("m_queued_diff")
        )
        part2 = (
            (0.2 if m_queued_after_department > 0 else 0.7)
            * (1 if expectation_gap < -5 else 0)
            * expectation_gap
        )

        reward = part1 + part2

        # update state
        self.m_action[eqp_idx] = action[0]
        self.m_speed[eqp_idx] = m_speed_after_action
        self.m_queued[eqp_idx] = m_queued_after_department
        self.m_queued_diff[eqp_idx] = current_m_queued_diff

        if eqp_idx + 2 == 5:
            self.state = {
                # -------------
                "pm_action": self.m_action[0],
                "pm_speed": self.m_speed[0],
                "pm_queued": self.m_queued[0],
                "pm_queued_diff": self.m_queued_diff[0],
                # -------------
                "m_action": self.m_action[1],
                "m_speed": self.m_speed[1],
                "m_queued": self.m_queued[1],
                "m_queued_diff": self.m_queued_diff[1],
                # -------------
                "nm_action": self.m_action[2],
                "nm_speed": self.m_speed[2],
                "nm_queued": self.m_queued[2],
                "nm_queued_diff": self.m_queued_diff[2],
                # -------------
            }
        else:
            self.state = {
                # -------------
                "pm_action": action[0],
                "pm_speed": m_speed_after_action,
                "pm_queued": min(400, m_queued_after_department // 3 * 3),
                "pm_queued_diff": current_m_queued_diff // 3 * 3,
                # -------------
                "m_action": self.m_action[eqp_idx + 1],
                "m_speed": self.m_speed[eqp_idx + 1],
                "m_queued": self.m_queued[eqp_idx + 1],
                "m_queued_diff": self.m_queued_diff[eqp_idx + 1],
                # -------------
                "nm_action": self.m_action[eqp_idx + 2],
                "nm_speed": self.m_speed[eqp_idx + 2],
                "nm_queued": self.m_queued[eqp_idx + 2],
                "nm_queued_diff": self.m_queued_diff[eqp_idx + 2],
                # -------------
            }
        return reward, m_departed_actual

    def reset(self):
        self.m_action = [None, 0, 0, 0, None]
        self.m_speed = [None, 20, 20, 20, None]
        self.m_queued = [None, 0, 0, 0, None]
        self.m_queued_diff = [None, 0, 0, 0, None]

        self.state = {
            # -------------
            "pm_action": self.m_action[0],
            "pm_speed": self.m_speed[0],
            "pm_queued": self.m_queued[0],
            "pm_queued_diff": self.m_queued_diff[0],
            # -------------
            "m_action": self.m_action[1],
            "m_speed": self.m_speed[1],
            "m_queued": self.m_queued[1],
            "m_queued_diff": self.m_queued_diff[1],
            # -------------
            "nm_action": self.m_action[2],
            "nm_speed": self.m_speed[2],
            "nm_queued": self.m_queued[2],
            "nm_queued_diff": self.m_queued_diff[2],
            # -------------
        }
