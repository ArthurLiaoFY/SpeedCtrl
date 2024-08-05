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
        )
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
        expectation_gap = m_departed_actual - m_depart_ability
        # new m queued
        m_queued_after_department = max(0, m_queued_after_action - m_departed_actual)
        # new m queued speed
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
            "m_queued": min(200, m_queued_after_department // 3 * 3),
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

    def plt_relations(self, step: int = 20):
        m1_speeds = []
        act_1 = []
        reward_l = []
        m1_queued_l = []
        p1, p2 = [], []
        for s in range(step):
            action = kwargs.get("action_mapping")[
                np.random.choice(
                    np.arange(len(kwargs.get("action_mapping"))), size=1
                ).item()
            ]

            act_1.append(action[0])

            reward, part1, part2 = self.step(action=action, time=s, keep_info=True)
            reward_l.append(reward)
            p1.append(part1)
            p2.append(part2)

            m1_speeds.append(self.state.get("m_speed"))
            m1_queued_l.append(self.state.get("m_queued"))

        fig = make_subplots(rows=5)

        fig.add_trace(
            go.Scatter(
                x=np.arange(len(m1_speeds)),
                y=m1_speeds,
                mode="lines+markers",
                name="m1_speeds",
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=np.arange(len(m1_queued_l)),
                y=m1_queued_l,
                mode="lines+markers",
                name="m1_queued_l",
            ),
            row=3,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=np.arange(len(act_1)),
                y=act_1,
                mode="lines+markers",
                name="action",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(x=np.arange(len(p1)), y=p1, mode="lines+markers", name="part1"),
            row=4,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=np.arange(len(p2)), y=p2, mode="lines+markers", name="part2"),
            row=4,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=np.arange(len(reward_l)),
                y=reward_l,
                mode="lines+markers",
                name="reward_l",
            ),
            row=5,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=np.arange(len(reward_l)),
                y=np.zeros_like(reward_l),
                mode="lines",
                name="zero",
            ),
            row=5,
            col=1,
        )

        plotly.offline.plot(figure_or_data=fig, filename="m1.html")
