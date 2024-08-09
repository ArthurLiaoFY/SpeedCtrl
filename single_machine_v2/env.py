import numpy as np


class Env:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):
        self.m_max_buffer = self.max_buffer.copy()
        self.m_speed = self.init_speed.copy()

        self.state_dict = {
            eqp_idx: {
                "m_status": 1,
                "m_action": self.action_mapping.get(0),
                "m_speed": self.m_speed[eqp_idx],
                "m_queued": 0,
                "m_queued_diff": 0,
            }
            for eqp_idx in range(self.num_of_eqps)
        }

    def step(self, action: tuple, eqp_idx: int, m_arrived: int) -> tuple | float:
        # 操作動作後，當前設備速度
        m_speed_after_action = (
            np.clip(
                a=self.state_dict[eqp_idx].get("m_speed") + action[0],
                a_min=self.min_speed[eqp_idx],
                a_max=self.max_speed[eqp_idx],
            ).item()
            if self.state_dict[eqp_idx].get("m_status")
            else 0
        )
        # 前方設備來貨後, 產品堆疊數量
        m_queued_after_arrive = max(
            0, m_arrived + self.state_dict[eqp_idx].get("m_queued")
        )

        # 是否已經超出最大可緩存產品數量？
        if m_queued_after_arrive > self.m_max_buffer[eqp_idx] and eqp_idx != 0:
            m_queued_after_arrive = min(
                m_queued_after_arrive, self.m_max_buffer[eqp_idx]
            )
            self.state_dict[eqp_idx - 1]["m_status"] = 0
        #

        # 當前速度預期應該要有的產量
        m_depart_ability = m_speed_after_action * 1.5
        # 實際的產量
        m_departed_actual = (
            min(
                m_queued_after_arrive,
                int(m_depart_ability + np.random.uniform(-2, 2)),
            )
            if self.state_dict[eqp_idx].get("m_status")
            else 0
        )

        expectation_gap = m_departed_actual - m_depart_ability
        serious_gap = expectation_gap < -10
        # 產品離站後, 堆疊的產品數量
        m_queued_after_department = max(0, m_queued_after_arrive - m_departed_actual)
        # 堆疊遞減速率差異
        current_m_queued_diff = (
            self.state_dict[eqp_idx].get("m_queued") - m_queued_after_department
        )
        # 回報函數估算
        queued = m_queued_after_department > 0

        # UPH 目標
        uph_target = (
            1 if queued and self.state_dict[eqp_idx].get("m_status") else 0
        ) * (current_m_queued_diff - self.state_dict[eqp_idx].get("m_queued_diff"))
        # 資源使用效率目標
        resource_efficiency = (
            (0.2 if queued else 0.7)
            * (1 if serious_gap and self.state_dict[eqp_idx].get("m_status") else 0)
            * expectation_gap
        )
        # 產品堆疊導致前站滿料損失
        force_station_stop_loss = 0

        reward = uph_target + resource_efficiency + force_station_stop_loss

        # update state

        self.state_dict[eqp_idx] = {
            "m_status": self.state_dict[eqp_idx].get("m_status"),
            "m_action": action[0],
            "m_speed": m_speed_after_action,
            "m_queued": min(
                self.m_max_buffer[eqp_idx], m_queued_after_department // 3 * 3
            ),
            "m_queued_diff": current_m_queued_diff // 3 * 3,
        }
        return reward, m_departed_actual
