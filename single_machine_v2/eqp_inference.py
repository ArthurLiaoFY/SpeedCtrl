import plotly
import plotly.graph_objects as go
from agent import Agent
from config import eqp_kwargs, np
from eqp_env import EqpEnv
from plotly.subplots import make_subplots

print(eqp_kwargs)
agent = Agent(**eqp_kwargs)
agent.load_table(prefix="single_machine_v2_feeding_speed_60_shipping_speed_60_")
agent.shutdown_explore

m_speed_rl = {eqp_idx: [] for eqp_idx in range(eqp_kwargs.get("num_of_eqps"))}
m_h_queued_rl = {eqp_idx: [] for eqp_idx in range(eqp_kwargs.get("num_of_eqps"))}
m_t_queued_rl = {eqp_idx: [] for eqp_idx in range(eqp_kwargs.get("num_of_eqps"))}
m_actions_rl = {eqp_idx: [] for eqp_idx in range(eqp_kwargs.get("num_of_eqps"))}

m_h_queued_bl = {eqp_idx: [] for eqp_idx in range(eqp_kwargs.get("num_of_eqps"))}
m_t_queued_bl = {eqp_idx: [] for eqp_idx in range(eqp_kwargs.get("num_of_eqps"))}


env_step = 500
eqp_idx = 0

env = EqpEnv(eqp_idx=eqp_idx, **eqp_kwargs)
uph_rl = []
max_step = 500
step_cnt = 0
while (
    env.current_head_queued + env.current_unprocessed_amount > 0
    and step_cnt <= max_step
):
    state = env.eqp_state.copy()
    m_speed_rl[eqp_idx].append(state.get("m_speed"))
    m_h_queued_rl[eqp_idx].append(env.current_head_queued)
    m_t_queued_rl[eqp_idx].append(env.current_tail_queued)
    action_idx = agent.select_action_idx(state_tuple=tuple(v for v in state.values()))
    action = agent.action_idx_to_action(action_idx=action_idx)
    m_actions_rl[eqp_idx].append(action)
    reward = env.step(action=action)
    # uph_rl.append(m_arrived)
    step_cnt += 1

step_cnt = 0
uph_bl = []
env.reset()
while (
    env.current_head_queued + env.current_unprocessed_amount > 0
    and step_cnt <= max_step
):
    state = env.eqp_state.copy()
    m_h_queued_bl[eqp_idx].append(env.current_head_queued)
    m_t_queued_bl[eqp_idx].append(env.current_tail_queued)
    action = agent.action_idx_to_action(action_idx=0)
    reward = env.step(action=action)
    # uph_bl.append(m_arrived)
    step_cnt += 1


fig = make_subplots(rows=3, cols=1)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_speed_rl[eqp_idx])),
        y=m_speed_rl[eqp_idx],
        mode="lines+markers",
        name=f"speed {eqp_idx}",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=np.arange(env_step),
        y=eqp_kwargs.get("max_speed_dict")[eqp_idx] * np.ones_like(m_speed_rl[eqp_idx]),
        line=dict(color="red", dash="dash"),
        name=f"speed upper limit {eqp_idx}",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(env_step),
        y=eqp_kwargs.get("min_speed_dict")[eqp_idx] * np.ones_like(m_speed_rl[eqp_idx]),
        line=dict(color="red", dash="dash"),
        name=f"speed lower limit {eqp_idx}",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_h_queued_rl[eqp_idx])),
        y=m_h_queued_rl[eqp_idx],
        mode="lines+markers",
        name=f"head queued {eqp_idx}",
    ),
    row=2,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=np.arange(len(m_t_queued_rl[eqp_idx])),
        y=m_t_queued_rl[eqp_idx],
        mode="lines+markers",
        name=f"tail queued {eqp_idx}",
    ),
    row=2,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=np.arange(max(len(m_t_queued_rl[eqp_idx]), len(m_h_queued_rl[eqp_idx]))),
        y=[a + b for a, b in zip(m_t_queued_rl[eqp_idx], m_h_queued_rl[eqp_idx])],
        mode="lines+markers",
        name=f"total queued {eqp_idx}",
    ),
    row=3,
    col=1,
)

plotly.offline.plot(figure_or_data=fig, filename="speed_queue_trend.html")
