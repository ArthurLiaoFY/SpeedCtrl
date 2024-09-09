import salabim as sim
from agent import Agent
from config import (
    simulate_conveyer_config,
    simulate_machine_config,
    simulate_setup_config,
)


class SNGenerator(sim.Component):
    def process(self):
        while True:
            while (
                sum(
                    [
                        simulate_obj.get(to_id, {})
                        .get("head_buffer")
                        .available_quantity()
                        for to_id in simulate_setup_config.get("sn_feeder", {}).get(
                            "to_ids"
                        )
                    ]
                )
                <= 0
            ):
                self.standby()
            for to_id in simulate_setup_config.get("sn_feeder", {}).get("to_ids"):
                if (
                    simulate_obj.get(to_id, {}).get("head_buffer").available_quantity()
                    <= 0
                ):
                    continue
                else:
                    product = SN()
                    self.hold(
                        # simulate_conveyer_config.get(
                        #     f'{simulate_setup_config.get("sn_feeder", {}).get("id")}#{to_id}'
                        # ).get("conveyer_cycletime")
                        1
                    )
                    self.to_store(
                        simulate_obj[to_id]["head_buffer"],
                        product,
                    )


class SN(sim.Component):
    # data component

    def animation_objects(self, id):
        """
        the way the component is determined by the id, specified in AnimateQueue
        'text' means just the name
        any other value represents the color
        """
        if id == "text":
            animate_text = sim.AnimateText(
                text=self.name(), textcolor="fg", text_anchor="nw"
            )
            return 15, 0, animate_text
        else:
            animate_rectangle = sim.AnimateRectangle(
                (
                    -20,
                    0,
                    20,
                    20,
                ),  # (x lower left, y lower left, x upper right, y upper right)
                text=self.name(),
                fillcolor=id,
                textcolor="white",
                arg=self,
            )
            return 0, 30, animate_rectangle


class Conveyer(sim.Component):
    """
    send product from machine A tail buffer area to machine B head buffer area
    """

    def __init__(
        self, from_id: str, to_id: str, conveyer_cycletime: int, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.from_id = from_id
        self.to_id = to_id
        self.conveyer_cycletime = conveyer_cycletime

    def process(self):
        while True:
            while len(simulate_obj.get(self.from_id, {}).get("tail_buffer")) <= 0:
                self.standby()

            product = self.from_store(simulate_obj[self.from_id]["tail_buffer"])

            self.hold(self.conveyer_cycletime)

            if self.to_id == simulate_setup_config.get("sn_receiver", {}).get("id"):
                # to sink
                product.enter(
                    simulate_obj[simulate_setup_config.get("sn_receiver", {}).get("id")]
                )

            else:
                while (
                    simulate_obj.get(self.to_id, {})
                    .get("head_buffer")
                    .available_quantity()
                    == 0
                ):
                    self.standby()
                self.to_store(simulate_obj[self.to_id]["head_buffer"], product)


class Machine(sim.Component):
    def __init__(self, machine_id: str, machine_cycletime: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.machine_id = machine_id
        self.machine_cycletime = machine_cycletime

    def switch_to_status(self, status: int):
        for status_code in simulate_obj[self.machine_id]["status"].keys():
            if status_code == status:
                simulate_obj[self.machine_id]["status"][status_code].set(value=True)

            else:
                simulate_obj[self.machine_id]["status"][status_code].set(value=False)

    def process(self):
        while True:
            while len(simulate_obj.get(self.machine_id, {}).get("head_buffer")) == 0:
                self.switch_to_status(status=4)
                self.standby()

            product = self.from_store(simulate_obj[self.machine_id]["head_buffer"])

            self.switch_to_status(status=0)

            self.hold(self.machine_cycletime)

            while (
                simulate_obj.get(self.machine_id, {})
                .get("tail_buffer")
                .available_quantity()
                <= 0
            ):
                self.switch_to_status(status=5)
                self.standby()

            self.switch_to_status(status=0)

            self.to_store(simulate_obj[self.machine_id]["tail_buffer"], product)


# class EnvScanner(sim.Component):
#     def __init__(self, scan_interval: int = 5, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.scan_interval = scan_interval

#     def reward(self):
#         pass

#     def process(self):
#         while True:
#             # feed state to eqp agent
#             for i in range(num_of_machine):
#                 eqp_state = {
#                     "m_speed": simulate_obj.get(f"machine_{i+1}")
#                     .get("machine")
#                     .machine_speed,
#                     "balancing_coef": 0.7,
#                     "head_queued": len(
#                         simulate_obj.get(f"machine_{i+1}", {}).get("head_buffer")
#                     ),
#                     "tail_queued": len(
#                         simulate_obj.get(f"machine_{i+1}", {}).get("tail_buffer")
#                     ),
#                 }
#                 action_idx = agent.select_action_idx(
#                     state_tuple=tuple(v for v in eqp_state.values())
#                 )
#                 action = agent.action_idx_to_action(action_idx=action_idx)
#             # feed state to line agent

#             len(simulate_obj["sn_receiver"])

#             # wait until next scan
#             self.hold(self.scan_interval)


env = sim.Environment(
    trace=simulate_setup_config.get("trace_env", False),
    random_seed=simulate_setup_config.get("seed", 1122),
)
# agent = Agent()

simulate_obj = {
    **{
        simulate_setup_config.get("sn_feeder", {}).get("id"): SNGenerator(
            name=simulate_setup_config.get("sn_feeder", {}).get("name")
        )
    },
    **{
        machine_id: {
            "machine": Machine(
                name=machine_infos.get("machine_name"),
                machine_id=machine_id,
                machine_cycletime=simulate_machine_config.get(machine_id).get(
                    "machine_cycletime"
                ),
            ),
            "head_buffer": sim.Store(
                f"{machine_infos.get('machine_name')} 前方緩存區",
                capacity=simulate_machine_config.get(machine_id, {}).get(
                    "max_head_buffer"
                ),
            ),
            "tail_buffer": sim.Store(
                f"{machine_infos.get('machine_name')} 後方緩存區",
                capacity=simulate_machine_config.get(machine_id, {}).get(
                    "max_tail_buffer"
                ),
            ),
            "status": {
                status_code: sim.State(name=cn_name, value=False)
                for status_code, cn_name in zip(
                    range(-1, 13),
                    [
                        "未連線",
                        "正常",
                        "故障",
                        "暫停",
                        "待機",
                        "待料",
                        "滿料",
                        "材料低位",
                        "換線",
                        "缺料",
                        "待啟動",
                        "安全停機",
                        "品質停機",
                        "調機",
                    ],
                )
            },
        }
        for machine_id, machine_infos in simulate_machine_config.items()
    },
    **{
        conveyer_id: {
            "conveyer": Conveyer(
                name=conveyer_infos.get("conveyer_name", ""),
                from_id=conveyer_infos.get("conveyer_from", ""),
                to_id=conveyer_infos.get("conveyer_to", ""),
                conveyer_cycletime=conveyer_infos.get("conveyer_cycletime", 1),
            ),
        }
        for conveyer_id, conveyer_infos in simulate_conveyer_config.items()
    },
    **{
        simulate_setup_config.get("sn_receiver", {}).get("id"): sim.Store( 
            name=simulate_setup_config.get("sn_receiver", {}).get("name")
        )
    },
}


env.run(till=simulate_setup_config.get("run_till"))


print(simulate_obj[simulate_setup_config.get("sn_receiver", {}).get("id")].length())
