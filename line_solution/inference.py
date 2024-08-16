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

m_speed_rl = {eqp_idx: [] for eqp_idx in range(kwargs.get("num_of_eqps"))}
m_h_queued_rl = {eqp_idx: [] for eqp_idx in range(kwargs.get("num_of_eqps"))}
m_t_queued_rl = {eqp_idx: [] for eqp_idx in range(kwargs.get("num_of_eqps"))}
m_actions_rl = {eqp_idx: [] for eqp_idx in range(kwargs.get("num_of_eqps"))}

m_h_queued_bl = {eqp_idx: [] for eqp_idx in range(kwargs.get("num_of_eqps"))}
m_t_queued_bl = {eqp_idx: [] for eqp_idx in range(kwargs.get("num_of_eqps"))}


env_step = 500

env = Env(**kwargs)
uph_rl = []
max_step = 500
step_cnt = 0
while sum(env.current_head_queued_list) > 0 and step_cnt <= max_step:
    for eqp_idx in range(kwargs.get("num_of_eqps")):
        state = env.state_dict[eqp_idx]
        m_speed_rl[eqp_idx].append(state.get("m_speed"))
        m_h_queued_rl[eqp_idx].append(env.current_head_queued_list[eqp_idx])
        m_t_queued_rl[eqp_idx].append(env.current_tail_queued_list[eqp_idx])
        action_idx = agent.select_action_idx(
            state_tuple=tuple(v for v in state.values())
        )
        action = agent.action_idx_to_action(action_idx=action_idx)
        m_actions_rl[eqp_idx].append(action)
        reward = env.step(action=action, eqp_idx=eqp_idx)
    # uph_rl.append(m_arrived)
    step_cnt += 1

step_cnt = 0
uph_bl = []
env.reset()
while sum(env.current_head_queued_list) > 0 and step_cnt <= max_step:
    for eqp_idx in range(kwargs.get("num_of_eqps")):
        state = env.state_dict[eqp_idx]
        m_h_queued_bl[eqp_idx].append(env.current_head_queued_list[eqp_idx])
        m_t_queued_bl[eqp_idx].append(env.current_tail_queued_list[eqp_idx])
        action = agent.action_idx_to_action(action_idx=0)
        reward = env.step(action=action, eqp_idx=eqp_idx)
    # uph_bl.append(m_arrived)
    step_cnt += 1


fig = make_subplots(rows=3, cols=1)
for eqp_idx in range(kwargs.get("num_of_eqps")):
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

# for eqp_idx in range(kwargs.get("num_of_eqps")):
#     fig.add_trace(
#         go.Scatter(
#             x=np.arange(env_step),
#             y=kwargs.get("init_speed")[0] * np.ones_like(m_speed_rl[eqp_idx]),
#             mode="lines+markers",
#             name=f"speed baseline {eqp_idx}",
#         ),
#         row=1,
#         col=1,
#     )
for eqp_idx in range(kwargs.get("num_of_eqps")):
    fig.add_trace(
        go.Scatter(
            x=np.arange(env_step),
            y=kwargs.get("max_speed")[0] * np.ones_like(m_speed_rl[eqp_idx]),
            line=dict(color="red", dash="dash"),
            name=f"speed upper limit {eqp_idx}",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(env_step),
            y=kwargs.get("min_speed")[0] * np.ones_like(m_speed_rl[eqp_idx]),
            line=dict(color="red", dash="dash"),
            name=f"speed lower limit {eqp_idx}",
        ),
        row=1,
        col=1,
    )
for eqp_idx in range(kwargs.get("num_of_eqps")):
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
# for eqp_idx in range(kwargs.get("num_of_eqps")):

#     fig.add_trace(
#         go.Scatter(
#             x=np.arange(len(m_h_queued_bl[eqp_idx])),
#             y=m_h_queued_bl[eqp_idx],
#             mode="lines+markers",
#             name=f"head queued baseline {eqp_idx}",
#         ),
#         row=2,
#         col=1,
#     )

for eqp_idx in range(kwargs.get("num_of_eqps")):
    fig.add_trace(
        go.Scatter(
            x=np.arange(len(m_t_queued_rl[eqp_idx])),
            y=m_t_queued_rl[eqp_idx],
            mode="lines+markers",
            name=f"tail queued {eqp_idx}",
        ),
        row=3,
        col=1,
    )
# for eqp_idx in range(kwargs.get("num_of_eqps")):

#     fig.add_trace(
#         go.Scatter(
#             x=np.arange(len(m_t_queued_bl[eqp_idx])),
#             y=m_t_queued_bl[eqp_idx],
#             mode="lines+markers",
#             name=f"tail queued baseline {eqp_idx}",
#         ),
#         row=3,
#         col=1,
#     )
# fig.add_trace(
#     go.Scatter(
#         x=np.arange(len(uph_rl)), y=np.cumsum(uph_rl), mode="lines+markers", name="uph"
#     ),
#     row=3,
#     col=1,
# )
# fig.add_trace(
#     go.Scatter(
#         x=np.arange(len(uph_bl)),
#         y=np.cumsum(uph_bl),
#         mode="lines+markers",
#         name="uph baseline",
#     ),
#     row=3,
#     col=1,
# )
plotly.offline.plot(figure_or_data=fig, filename="speed_queue_trend.html")
