import matplotlib.pyplot as plt
import numpy as np
from config import kwargs


def flatten(nested_list: list):
    return [x for xs in nested_list for x in xs]


class Env:
    def __init__(self) -> None:
        self.reset()

    def step(self, action: tuple, time: int) -> None:
        m_arrived = 100 + np.random.uniform(low=-2, high=2, size=1).item() // 1
        m_speed_after_action = np.clip(
            a=self.state.get("m_speed") + action[0], a_min=0, a_max=40
        ).item()
        m_queued_after_action = max(0, m_arrived + self.state.get("m_queued"))

        m_depart_ability = m_speed_after_action * 5
        m_departed_actual = min(
            m_queued_after_action,
            int(m_depart_ability + np.random.uniform(-2, 2)),
        )
        # reward

        reward = (m_departed_actual - m_arrived) + (
            m_departed_actual - m_depart_ability
        )

        # update state

        self.state = {
            "m_speed": m_speed_after_action,
            "m_queued": m_queued_after_action - m_departed_actual,
        }

        return reward

    def reset(self):
        self.state = {
            "m_speed": 20,
            "m_queued": 0,
        }


    def plt_relations(self, step: int = 20):
        m1_speeds = []
        act_1 = []
        reward_l = []
        m1_queued_l = []
        for s in range(step):
            action = kwargs.get("action_mapping")[
                np.random.choice(
                    np.arange(len(kwargs.get("action_mapping"))), size=1
                ).item()
            ]

            act_1.append(action[0])
            reward_l.append(self.step(action=action, time=s))
            m1_speeds.append(self.state.get("m_speed"))
            m1_queued_l.append(self.state.get("m_queued"))

        ax1 = plt.subplot(411)
        ax1.plot(m1_queued_l, "-o")
        ax2 = plt.subplot(412)
        ax2.plot(act_1, "-o")
        ax3 = plt.subplot(413)
        ax3.plot(reward_l, "-o")
        ax3.plot(np.zeros_like(reward_l), "-o")
        ax4 = plt.subplot(414)
        ax4.plot(m1_speeds, "-o")
        ax4.plot(20 * np.ones_like(m1_speeds), "-o")
        plt.savefig("m1.png")
        plt.close()


env = Env()
env.plt_relations()
