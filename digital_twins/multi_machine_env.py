import json

import salabim as sim


class SNGenerator(sim.Component):
    def process(self):
        while True:
            while head_buffer.available_quantity() <= 0:
                self.standby()
            self.request((conveyor1, 1))
            self.hold(2)
            self.release((conveyor1, 1))
            SN().enter(head_buffer)


class SN(sim.Component):
    def process(self):
        while True:
            self.passivate()


class SNSink(sim.Component):
    def process(self):
        while True:
            while tail_buffer.available_quantity() == tail_buffer.capacity.value:
                self.standby()
            product = self.from_store(tail_buffer)
            self.request((conveyor2, 1))
            self.hold(4)
            self.release((conveyor2, 1))
            product.passivate()
            env.total_prod_amount += 1


class Machine(sim.Component):
    def __init__(self, machine_order: int = 0, speed: int = 50000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.machine_order = machine_order
        self.speed = speed

    @staticmethod
    def waiting_for_materials():
        status_0.set(value=False)
        status_4.set(value=True)
        status_5.set(value=False)

    @staticmethod
    def waiting_for_seats():
        status_0.set(value=False)
        status_4.set(value=False)
        status_5.set(value=True)

    @staticmethod
    def normal_production():
        status_0.set(value=True)
        status_4.set(value=False)
        status_5.set(value=False)

    def process(self):
        while True:
            while len(head_buffer) == 0:
                self.waiting_for_materials()
                self.standby()

            product = self.from_store(head_buffer)

            if self.ispassive():
                self.activate()
            self.normal_production()

            self.hold(sim.Exponential(5))

            while tail_buffer.available_quantity() <= 0:
                self.waiting_for_seats()
                self.standby()

            if self.ispassive():
                self.activate()
            self.normal_production()

            self.to_store(tail_buffer, product)


# data_file_path = "./digital_twins"
# unity_config = json.load(open(f'{data_file_path}/unity_config.json'))
# unity_config.get('Layoutdata', {}).get("Device")

env = sim.Environment(trace=True)
env.total_prod_amount = 0
num_of_machine = 5


simulate_config = {
    **{"sn_feeder": SNGenerator(name="半成品發射器")},
    **{
        f"machine_{i+1}": {
            "machine": Machine(name=f"設備({i+1})"),
            "head_buffer": sim.Resource(f"設備({i+1}) 前方緩存區", capacity=8),
            "tail_buffer": sim.Resource(f"設備({i+1}) 後方緩存區", capacity=8),
            "status_0": sim.State(name=f"設備({i+1}) 正常生產", value=False),
            "status_4": sim.State(name=f"設備({i+1}) 待料", value=False),
            "status_5": sim.State(name=f"設備({i+1}) 滿料", value=False),
        }
        for i in range(num_of_machine)
    },
    **{"sn_receiver": SNSink(name="成品接收器")},
}
connection_config = {}


# env.run(till=100)
# print(env.total_prod_amount)
