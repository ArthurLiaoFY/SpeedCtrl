import matplotlib.pyplot as plt
import numpy as np


def flatten(nested_list: list):
    return [x for xs in nested_list for x in xs]


class Env:
    def __init__(self) -> None:
        self.reset()

    def step(self, action: tuple, time: int) -> None:
        # update state infos
        self.m1_speed = np.clip(self.m1_speed + action[0], 0, 100000).item()
        self.m2_speed = np.clip(self.m2_speed + action[1], 0, 100000).item()
        self.m3_speed = np.clip(self.m2_speed + action[2], 0, 100000).item()

        m1_arrived = int(120000 * 0.005 + np.random.uniform(-3, 3))
        m1_departed = min(
            m1_arrived + self.m1_queued,
            int(self.m1_speed * 0.005 + np.random.uniform(-2, 2)),
        )
        m1_queued = max(0, m1_arrived + self.m1_queued - m1_departed)
        self.m1_queued_diff = (
            self.m1_queued - m1_queued
        )  # positive if pressure released, else negative
        self.m1_queued = m1_queued

        m2_arrived = m1_departed + int(np.random.uniform(-3, 3))

        m2_departed = min(
            m2_arrived + self.m2_queued,
            int(self.m2_speed * 0.005 + np.random.uniform(-2, 2)),
        )
        m2_queued = max(0, m2_arrived + self.m2_queued - m2_departed)
        self.m2_queued_diff = (
            self.m2_queued - m2_queued
        )  # positive if pressure released, else negative
        self.m2_queued = m2_queued

        m3_arrived = m2_departed + int(np.random.uniform(-3, 3))
        m3_departed = min(
            m3_arrived + self.m3_queued,
            int(self.m3_speed * 0.005 + np.random.uniform(-2, 2)),
        )
        m3_queued = max(0, m3_arrived + self.m3_queued - m3_departed)
        self.m3_queued_diff = (
            self.m3_queued - m3_queued
        )  # positive if pressure released, else negative
        self.m3_queued = m3_queued

        # update reward after action
        have_fault = int(
            bool(
                self.m1_fault_trend[time]
                + self.m2_fault_trend[time]
                + self.m3_fault_trend[time]
            )
        )

        reward = (1 - have_fault) * (
            -3000 + m1_departed + m2_departed + m3_departed
        ) + (self.m1_queued_diff + self.m2_queued_diff + self.m3_queued_diff)
        # 無停幾時最大化ＵＰＨ，無論何時queue amount都不要太高

        self.state = {
            "m1_speed": self.m1_speed,
            "m2_speed": self.m2_speed,
            "m3_speed": self.m3_speed,
            "m1_queued": self.m1_queued_diff,
            "m2_queued": self.m2_queued_diff,
            "m3_queued": self.m3_queued_diff,
            "m1_fault": self.m1_fault_trend[time],
            "m2_fault": self.m2_fault_trend[time],
            "m3_fault": self.m3_fault_trend[time],
        }

        return reward

    def reset(self):
        self.m1_fault_trend = flatten(
            [
                [np.random.choice(a=[0, 1], size=1, replace=False, p=[0.9, 0.1]).item()]
                * int(np.random.uniform(low=0, high=100))
                for _ in range(500)
            ]
        )
        self.m2_fault_trend = flatten(
            [
                [np.random.choice(a=[0, 1], size=1, replace=False, p=[0.9, 0.1]).item()]
                * int(np.random.uniform(low=0, high=100))
                for _ in range(500)
            ]
        )
        self.m3_fault_trend = flatten(
            [
                [np.random.choice(a=[0, 1], size=1, replace=False, p=[0.9, 0.1]).item()]
                * int(np.random.uniform(low=0, high=100))
                for _ in range(500)
            ]
        )
        self.m1_speed = 50000
        self.m2_speed = 50000
        self.m3_speed = 50000

        self.m1_queued = 0
        self.m2_queued = 0
        self.m3_queued = 0

        self.m1_queued_diff = 0
        self.m2_queued_diff = 0
        self.m3_queued_diff = 0

        self.state = {
            "m1_speed": self.m1_speed,
            "m2_speed": self.m2_speed,
            "m3_speed": self.m3_speed,
            "m1_queued": self.m1_queued_diff,
            "m2_queued": self.m2_queued_diff,
            "m3_queued": self.m3_queued_diff,
            "m1_fault": self.m1_fault_trend[0],
            "m2_fault": self.m2_fault_trend[0],
            "m3_fault": self.m3_fault_trend[0],
        }

    def plt_relations(self, step: int = 20):
        m1_speeds = []
        m2_speeds = []
        m3_speeds = []
        act_1 = []
        act_2 = []
        act_3 = []
        m1_arrived_l = []
        m1_departed_l = []
        m1_queued_l = []
        m2_arrived_l = []
        m2_departed_l = []
        m2_queued_l = []
        m3_arrived_l = []
        m3_departed_l = []
        m3_queued_l = []
        for s in range(step):
            action = tuple(
                np.random.choice(
                    a=[-2000, -1000, -500, 0, 500, 1000, 2000],
                    size=3,
                    replace=True,
                )
            )

            act_1.append(action[0])
            act_2.append(action[1])
            act_3.append(action[2])

            (
                m1_arrived,
                m1_departed,
                m2_arrived,
                m2_departed,
                m3_arrived,
                m3_departed,
            ) = self.step(action=action, time=s)

            m1_speeds.append(self.state.get("m1_speed"))
            m2_speeds.append(self.state.get("m2_speed"))
            m3_speeds.append(self.state.get("m3_speed"))

            m1_arrived_l.append(m1_arrived)
            m1_departed_l.append(m1_departed)
            m1_queued_l.append(self.state.get("m1_queued"))

            m2_arrived_l.append(m2_arrived)
            m2_departed_l.append(m2_departed)
            m2_queued_l.append(self.state.get("m2_queued"))

            m3_arrived_l.append(m3_arrived)
            m3_departed_l.append(m3_departed)
            m3_queued_l.append(self.state.get("m3_queued"))

        ax1 = plt.subplot(311)
        ax1.plot(m1_arrived_l, "-o")
        ax1.plot(m1_departed_l, "-o")
        ax1.plot(m1_queued_l, "-o")
        ax2 = plt.subplot(312)
        ax2.plot(act_1, "-o")
        ax3 = plt.subplot(313)
        ax3.plot(m1_speeds, "-o")
        ax3.plot(50000 * np.ones_like(m1_speeds), "-o")
        plt.savefig("m1.png")
        plt.close()

        ax1 = plt.subplot(311)
        ax1.plot(m2_arrived_l, "-o")
        ax1.plot(m2_departed_l, "-o")
        ax1.plot(m2_queued_l, "-o")
        ax2 = plt.subplot(312)
        ax2.plot(act_2, "-o")
        ax3 = plt.subplot(313)
        ax3.plot(m2_speeds, "-o")
        ax3.plot(50000 * np.ones_like(m2_speeds), "-o")
        plt.savefig("m2.png")
        plt.close()

        ax1 = plt.subplot(311)
        ax1.plot(m3_arrived_l, "-o")
        ax1.plot(m3_departed_l, "-o")
        ax1.plot(m3_queued_l, "-o")
        ax2 = plt.subplot(312)
        ax2.plot(act_3, "-o")
        ax3 = plt.subplot(313)
        ax3.plot(m3_speeds, "-o")
        ax3.plot(50000 * np.ones_like(m3_speeds), "-o")
        plt.savefig("m3.png")
        plt.close()

        ax1 = plt.subplot(311)
        ax1.plot(self.m1_fault_trend[:step], "-o")
        ax2 = plt.subplot(312)
        ax2.plot(self.m2_fault_trend[:step], "-o")
        ax3 = plt.subplot(313)
        ax3.plot(self.m3_fault_trend[:step], "-o")
        plt.savefig("fault_trend.png")
        plt.close()
