import plotly
import plotly.graph_objects as go
from agent import Agent
from config import kwargs, np
from env import Env
from plotly.subplots import make_subplots

agent = Agent(**kwargs)
agent.load_table(prefix="single_machine_with_fault_")
agent.shutdown_explore

m_speed_rl = []
m_queued_rl = []
actions_rl = []

m_queued_bl = []


print(kwargs)

env_step = 500

env = Env()
for s in range(env_step):
    state = env.state

    m_speed_rl.append(state.get("m_speed"))
    m_queued_rl.append(state.get("m_queued"))

    action_idx = agent.select_action_idx(state_tuple=tuple(v for v in state.values()))
    action = agent.action_idx_to_action(action_idx=action_idx)
    actions_rl.append(action[0])

    reward = env.step(action=action, time=s)

env.reset()
for s in range(env_step):
    state = env.state

    m_queued_bl.append(state.get("m_queued"))
    action = agent.action_idx_to_action(action_idx=0)
    reward = env.step(action=action, time=s)

fig = make_subplots(rows=3, cols=1)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_speed_rl)), y=m_speed_rl, mode="lines+markers", name="speed"
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=np.arange(500),
        y=20 * np.ones_like(m_speed_rl),
        mode="lines+markers",
        name="speed baseline",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_queued_rl)),
        y=m_queued_rl,
        mode="lines+markers",
        name="queued",
    ),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_queued_bl)),
        y=m_queued_bl,
        mode="lines+markers",
        name="queued baseline",
    ),
    row=2,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(actions_rl)), y=actions_rl, mode="lines+markers", name="action"
    ),
    row=3,
    col=1,
)
plotly.offline.plot(figure_or_data=fig, filename="speed_queue_trend.html")
