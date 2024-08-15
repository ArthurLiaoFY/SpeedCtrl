import numpy as np


class EqpEnv:
    def __init__(self, eqp_idx: int, **kwargs) -> None:
        self.eqp_idx = eqp_idx
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):
        # 目標生產總數量 [checked]
        self.current_requested = self.sim_production_quantity

        # 記錄實時速度 [checked]
        self.pm_speed = self.init_speed_dict.get(self.eqp_idx - 1, self.feeding_speed)
        self.nm_speed = self.init_speed_dict.get(self.eqp_idx + 1, self.shipping_speed)
        self.min_speed = self.min_speed_dict.get(self.eqp_idx)
        self.max_speed = self.max_speed_dict.get(self.eqp_idx)

        # 記錄模擬開始時緩存區堆貨上限值 [checked]
        self.m_max_head_buffer = self.max_head_buffer_dict.get(self.eqp_idx)
        self.m_max_tail_buffer = self.max_tail_buffer_dict.get(self.eqp_idx)

        # 記錄精確, 當前緩存區緩存數量 [checked]
        self.current_head_queued = 0
        self.current_tail_queued = 0

        # 初始化狀態
        self.eqp_state = {
            "m_status": self.init_status_dict.get(self.eqp_idx),
            "m_speed": self.init_speed_dict.get(self.eqp_idx),
            "balancing_coef": self.balancing_coef_dict.get(self.eqp_idx),
            "head_queued": self.current_head_queued // 3 * 3,
            "tail_queued": self.current_tail_queued // 3 * 3,
        }

    def step(
        self,
        action: int,
    ):
        arrived_amount = min(
            self.current_requested, int(self.pm_speed * 1.5 + np.random.uniform(-2, 2))
        )
        self.current_requested -= arrived_amount

        head_queued_after_arrive = self.current_head_queued + arrived_amount

        m_working = self.eqp_state.get("m_status")
        m_speed_after_action = (
            np.clip(
                a=self.eqp_state.get("m_speed") + action,
                a_min=self.min_speed,
                a_max=self.max_speed,
            ).item()
            if m_working
            else 0
        )

        # 當前速度預期應該要有的產量 [checked]
        m_depart_ability = m_speed_after_action * 1.5

        # 實際的產量 [checked]
        m_depart_actual = (
            min(
                head_queued_after_arrive,  # 最多可離站產品數量
                int(
                    m_depart_ability + np.random.uniform(-2, 2) * m_working
                ),  # 當前速度最大能耐
                self.m_max_tail_buffer
                - self.eqp_state.get("tail_queued"),  # 後方緩存區最多可收數量
            )
            if m_working
            else 0
        )

        #
        nm_shipping_amount = int(self.nm_speed * 1.5 + np.random.uniform(-2, 2))

        uph_target = self.eqp_state.get("balancing_coef") * m_depart_actual

        resource_efficiency = (
            (1 - self.eqp_state.get("balancing_coef"))
            * 0.5
            * (m_depart_actual - m_depart_ability)
        )

        m_reward = uph_target + resource_efficiency

        # 更新狀態
        self.current_head_queued = head_queued_after_arrive - m_depart_actual
        self.current_tail_queued = max(
            0, self.eqp_state.get("tail_queued") + m_depart_actual - nm_shipping_amount
        )
        if self.current_tail_queued >= self.m_max_tail_buffer:
            new_status = 0
        else:
            new_status = 1

        self.eqp_state = {
            "m_status": new_status,
            "m_speed": m_speed_after_action,
            "balancing_coef": self.eqp_state.get("balancing_coef"),
            "head_queued": min(
                self.m_max_head_buffer, self.current_head_queued // 3 * 3
            ),
            "tail_queued": min(
                self.m_max_tail_buffer, self.current_tail_queued // 3 * 3
            ),
        }
        return m_reward
