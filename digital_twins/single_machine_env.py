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
    def setup(self):
        self.machine_status = {
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
        }

    def switch_to_status(self, status: int):
        for status_code in self.machine_status:
            if status_code == 4:
                self.machine_status[status_code].set(value=True)

            else:
                self.machine_status[status_code].set(value=False)

    def process(self):
        while True:
            while len(head_buffer) == 0:
                self.switch_to_status(status=4)
                self.standby()

            product = self.from_store(head_buffer)

            if self.ispassive():
                self.activate()
            self.switch_to_status(status=0)

            self.hold(sim.Exponential(5))

            while tail_buffer.available_quantity() <= 0:
                self.switch_to_status(status=5)
                self.standby()

            if self.ispassive():
                self.activate()
            self.switch_to_status(status=0)

            self.to_store(tail_buffer, product)


animate = False
run_till = 500
seed = 1122
animate_speed = 16
if animate:
    env = sim.Environment(trace=False, random_seed=seed)
    env.animation_parameters(speed=animate_speed)
    env.background_color("40%gray")

    sim.AnimateImage("./digital_twins/factory-machine.png", x=350, y=400, width=300)
    sim.AnimateImage("./digital_twins/delivery-box.png", x=100, y=400, width=200)
    sim.AnimateImage("./digital_twins/delivery-box.png", x=700, y=400, width=200)

else:
    env = sim.Environment(trace=True, random_seed=seed)


env.total_prod_amount = 0

sn_generator = SNGenerator(name="產品發射器")
conveyor1 = sim.Resource("前方傳輸帶")
head_buffer = sim.Store(name="前方緩存區", capacity=8)
machine = Machine(name="雷射焊錫機")
tail_buffer = sim.Store(name="後方緩存區", capacity=8)
conveyor2 = sim.Resource("後方傳輸帶")
sn_sink = SNSink(name="產品接收器")
if animate:
    hb_animate = sim.AnimateQueue(
        head_buffer,
        x=160,
        y=350,
        title="Head Buffer",
        direction="s",
        id="blue",
        titlefontsize=30,
    )
    tb_animate = sim.AnimateQueue(
        tail_buffer,
        x=760,
        y=350,
        title="Tail Buffer",
        direction="s",
        id="black",
        titlefontsize=30,
    )

with env.video("./digital_twins/demo.mp4"):
    env.animate(animate)
    env.run(run_till)

# sn_generator.status.print_histogram(values=True)
# machine.status.print_histogram(values=True)
# sn_sink.status.print_histogram(values=True)


# head_buffer.print_statistics()
# tail_buffer.print_statistics()
