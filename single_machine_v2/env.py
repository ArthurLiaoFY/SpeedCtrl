import numpy as np


class Env:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):
        # 記錄模擬開始時緩存區堆貨上限值 [checked]
        self.m_max_head_buffer = self.max_head_buffer
        self.m_max_tail_buffer = self.max_tail_buffer

        # 記錄實時緩存區堆貨情況, 及緩存區堆貨遞增/遞減速率 [checked]
        self.current_head_queued_list = [self.sim_production_quantity] + [
            0 for _ in range(self.num_of_eqps - 1)
        ]
        self.current_tail_queued_list = [0 for _ in range(self.num_of_eqps)]
        self.current_queued_diff_list = [0 for _ in range(self.num_of_eqps)]

        # 記錄實時速度 [checked]
        self.m_speed = self.init_speed.copy()

        # 記錄實時狀態 [checked]
        self.state_dict = {
            eqp_idx: {
                "m_status": 1,
                "m_action": self.action_mapping.get(0),
                "m_speed": self.m_speed[eqp_idx],
                "m_amb_head_queued": min(
                    self.ambiguous_upper_bound,
                    self.current_head_queued_list[eqp_idx] // 3 * 3,
                ),
                "m_amb_tail_queued": min(
                    self.ambiguous_upper_bound,
                    self.current_tail_queued_list[eqp_idx] // 3 * 3,
                ),
                "m_amb_queued_diff": min(
                    self.ambiguous_upper_bound,
                    self.current_tail_queued_list[eqp_idx] // 3 * 3,
                ),
            }
            for eqp_idx in range(self.num_of_eqps)
        }

    def step(self, action: int, eqp_idx: int) -> tuple | float:
        # 斷定是否為首站或末站 [checked]
        first_station = bool(eqp_idx == 0)
        last_station = bool(eqp_idx == self.num_of_eqps - 1)

        # 前方設備來貨後, 前方緩存區產品堆疊數量 [checked]
        m_head_queued_after_arrive = max(
            0,
            (
                self.current_head_queued_list[eqp_idx]
                if eqp_idx == 0
                else self.current_tail_queued_list[eqp_idx - 1]
                + self.current_head_queued_list[eqp_idx]
            ),
        )
        ############################################
        # [生產前的狀態確認, 將斷定當前設備狀態是否可以生產]
        ############################################
        # 若來貨後無產品可生產 或是後方緩存區已經無空間收貨, 定為停機.
        if (
            m_head_queued_after_arrive <= 0
            or self.current_tail_queued_list[eqp_idx] == self.m_max_tail_buffer[eqp_idx]
        ):
            # 當前設備待料或是後方滿料
            self.state_dict[eqp_idx]["m_status"] = 0
        else:
            # 當前設備正常生產
            self.state_dict[eqp_idx]["m_status"] = 1

        ############################################
        # [開始生產]
        ############################################
        # 操作動作後，當前設備速度 [checked]
        m_speed_after_action = (
            np.clip(
                a=self.state_dict[eqp_idx].get("m_speed") + action,
                a_min=self.min_speed[eqp_idx],
                a_max=self.max_speed[eqp_idx],
            ).item()
            if self.state_dict[eqp_idx].get("m_status")
            else 0
        )

        # 當前速度預期應該要有的產量 [checked]
        m_depart_ability = m_speed_after_action * 1.5

        # 實際的產量 [checked]
        m_departed_actual = (
            min(
                m_head_queued_after_arrive,  # 最多可離站產品數量
                int(m_depart_ability + np.random.uniform(-2, 2)),  # 當前速度最大能耐
            )
            if self.state_dict[eqp_idx].get("m_status")
            else 0
        )  # 有可能其輸出的產品數量大過後面可承接的緩存數量, 屆時會依此判定當前設備是否滿料

        # 期望產量與實際產量落差, 若差距超過 5 視為嚴重的 gap [checked]
        expectation_gap = m_departed_actual - m_depart_ability
        serious_gap = expectation_gap < -5

        ####################################
        # [回報計算]
        ####################################
        m_head_queued_after_depart = m_head_queued_after_arrive - m_departed_actual
        # 當前待料遞減速度差異
        current_m_queued_diff = m_head_queued_after_arrive - m_head_queued_after_depart
        # 回報函數估算
        queued = m_head_queued_after_depart > 0

        # UPH 目標
        uph_target = (
            1 if queued and self.state_dict[eqp_idx].get("m_status") else 0
        ) * (current_m_queued_diff - self.current_queued_diff_list[eqp_idx])
        # 資源使用效率目標
        resource_efficiency = (
            (0.2 if queued else 0.7)
            * (1 if serious_gap and self.state_dict[eqp_idx].get("m_status") else 0)
            * expectation_gap
        )
        # 產品堆疊導致前站滿料損失
        force_station_stop_loss = 0

        reward = uph_target + resource_efficiency + force_station_stop_loss

        ####################################
        # [生產後的狀態賦予, 將賦予狀態給前後設備]
        ####################################
        # 產品離站後, 前方緩存區產品堆疊的數量
        if (
            m_head_queued_after_depart >= self.m_max_head_buffer[eqp_idx]
        ) and not first_station:
            self.current_head_queued_list[eqp_idx] = self.m_max_head_buffer[eqp_idx]
            self.current_tail_queued_list[eqp_idx - 1] = (
                m_head_queued_after_depart - self.m_max_head_buffer[eqp_idx]
            )
        else:
            self.current_head_queued_list[eqp_idx] = m_head_queued_after_depart
        # 產品離站後, 後方緩存區產品堆疊的數量
        m_tail_queued_after_depart = (
            (
                self.current_tail_queued_list[eqp_idx]
                + self.current_head_queued_list[eqp_idx + 1]
                + m_departed_actual
            )
            if not last_station
            else (self.current_tail_queued_list[eqp_idx] + m_departed_actual)
        )

        if (
            m_tail_queued_after_depart >= self.m_max_tail_buffer[eqp_idx]
        ) and not last_station:
            self.current_head_queued_list[eqp_idx + 1] = self.m_max_tail_buffer[eqp_idx]
            self.current_tail_queued_list[eqp_idx] = (
                m_tail_queued_after_depart - self.m_max_tail_buffer[eqp_idx]
            )
        else:
            self.current_tail_queued_list[eqp_idx] = m_tail_queued_after_depart

        self.current_queued_diff_list[eqp_idx] = current_m_queued_diff

        self.state_dict[eqp_idx] = {
            "m_status": self.state_dict[eqp_idx].get("m_status"),
            "m_action": action,
            "m_speed": m_speed_after_action,
            "m_amb_head_queued": min(
                self.ambiguous_upper_bound,
                self.current_head_queued_list[eqp_idx] // 3 * 3,
            ),
            "m_amb_tail_queued": min(
                self.ambiguous_upper_bound,
                self.current_tail_queued_list[eqp_idx] // 3 * 3,
            ),
            "m_amb_queued_diff": min(
                self.ambiguous_upper_bound,
                self.current_queued_diff_list[eqp_idx] // 3 * 3,
            ),
        }

        if not first_station:
            self.state_dict[eqp_idx - 1].update(
                {
                    "m_amb_tail_queued": min(
                        self.ambiguous_upper_bound,
                        self.current_tail_queued_list[eqp_idx - 1] // 3 * 3,
                    ),
                }
            )
        elif not last_station:
            self.state_dict[eqp_idx + 1].update(
                {
                    "m_amb_head_queued": min(
                        self.ambiguous_upper_bound,
                        self.current_head_queued_list[eqp_idx + 1] // 3 * 3,
                    ),
                }
            )
        else:
            self.state_dict[eqp_idx + 1].update(
                {
                    "m_amb_head_queued": min(
                        self.ambiguous_upper_bound,
                        self.current_head_queued_list[eqp_idx + 1] // 3 * 3,
                    ),
                }
            )
            self.state_dict[eqp_idx - 1].update(
                {
                    "m_amb_tail_queued": min(
                        self.ambiguous_upper_bound,
                        self.current_tail_queued_list[eqp_idx - 1] // 3 * 3,
                    ),
                }
            )

        return reward
