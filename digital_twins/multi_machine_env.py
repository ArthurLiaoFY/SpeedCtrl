import salabim as sim


class SNGenerator(sim.Component):
    def process(self):
        while True:
            while head_buffer.available_quantity() <= 0:
                self.standby()
            self.request(conveyor1)
            self.hold(2)
            self.release()
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
            self.request(conveyor2)
            self.hold(4)
            self.release()
            product.passivate()
            env.total_prod_amount += 1


class Machine(sim.Component):
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


env = sim.Environment(trace=True)
env.total_prod_amount = 0

sn_generator = SNGenerator(name="產品發射器")
conveyor1 = sim.Resource("前方傳輸帶")
head_buffer = sim.Store(name="前方緩存區", capacity=8)
machine = Machine(name="雷射焊錫機")
tail_buffer = sim.Store(name="後方緩存區", capacity=8)
conveyor2 = sim.Resource("後方傳輸帶")
sn_sink = SNSink(name="產品接收器")


status_0 = sim.State(name="正常生產", value=False)
status_4 = sim.State(name="待料", value=False)
status_5 = sim.State(name="滿料", value=False)


env.run(till=100)
status_0.print_statistics()
status_4.print_statistics()
status_5.print_statistics()


head_buffer.print_statistics()
tail_buffer.print_statistics()
