import numpy as np


class SubLineEnv:
    def __init__(self, eqp_idx, **kwargs) -> None:
        self.eqp_idx = eqp_idx
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):

        # 記錄模擬開始時緩存區堆貨上限值 [checked]
        self.pm_max_tail_buffer = self.eqp_kwargs.get(self.eqp_idx - 1, {}).get(
            "max_tail_buffer"
        )

        self.m_max_head_buffer = self.eqp_kwargs.get(self.eqp_idx).get(
            "max_head_buffer"
        )
        self.m_max_tail_buffer = self.eqp_kwargs.get(self.eqp_idx).get(
            "max_tail_buffer"
        )

        self.nm_max_head_buffer = self.eqp_kwargs.get(self.eqp_idx + 1, {}).get(
            "max_head_buffer"
        )

        # 記錄模擬開始時緩存區堆貨精確值 [checked]
        self.pm_tail_buffer = 0

        self.m_head_buffer = 0
        self.m_tail_buffer = 0

        self.nm_head_buffer = 0

        # 初始化狀態
        self.line_state = {}

    def step(
        self,
        action: int,
    ):
        line_reward = None
        return line_reward
