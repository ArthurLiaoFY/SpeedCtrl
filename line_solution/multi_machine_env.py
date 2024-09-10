# %%
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
        self.machine_unit_count = 0

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
            self.machine_unit_count += 1


class EnvScanner(sim.Component):
    def __init__(self, scan_interval: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scan_interval = scan_interval
        self.reset()

    def reset(self) -> None:
        self.eqp_state_dict = defaultdict(list)
        self.eqp_reward_dict = defaultdict(list)
        self.machine_speed_dict = defaultdict(list)
        self.machine_uph_dict = defaultdict(list)
        self.current_action_idx = {}

    def reward(self, machine_id: str, eqp_state: dict):
        # part 1, effect other machine
        part_1 = (
            -1000
            if 5 in eqp_state.get("pm_state") or 4 in eqp_state.get("nm_state")
            else 0
        )

        # part 2, resource waste
        part_2 = 0

        # part 3, buffer stack
        part_3 = -1 * (
            eqp_state.get("balancing_coef", 0.7) * eqp_state.get("head_queued")
            + (1.0 - eqp_state.get("balancing_coef", 0.7))
            * eqp_state.get("tail_queued")
        )

        # part 4, uph
        part_4 = (
            self.machine_uph_dict[machine_id][-1]
            - self.machine_uph_dict[machine_id][-2]
        )

        return part_1 + part_2 + part_3 + part_4

    def process(self) -> None:
        while True:
            # feed state to eqp agent
            for machine_id in simulate_machine_config.keys():
                if len(self.eqp_state_dict[machine_id]) > 0:
                    eqp_state = self.eqp_state_dict[machine_id][-1]
                else:
                    self.machine_uph_dict[machine_id].append(0)
                    eqp_state = {
                        "pm_state": [
                            status_code
                            for status_code, status in simulate_obj.get(
                                simulate_obj.get(machine_id, {}).get("prev_machine_id"),
                                {},
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
                                simulate_obj.get(machine_id, {}).get("next_machine_id"),
                                {},
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
                self.current_action_idx[machine_id] = action_idx
                action = simulate_obj[machine_id]["eqp_agent"].action_idx_to_action(
                    action_idx
                )

                simulate_obj[machine_id]["machine"].machine_cycletime = np.clip(
                    a=simulate_obj[machine_id]["machine"].machine_cycletime + action[0],
                    a_max=15,
                    a_min=5,
                ).item()
                self.machine_speed_dict[machine_id].append(
                    simulate_obj[machine_id]["machine"].machine_cycletime
                )

            # wait until next scan
            self.hold(self.scan_interval)

            for machine_id in simulate_machine_config.keys():
                self.machine_uph_dict[machine_id].append(
                    simulate_obj[machine_id]["machine"].machine_unit_count
                )
                reward = self.reward(
                    machine_id=machine_id, eqp_state=self.eqp_state_dict[machine_id][-1]
                )
                new_eqp_state = {
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
                simulate_obj[machine_id]["eqp_agent"].update_policy(
                    state_tuple=tuple(
                        v
                        for k, v in self.eqp_state_dict[machine_id][-1].items()
                        if k not in ("pm_state", "m_state", "nm_state")
                    ),
                    action_idx=self.current_action_idx[machine_id],
                    reward=reward,
                    next_state_tuple=tuple(
                        v
                        for k, v in new_eqp_state.items()
                        if k not in ("pm_state", "m_state", "nm_state")
                    ),
                )

                self.eqp_state_dict[machine_id].append(new_eqp_state)
                self.eqp_reward_dict[machine_id].append(reward)



env = sim.Environment(
    trace=simulate_setup_config.get("trace_env"),
    # random_seed=simulate_setup_config.get("seed"),
)
simulate_obj = {
    **{
        simulate_setup_config.get("sn_feeder", {}).get("id"): SNGenerator(
            name=simulate_setup_config.get("sn_feeder", {}).get("name"),
            env=env,
        )
    },
    **{
        machine_id: {
            "eqp_agent": Agent(**agent_config),
            "machine": Machine(
                name=machine_infos.get("machine_name"),
                machine_id=machine_id,
                machine_cycletime=float(
                    simulate_machine_config.get(machine_id).get(
                        "machine_cycletime"
                    )
                ),
                env=env,
            ),
            "head_buffer": sim.Store(
                f"{machine_infos.get('machine_name')} 前方緩存區",
                capacity=simulate_machine_config.get(machine_id, {}).get(
                    "max_head_buffer"
                ),
                env=env,
            ),
            "tail_buffer": sim.Store(
                f"{machine_infos.get('machine_name')} 後方緩存區",
                capacity=simulate_machine_config.get(machine_id, {}).get(
                    "max_tail_buffer"
                ),
                env=env,
            ),
            "status": {
                status_code: sim.State(
                    name=cn_name,
                    value=False,
                    env=env,
                )
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
                env=env,
            ),
        }
        for conveyer_id, conveyer_infos in simulate_conveyer_config.items()
    },
    **{
        simulate_setup_config.get("sn_receiver", {}).get("id"): sim.Store(
            name=simulate_setup_config.get("sn_receiver", {}).get("name"),
            env=env,
        )
    },
}
env_scanner = EnvScanner(
    scan_interval=simulate_setup_config.get("env_scan_interval"),
)
env_scanner.activate(at=simulate_setup_config.get("env_scan_interval"))

env.run(till=simulate_setup_config.get("run_till"))


print(simulate_obj[simulate_setup_config.get("sn_receiver", {}).get("id")].length())
# %%

import matplotlib.pyplot as plt

plt.plot(
    [
        sd.get("m_cycletime")
        for sd in env_scanner.eqp_state_dict["14a23e75-caa0-40bc-aeec-b559445f7915"]
    ]
)
plt.show()
# %%
plt.plot(
    [None]
    + [
        sd for sd in env_scanner.eqp_reward_dict["14a23e75-caa0-40bc-aeec-b559445f7915"]
    ],
    "o",
)
plt.show()
# %%
[
    sd.get("tail_queued")
    for sd in env_scanner.eqp_state_dict["14a23e75-caa0-40bc-aeec-b559445f7915"]
]
# %%
plt.plot(env_scanner.machine_uph_dict["14a23e75-caa0-40bc-aeec-b559445f7915"])
plt.plot(
    range(len(env_scanner.machine_uph_dict["14a23e75-caa0-40bc-aeec-b559445f7915"])),
    range(len(env_scanner.machine_uph_dict["14a23e75-caa0-40bc-aeec-b559445f7915"])),
)
# %%
plt.plot(
    [
        v - i
        for v, i in zip(
            env_scanner.machine_uph_dict["14a23e75-caa0-40bc-aeec-b559445f7915"],
            range(
                len(
                    env_scanner.machine_uph_dict["14a23e75-caa0-40bc-aeec-b559445f7915"]
                )
            ),
        )
    ]
)
plt.plot(
    [
        0
        for i in range(
            len(env_scanner.machine_uph_dict["14a23e75-caa0-40bc-aeec-b559445f7915"])
        )
    ]
)


# %%
