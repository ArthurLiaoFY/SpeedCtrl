import numpy as np


class EqpEnv:
    def __init__(self, eqp_idx: int, **kwargs) -> None:
        self.eqp_idx = eqp_idx
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):
        # 目標生產總數量 [checked]
        self.current_unprocessed_amount = self.sim_production_quantity

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
            "pm_speed": self.pm_speed,
            "m_speed": self.init_speed_dict.get(self.eqp_idx),
            "nm_speed": self.nm_speed,
            "balancing_coef": self.balancing_coef_dict.get(self.eqp_idx),
            "head_queued": self.current_head_queued // 3 * 3,
            "tail_queued": self.current_tail_queued // 3 * 3,
        }

    def step(
        self,
        action: int,
    ):
        arrived_amount = (
            min(
                self.current_unprocessed_amount,
                max(
                    0,  # 不可小於0
                    int(
                        self.pm_speed * 1.5 + np.random.randn() * 2
                    ),  # 前方設備最大能耐
                ),
                self.m_max_head_buffer - self.current_head_queued,
            )
            if self.current_head_queued <= self.m_max_head_buffer
            else 0
        )
        self.current_unprocessed_amount -= arrived_amount

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
                max(
                    0,  # 不可小於0
                    int(m_depart_ability + np.random.randn() * 2),  # 當前速度最大能耐
                ),
                self.m_max_tail_buffer
                - self.current_tail_queued,  # 後方緩存區最多可收數量
            )
            if m_working and m_speed_after_action != 0
            else 0
        )

        # 離站產品數量
        nm_shipping_amount = int(self.nm_speed * 1.5 + np.random.randn() * 2)

        new_head_queued = head_queued_after_arrive - m_depart_actual
        new_tail_queued = (
            0
            if self.eqp_idx == self.num_of_eqps - 1
            else max(
                0,
                self.current_tail_queued + m_depart_actual - nm_shipping_amount,
            )
        )

        # uph 越大越好
        uph_target = m_depart_actual

        # 待料是很嚴重的loss
        if self.current_tail_queued >= self.m_max_tail_buffer:
            new_status = 0
            effect_other_machine_loss = -2 * m_depart_ability
        else:
            new_status = 1
            effect_other_machine_loss = 0

        # 做毫無意義的動作造成資源浪費
        resource_waste = 0.1 * abs(action) * min(0, m_depart_actual - m_depart_ability)

        m_reward = uph_target + effect_other_machine_loss + resource_waste

        # 更新狀態
        # self.pm_speed += action
        # self.nm_speed += action

        self.current_head_queued = new_head_queued
        self.current_tail_queued = new_tail_queued

        self.eqp_state = {
            "m_status": new_status,
            "pm_speed": self.pm_speed,
            "m_speed": m_speed_after_action,
            "nm_speed": self.nm_speed,
            "balancing_coef": self.eqp_state.get("balancing_coef"),
            "head_queued": min(
                self.m_max_head_buffer, self.current_head_queued // 3 * 3
            ),
            "tail_queued": min(
                self.m_max_tail_buffer, self.current_tail_queued // 3 * 3
            ),
        }
        return m_reward, m_depart_actual, m_depart_ability
