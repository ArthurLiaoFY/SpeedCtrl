import copy

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
        self.current_head_queued_list = [0 for _ in range(self.num_of_eqps)]
        self.current_tail_queued_list = [0 for _ in range(self.num_of_eqps)]
        self.current_queued_diff_list = [0 for _ in range(self.num_of_eqps)]

        # 記錄實時速度 [checked]
        self.m_speed = copy.deepcopy(self.init_speed)

        # 記錄實時狀態 [checked]
        self.state_dict = {
            eqp_idx: {
                "m_status": 1,
                "m_action": self.action_mapping.get(0),
                "m_speed": self.m_speed[eqp_idx],
                "m_anb_head_queued": 0,
                "m_anb_tail_queued": 0,
                "m_anb_queued_diff": 0,
            }
            for eqp_idx in range(self.num_of_eqps)
        }

    def step(self, action: int, eqp_idx: int, m_arrived: int = 0) -> tuple | float:
        # 斷定是否為首站或末站 [checked]
        first_station = bool(eqp_idx == 0)
        last_station = bool(eqp_idx == self.num_of_eqps - 1)

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
        # 前方設備來貨後, 前方緩存區產品堆疊數量 [checked]
        m_head_queued_after_arrive = max(
            0,
            (
                m_arrived + self.current_head_queued_list[eqp_idx]
                if eqp_idx == 0
                else self.current_tail_queued_list[eqp_idx - 1]
                + self.current_head_queued_list[eqp_idx]
            ),
        )
        # 若來貨後, 無產品可生產
        if m_head_queued_after_arrive <= 0:
            # 當前設備待料
            self.state_dict[eqp_idx]["m_status"] = 0
        else:
            # 當前設備正常生產
            self.state_dict[eqp_idx]["m_status"] = 1

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

        # 產品離站後, 前方緩存區產品堆疊的數量
        if (
            max(0, m_head_queued_after_arrive - m_departed_actual)
            - self.m_max_head_buffer[eqp_idx]
            >= 0
        ):  # 首台設備不會進入此地, 因為首台 max buffer = 無限
            pm_tail_queued_after_department = (
                max(0, m_head_queued_after_arrive - m_departed_actual)
                - self.m_max_head_buffer[eqp_idx]
            )  # 前方設備尾部緩存情況更新, 若超出尾部緩存極限要更新狀態前方設備狀態為停機(0)
            m_head_queued_after_department = self.m_max_head_buffer[
                eqp_idx
            ]  # 當前設備頭部緩存情況更新, 超出頭部緩存極限要更新狀態前方設備狀態為停機(0)
        else:
            # 前方設備不需要停機
            pm_tail_queued_after_department = 0
            m_head_queued_after_department = max(
                0, m_head_queued_after_arrive - m_departed_actual
            )

        # 若前方緩存區消化完貨後, 超出前方設備緩存極限, 前方設備需要停機
        if first_station:
            pass
            # print("首站供料過快．")
        else:
            if pm_tail_queued_after_department < self.m_max_tail_buffer[eqp_idx - 1]:
                # 前站正常生產
                self.state_dict[eqp_idx - 1]["m_status"] = 1

            else:
                # 前站滿料
                self.state_dict[eqp_idx - 1]["m_status"] = 0

        # 若後方緩存區收到貨後, 超出後方設備緩存極限, 當前設備需要停機
        if (
            self.current_tail_queued_list[eqp_idx] + m_departed_actual
            >= self.m_max_tail_buffer[eqp_idx]
        ):
            self.state_dict[eqp_idx]["m_status"] = 0
            # self.current_tail_queued_list[eqp_idx] = self.m_max_tail_buffer[eqp_idx]
        else:
            self.state_dict[eqp_idx]["m_status"] = 1
            # self.current_tail_queued_list[eqp_idx] += m_departed_actual

        # 當前待料遞減速度差異
        current_m_queued_diff = m_head_queued_after_arrive - (
            pm_tail_queued_after_department + m_head_queued_after_department
        )
        # 回報函數估算
        queued = pm_tail_queued_after_department + m_head_queued_after_department > 0

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

        # update state
        self.current_head_queued_list[eqp_idx] = m_head_queued_after_department
        self.current_queued_diff_list[eqp_idx] = current_m_queued_diff

        self.state_dict[eqp_idx] = {
            "m_status": self.state_dict[eqp_idx].get("m_status"),
            "m_action": action,
            "m_speed": m_speed_after_action,
            "m_anb_head_queued": m_head_queued_after_department // 3 * 3,
            "m_anb_tail_queued": m_departed_actual // 3 * 3,
            "m_anb_queued_diff": current_m_queued_diff // 3 * 3,
        }

        if not first_station:
            self.state_dict[eqp_idx - 1] = {
                "m_status": self.state_dict[eqp_idx - 1]["m_status"],
                "m_action": self.state_dict[eqp_idx - 1]["m_action"],
                "m_speed": self.state_dict[eqp_idx - 1]["m_speed"],
                "m_anb_head_queued": self.state_dict[eqp_idx - 1]["m_anb_head_queued"],
                "m_anb_tail_queued": pm_tail_queued_after_department // 3 * 3,
                "m_anb_queued_diff": self.state_dict[eqp_idx - 1]["m_anb_queued_diff"],
            }
        return reward
