import numpy as np


class LineEnv:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):
        # 目標生產總數量 [checked]
        self.current_unprocessed_amount = self.sim_production_quantity

        # 記錄實時速度 [checked]
        self.speed_list = [
            self.eqp_kwargs.get(eqp_idx).get("init_speed")
            for eqp_idx in range(self.num_of_eqps)
        ]
        self.min_speed_list = [
            self.eqp_kwargs.get(eqp_idx).get("min_speed")
            for eqp_idx in range(self.num_of_eqps)
        ]
        self.max_speed_list = [
            self.eqp_kwargs.get(eqp_idx).get("max_speed")
            for eqp_idx in range(self.num_of_eqps)
        ]

        # 記錄模擬開始時緩存區堆貨上限值 [checked]
        self.m_max_head_buffer_list = [
            self.eqp_kwargs.get(eqp_idx).get("max_head_buffer")
            for eqp_idx in range(self.num_of_eqps)
        ]
        self.m_max_tail_buffer_list = [
            self.eqp_kwargs.get(eqp_idx).get("max_tail_buffer")
            for eqp_idx in range(self.num_of_eqps)
        ]

        # 記錄精確, 當前緩存區緩存數量 [checked]
        self.current_head_queued_list = [0 for _ in range(self.num_of_eqps)]
        self.current_tail_queued_list = [0 for _ in range(self.num_of_eqps)]

        # 初始化狀態
        self.line_state = {
            "speed_tuple": tuple(self.speed_list),
            "head_queued_ratio_tuple": tuple(
                [
                    min(val, val_max) / val_max * 100 // 5 * 5
                    for val, val_max in zip(
                        self.current_head_queued_list, self.m_max_head_buffer_list
                    )
                ]
            ),
            "tail_queued_ratio_tuple": tuple(
                [
                    min(val, val_max) / val_max * 100 // 5 * 5
                    for val, val_max in zip(
                        self.current_tail_queued_list, self.m_max_tail_buffer_list
                    )
                ]
            ),
        }

    def step(
        self,
        action: int,
    ):
        line_reward = None
        return line_reward
