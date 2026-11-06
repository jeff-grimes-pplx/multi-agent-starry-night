with open("/home/user/workspace/multi-agent-starry-night/pipeline/build_complete_pipeline.py") as f:
    code = f.read()

old_block = """# Pass D: 450 high-precision edge/spire/corona accent strokes
candidates = []
for y in range(2, H, 6):
    for x in range(2, W, 6):
        candidates.append((float(grad_norm[y, x]), x, y))
candidates.sort(key=lambda t: t[0], reverse=True)
pass_d = []
for score, x, y in candidates[:450]:
    ag = int(agent_map[y, x])
    s = get_stroke_geometry(x, y, length=5.2, width=3.0, agent_id=ag, is_v1=False, rng_local=rng_local)
    s["pass"] = 2
    s["layer"] = "rework_accent"
    pass_d.append(s)

# Order strokes inside each pass so each subagent's brush cursor moves smoothly and organically across its territory
def sort_strokes_by_spatial_sweep(stroke_list):
    # Group into small spatial strips so the cursor paints like a real hand moving across a region
    return sorted(stroke_list, key=lambda s: (s["y"] // 28, s["x"] if (s["y"] // 28) % 2 == 0 else -s["x"]))

# Let's interleave the 5 subagents across Pass 1 (pass_a + pass_b) and Pass 2 (pass_c + pass_d)
# so during playback all 5 subagent cursors are actively painting in parallel!
p1_by_ag = {ag: sort_strokes_by_spatial_sweep([s for s in (pass_a + pass_b) if s["agent"] == ag]) for ag in range(1, 6)}
p2_by_ag = {ag: sort_strokes_by_spatial_sweep([s for s in (pass_c + pass_d) if s["agent"] == ag]) for ag in range(1, 6)}

def interleave_agent_lists(by_ag):
    max_len = max(len(v) for v in by_ag.values())
    out = []
    for i in range(max_len):
        for ag in (1, 2, 5, 4, 3): # painter's order within each micro-step
            lst = by_ag[ag]
            # map proportional index
            idx_start = int(i * len(lst) / max_len)
            idx_end = int((i + 1) * len(lst) / max_len)
            for k in range(idx_start, idx_end):
                out.append(lst[k])
    return out

ordered_pass1 = interleave_agent_lists(p1_by_ag)
ordered_pass2 = interleave_agent_lists(p2_by_ag)"""

new_block = """# Pass D: 850 high-precision edge/spire/corona accent strokes (especially village & corona edges)
candidates = []
for y in range(2, H, 5):
    for x in range(2, W, 5):
        bonus = 0.25 if agent_map[y, x] in (2, 4) else 0.0
        candidates.append((float(grad_norm[y, x]) + bonus, x, y))
candidates.sort(key=lambda t: t[0], reverse=True)
pass_d = []
for score, x, y in candidates[:850]:
    ag = int(agent_map[y, x])
    s = get_stroke_geometry(x, y, length=5.2, width=3.2, agent_id=ag, is_v1=False, rng_local=rng_local)
    s["pass"] = 2
    s["layer"] = "rework_accent"
    pass_d.append(s)

def sort_strokes_by_spatial_sweep(stroke_list):
    return sorted(stroke_list, key=lambda s: (s["y"] // 28, s["x"] if (s["y"] // 28) % 2 == 0 else -s["x"]))

def interleave_layer(layer_strokes):
    by_ag = {ag: sort_strokes_by_spatial_sweep([s for s in layer_strokes if s["agent"] == ag]) for ag in range(1, 6)}
    max_len = max(len(v) for v in by_ag.values())
    out = []
    for i in range(max_len):
        for ag in (1, 2, 5, 4, 3):
            lst = by_ag[ag]
            idx_start = int(i * len(lst) / max_len)
            idx_end = int((i + 1) * len(lst) / max_len)
            for k in range(idx_start, idx_end):
                out.append(lst[k])
    return out

ordered_pass1 = interleave_layer(pass_a) + interleave_layer(pass_b)
ordered_pass2 = interleave_layer(pass_c) + interleave_layer(pass_d)"""

assert old_block in code, "old_block not found"
code = code.replace(old_block, new_block)
with open("/home/user/workspace/multi-agent-starry-night/pipeline/build_complete_pipeline.py", "w") as f:
    f.write(code)
