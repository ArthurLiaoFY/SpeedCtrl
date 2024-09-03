import salabim as sim


class SNGenerator(sim.Component):
    def process(self):
        while True:
            while simulate_config["machine_1"]["head_buffer"].available_quantity() <= 0:
                self.standby()
            product = SN()
            self.hold(1 / conveyer_speed)
            self.to_store(simulate_config["machine_1"]["head_buffer"], product)


class SN(sim.Component):
    def process(self):
        while True:
            self.passivate()

    def animation_objects(self, id):
        """
        for animation
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
        self, from_idx: int, to_idx: int, conveyer_speed: int, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.from_idx = from_idx
        self.to_idx = to_idx
        self.conveyer_speed = conveyer_speed

    def process(self):
        if self.from_idx != 0:
            while (
                len(
                    simulate_config.get(f"machine_{self.from_idx}", {}).get(
                        "tail_buffer"
                    )
                )
                <= 0
            ):
                self.standby()

            product = self.from_store(
                simulate_config[f"machine_{self.from_idx}"]["tail_buffer"]
            )

        product.hold(1 / self.conveyer_speed)

        if self.from_idx == num_of_machine:
            # to sink
            self.to_store(simulate_config["sn_receiver"], product)
        else:
            while (
                simulate_config.get(f"machine_{self.to_idx}", {})
                .get("head_buffer")
                .available_quantity()
                == 0
            ):
                self.standby()
            self.to_store(
                simulate_config[f"machine_{self.to_idx}"]["head_buffer"], product
            )


class Machine(sim.Component):
    def __init__(self, machine_idx: int, machine_speed: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.machine_idx = machine_idx
        self.machine_speed = machine_speed

    def switch_to_status(self, status: int):
        for status_code in simulate_config[f"machine_{self.machine_idx}"][
            "status"
        ].keys():
            if status_code == status:
                simulate_config[f"machine_{self.machine_idx}"]["status"][
                    status_code
                ].set(value=True)

            else:
                simulate_config[f"machine_{self.machine_idx}"]["status"][
                    status_code
                ].set(value=False)

    def process(self):
        while True:
            while (
                len(
                    simulate_config.get(f"machine_{self.machine_idx}", {}).get(
                        "head_buffer"
                    )
                )
                == 0
            ):
                self.switch_to_status(status=4)
                self.standby()

            product = self.from_store(
                simulate_config[f"machine_{self.machine_idx}"]["head_buffer"]
            )

            self.switch_to_status(status=0)

            self.hold(sim.Exponential(1 / self.machine_speed))

            while (
                simulate_config.get(f"machine_{self.machine_idx}", {})
                .get("tail_buffer")
                .available_quantity()
                <= 0
            ):
                self.switch_to_status(status=5)
                self.standby()

            self.switch_to_status(status=0)

            self.to_store(
                simulate_config[f"machine_{self.machine_idx}"]["tail_buffer"], product
            )


# data_file_path = "./digital_twins"
# unity_config = json.load(open(f'{data_file_path}/unity_config.json'))
# unity_config.get('Layoutdata', {}).get("Device")
seed = 1122
run_till = 50000
trace_env = False

env = sim.Environment(trace=trace_env, random_seed=seed)

env.total_prod_amount = 0
num_of_machine = 3
conveyer_speed = 1 / 2
machine_speed = 1 / 5

simulate_config = {
    **{"sn_feeder": SNGenerator(name="半成品發射器")},
    **{
        f"machine_{i+1}": {
            "machine": Machine(
                name=f"設備({i+1})", machine_idx=i + 1, machine_speed=machine_speed
            ),
            "tail_buffer": sim.Store(f"設備({i+1}) 後方緩存區", capacity=8),
            "head_buffer": sim.Store(f"設備({i+1}) 前方緩存區", capacity=8),
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
        for i in range(num_of_machine)
    },
    **{
        f"conveyer_{i}_{i+1}": {
            "conveyer": Conveyer(
                name=f"傳輸帶({i}至{i+1})",
                from_idx=i,
                to_idx=i + 1,
                conveyer_speed=conveyer_speed,
            ),
        }
        for i in range(1, num_of_machine + 1)
    },
    **{"sn_receiver": sim.Store(name="成品接收器")},
}
connection_config = {}


env.run(till=run_till)

simulate_config["machine_1"]["status"][4].print_statistics()
simulate_config["machine_1"]["status"][5].print_statistics()
simulate_config["machine_2"]["status"][4].print_statistics()
simulate_config["machine_2"]["status"][5].print_statistics()
simulate_config["machine_3"]["status"][4].print_statistics()
simulate_config["machine_3"]["status"][5].print_statistics() 
simulate_config["sn_receiver"].print_statistics() 
