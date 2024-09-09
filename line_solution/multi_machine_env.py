import salabim as sim
from agent import Agent, np
from config import (
    agent_config,
    defaultdict,
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
    def __init__(
        self,
        machine_id: str,
        machine_cycletime: int,
        # machine_speed: int,
        # lm_coefs: tuple,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.machine_id = machine_id
        # self.machine_speed = machine_speed
        # self.machine_cycletime = lm_coefs[0] + lm_coefs[1] * self.machine_speed + lm_coefs[2] * np.random.randn()
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


class EnvScanner(sim.Component):
    def __init__(self, scan_interval: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scan_interval = scan_interval
        self.reset()

    def reset(self) -> None:
        self.eqp_state_dict = defaultdict(list)
        self.eqp_reward_dict = defaultdict(list)

    def reward(self, eqp_state: dict):
        # part 1, effect other machine
        part_1 = (
            -1000
            if 5 in eqp_state.get("pm_state") or 4 in eqp_state.get("nm_state")
            else 0
        )

        # part 2, resource waste
        part_2 = 0

        # part 3, buffer stack
        part_3 = eqp_state.get("balancing_coef", 0.7) * (
            eqp_state.get("head_queued")
        ) + (1.0 - eqp_state.get("balancing_coef", 0.7)) * (
            eqp_state.get("tail_queued")
        )

        return part_1 + part_2 + part_3

    def process(self) -> None:
        while True:
            # feed state to eqp agent
            for machine_id in simulate_machine_config.keys():
                eqp_state = {
                    "pm_state": [
                        status_code
                        for status_code, status in simulate_obj.get(
                            simulate_obj.get(machine_id, {}).get("prev_machine_id"), {}
                        )
                        .get("status", {})
                        .items()
                        if status() == True
                    ],
                    "m_state": [
                        status_code
                        for status_code, status in simulate_obj.get(machine_id, {})
                        .get("status", {})
                        .items()
                        if status() == True
                    ],
                    "nm_state": [
                        status_code
                        for status_code, status in simulate_obj.get(
                            simulate_obj.get(machine_id, {}).get("next_machine_id"), {}
                        )
                        .get("status", {})
                        .items()
                        if status() == True
                    ],
                    "m_cycletime": simulate_obj.get(machine_id, {})
                    .get("machine")
                    .machine_cycletime,
                    "balancing_coef": 0.7,
                    "head_queued": len(
                        simulate_obj.get(machine_id, {}).get("head_buffer")
                    ),
                    "tail_queued": len(
                        simulate_obj.get(machine_id, {}).get("tail_buffer")
                    ),
                }
                self.eqp_state_dict[machine_id].append(eqp_state)
                action_idx = simulate_obj[machine_id]["eqp_agent"].select_action_idx(
                    state_tuple=tuple(
                        v
                        for k, v in eqp_state.items()
                        if k not in ("pm_state", "m_state", "nm_state")
                    )
                )
                action = simulate_obj[machine_id]["eqp_agent"].action_idx_to_action(
                    action_idx
                )

                reward = self.reward(eqp_state=eqp_state.copy())
                self.eqp_reward_dict[machine_id].append(reward)

                simulate_obj[machine_id]["machine"].machine_cycletime = np.clip(
                    a=simulate_obj[machine_id]["machine"].machine_cycletime + action[0],
                    a_max=15,
                    a_min=5,
                )

            # wait until next scan
            self.hold(self.scan_interval)


env = sim.Environment(
    trace=simulate_setup_config.get("trace_env"),
    # random_seed=simulate_setup_config.get("seed"),
)
env_scanner = EnvScanner(scan_interval=simulate_setup_config.get("env_scan_interval"))
env_scanner.activate(at=simulate_setup_config.get("env_scan_interval"))


simulate_obj = {
    **{
        simulate_setup_config.get("sn_feeder", {}).get("id"): SNGenerator(
            name=simulate_setup_config.get("sn_feeder", {}).get("name")
        )
    },
    **{
        machine_id: {
            "eqp_agent": Agent(**agent_config),
            "machine": Machine(
                name=machine_infos.get("machine_name"),
                machine_id=machine_id,
                machine_cycletime=float(
                    simulate_machine_config.get(machine_id).get("machine_cycletime")
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
