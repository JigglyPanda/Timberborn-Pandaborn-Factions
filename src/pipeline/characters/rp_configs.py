"""Red panda (Ringtail) proportions, in beaver rest-pose units (before the final size change).

Inputs come from the owner's own game install, dumped to E: (never committed):
  python -I src/pipeline/dump_vanilla_models.py <Timberborn_Data> E:/PandabornDev/reference/vanilla-characters BeaverAdult BeaverChild
  and the beaver AO/normal textures in E:/PandabornDev/reference/vanilla-characters/textures (see README).
"""
import copy
import os

REF = os.environ.get('PANDABORN_CHAR_REF', r'E:\PandabornDev\reference\vanilla-characters')
TEX = os.path.join(REF, 'textures')

# Size of a Ringtail relative to an Inkpaw (= beaver-sized). Baked into every vertex, frame and node.
SIZE = 0.82

ADULT = dict(
    name='BeaverAdult', kind='adult',
    path=os.path.join(REF, 'BeaverAdult.Model.timbermesh'),
    height=0.53, scale=1.0,
    arm_island_x=0.09,
    neck_y=(0.315, 0.355), head_zmin=-0.06, head_strength=1.0, refine_zmin=0.0, ear_refine=1.15,
    # round, broad head; short muzzle; puffy cheeks
    cranium=dict(c=(0, 0.452, 0.036), r=(0.122, 0.092, 0.100)),
    cheek=dict(c=(0.064, 0.408, 0.074), r=(0.072, 0.056, 0.064), k=0.050),
    muzzle=dict(c=(0, 0.410, 0.126), r=(0.044, 0.038, 0.050), k=0.034),
    jaw=dict(c=(0, 0.382, 0.080), r=(0.078, 0.042, 0.074), k=0.055),
    # big pointed ears, set on the upper sides of the head
    ear=dict(c=(0.084, 0.522, 0.008), r=0.050, h=0.080, thick=0.42, sharp=1.0, tip_round=0.22,
             normal_mix=0.62, splay=0.42, lean_back=0.10, base_ellipse=(1.0, 0.72)),
    # slim, long body (the giant panda's is round): pulls the beaver's belly in as well as out
    body=dict(belly_c=(0, 0.150, -0.050), belly_r=(0.120, 0.150, 0.114),
              chest_c=(0, 0.272, -0.028), chest_r=(0.118, 0.090, 0.104), k=0.06,
              strength=0.80, inward_keep=0.95, limb_fade=0.06, leg_fade=(0.07, 0.15)),
    limbs=dict(arm=0.003, leg=0.004, arm_fade=0.10, leg_len=0.16),
    tubes=dict(arm_reach=0.05, arm_scale=1.25, paw_scale=1.15, paw_len=0.07, bin=0.008,
               leg_reach=0.17, leg_scale=1.22, foot_y=0.035,
               paw_short=0.85, paw_wide=1.06, paw_puff=1.15, paw_anchor_dz=-0.015),
    tail_root=(0, 0.095, -0.205), tail_bind_zone=0.03,
    # the long bushy ringed tail, built on the beaver's paddle (which drives it in every animation)
    tail=dict(length=0.46, r_root=0.047, r_max=0.060, t_max=0.35, t_cap=0.78, root_y=0.104,
              rest_clear=0.006, settle_t=0.50, curl=0.022, curl_t=0.70, slices=10, root_blend=0.16),
    teeth_hide=(0, 0.405, 0.125),
    bind_radius=0.03,
    smooth_iters=5,
    cavity=dict(free_uv=(0.8496, 0.9180), free_r=0.044),
    node_adjust={'#Head': dict(dpos=(0, 0.010, -0.004), scale=1.12)},
    beaver_ao=os.path.join(TEX, 'Adult_AO_2K.png'),
)

CHILD = dict(
    name='BeaverChild', kind='child',
    path=os.path.join(REF, 'BeaverChild.Model.timbermesh'),
    height=0.32, scale=0.6,
    arm_island_x=0.06,
    neck_y=(0.180, 0.215), head_zmin=-0.04, head_strength=1.0, refine_zmin=0.0, ear_refine=1.15,
    cranium=dict(c=(0, 0.272, 0.026), r=(0.098, 0.084, 0.084)),
    cheek=dict(c=(0.042, 0.246, 0.052), r=(0.052, 0.044, 0.048), k=0.036),
    muzzle=dict(c=(0, 0.249, 0.078), r=(0.028, 0.023, 0.028), k=0.022),
    jaw=dict(c=(0, 0.230, 0.048), r=(0.058, 0.030, 0.054), k=0.038),
    ear=dict(c=(0.064, 0.330, 0.004), r=0.036, h=0.052, thick=0.46, sharp=1.0, tip_round=0.26,
             normal_mix=0.60, splay=0.38, lean_back=0.08, base_ellipse=(1.0, 0.74)),
    body=dict(belly_c=(0, 0.090, -0.026), belly_r=(0.084, 0.094, 0.084),
              chest_c=(0, 0.158, -0.012), chest_r=(0.072, 0.054, 0.068), k=0.04,
              strength=0.75, inward_keep=0.85, limb_fade=0.04, leg_fade=(0.045, 0.09)),
    limbs=dict(arm=0.002, leg=0.0025, arm_fade=0.065, leg_len=0.10),
    tubes=dict(arm_reach=0.035, arm_scale=1.25, paw_scale=1.18, paw_len=0.045, bin=0.006,
               leg_reach=0.10, leg_scale=1.25, foot_y=0.022,
               paw_short=0.82, paw_wide=1.08, paw_puff=1.2, paw_anchor_dz=-0.010),
    tail_root=(0, 0.048, -0.118), tail_bind_zone=0.02,
    tail=dict(length=0.22, r_root=0.026, r_max=0.044, t_max=0.40, t_cap=0.78, root_y=0.050,
              rest_clear=0.004, settle_t=0.40, curl=0.020, curl_t=0.70, slices=8, root_blend=0.18),
    teeth_hide=(0, 0.250, 0.072),
    bind_radius=0.02,
    smooth_iters=5,
    beaver_ao=os.path.join(TEX, 'Child_AO_1K.png'),
    cavity=dict(region=dict(z=0.06, y=(0.205, 0.252), y_top=0.258), target_xy=(0.040, 0.240),
                free_uv=(0.8262, 0.9590), free_r=0.020),
)


def get(name):
    return copy.deepcopy({'ADULT': ADULT, 'CHILD': CHILD}[name.upper()])
