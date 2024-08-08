import plotly
import plotly.graph_objects as go
from agent import Agent
from config import kwargs, np
from env import Env
from plotly.subplots import make_subplots

print(kwargs)
agent = Agent(**kwargs)
agent.load_table(prefix="single_machine_v2_")
agent.shutdown_explore

m_speed_rl = []
m_queued_rl = []
actions_rl = []

m_queued_bl = []


env_step = 500

env = Env(**kwargs)
uph_rl = []
for t in range(env_step):
    m_arrived = np.sin(t / 30) * 20 + 100 + 0.2 * t + np.random.randn() * 5 // 1
    for eqp_idx in range(kwargs.get("num_of_eqps")):
        state = env.state
        m_speed_rl.append(state.get("m_speed"))
        m_queued_rl.append(state.get("m_queued"))
        action_idx = agent.select_action_idx(
            state_tuple=tuple(v for v in state.values())
        )
        action = agent.action_idx_to_action(action_idx=action_idx)
        actions_rl.append(action[0])
        reward, m_arrived = env.step(
            action=action, eqp_idx=eqp_idx, m_arrived=m_arrived
        )
    uph_rl.append(m_arrived)

print(kwargs)
uph_bl = []
env.reset()
for t in range(env_step):
    m_arrived = np.sin(t / 30) * 20 + 100 + 0.2 * t + np.random.randn() * 5 // 1
    for eqp_idx in range(kwargs.get("num_of_eqps")):
        state = env.state
        m_queued_bl.append(state.get("m_queued"))
        action = agent.action_idx_to_action(action_idx=0)
        reward, m_arrived = env.step(
            action=action, eqp_idx=eqp_idx, m_arrived=m_arrived
        )
    uph_bl.append(m_arrived)


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
        y=kwargs.get("init_speed")[0] * np.ones_like(m_speed_rl),
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
        x=np.arange(len(uph_rl)), y=np.cumsum(uph_rl), mode="lines+markers", name="uph"
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(uph_bl)),
        y=np.cumsum(uph_bl),
        mode="lines+markers",
        name="uph baseline",
    ),
    row=3,
    col=1,
)
plotly.offline.plot(figure_or_data=fig, filename="speed_queue_trend.html")
