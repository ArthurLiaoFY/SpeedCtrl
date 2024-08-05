import plotly
import plotly.graph_objects as go
from config import kwargs, np
from single_machine.env import Env
from plotly.subplots import make_subplots

from agent import Agent

agent = Agent(**kwargs)
agent.load_table(prefix="single_machine_")
agent.shutdown_explore

m_speed_l = []
m_queued_l = []
actions = []

print(kwargs)

env_step = 40

env = Env()
for s in range(env_step):
    state = env.state

    m_speed_l.append(state.get("m_speed"))
    m_queued_l.append(state.get("m_queued"))

    action_idx = agent.select_action_idx(state_tuple=tuple(v for v in state.values()))
    action = agent.action_idx_to_action(action_idx=action_idx)
    actions.append(action[0])

    reward = env.step(action=action, time=s)


fig = make_subplots(rows=3, cols=1)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_speed_l)), y=m_speed_l, mode="lines+markers", name="speed"
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_queued_l)), y=m_queued_l, mode="lines+markers", name="queued"
    ),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(actions)), y=actions, mode="lines+markers", name="action"
    ),
    row=3,
    col=1,
)
plotly.offline.plot(figure_or_data=fig, filename="speed_queue_trend.html")
