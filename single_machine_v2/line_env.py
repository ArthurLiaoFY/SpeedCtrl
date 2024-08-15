import numpy as np


class LineEnv:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)
        self.reset()

    def reset(self):
        current_head_queued_list = [self.sim_production_quantity] + [
            0 for _ in range(self.num_of_eqps - 1)
        ]
        current_tail_queued_list = [0 for _ in range(self.num_of_eqps)]
        current_queued_diff_list = [0 for _ in range(self.num_of_eqps)]

        buffer_head_queued_list = [None for _ in range(self.num_of_eqps)]
        buffer_tail_queued_list = [None for _ in range(self.num_of_eqps)]
        buffer_queued_diff_list = [None for _ in range(self.num_of_eqps)]

        self.eqp_agent_mapping_dict = {
            eqp_idx: (
                "initial_agent"
                if eqp_idx == 0
                else (
                    "terminal_agent"
                    if eqp_idx == (self.num_of_eqps - 1)
                    else "connect_agent"
                )
            )
            for eqp_idx in range(self.num_of_eqps)
        }

    def step(self):
        pass

        # 斷定是否為首站或末站 [checked]

        # 前方設備來貨後, 前方緩存區產品堆疊數量 [checked]

        ############################################
        # [生產前的狀態確認, 將斷定當前設備狀態是否可以生產]
        ############################################
        # 若來貨後無產品可生產 或是後方緩存區已經無空間收貨, 定為停機.

        ############################################
        # [開始生產]
        ############################################
        # 操作動作後，當前設備速度 [checked]

        # 當前速度預期應該要有的產量 [checked]

        # 實際的產量 [checked]

        ####################################
        # [回報計算]
        ####################################
        reward = None
        ####################################
        # [生產後的狀態賦予, 將賦予狀態給前後設備]
        ####################################
        # 產品離站後, 前方緩存區產品堆疊的數量

        # 產品離站後, 後方緩存區產品堆疊的數量

        return reward
