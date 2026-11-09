# Candidate runtime rules for the first two G1 skills

**Scope:** `04_push_shelf_forward` and `07_box_table_to_shelf` in HumanoidMimicGen.
**Status:** research draft for the user's HAZOP and expert review. These are
proposed task-specific extensions of the earlier combination-pliers HAZOP,
not findings that were individually analysed for these two new tasks. They are
not an implemented safety controller, validated limits, or a claim of standards
compliance.

## Task intent and evidence boundary

| Task | Intended sequence | What the upstream success check establishes |
| --- | --- | --- |
| Push Shelf Forward | Find the mobile shelving cart and its box; approach and establish push contact; push toward the target; stop and withdraw. | Shelf upright, shelf within 0.3 m of target in XY, and shelf in contact with box. This is a task-success predicate, not a continuous safety check. |
| Box Table to Shelf | Find box and receiving shelf; grasp, lift, move, place, release, and withdraw. | Box static, upright, and in contact with `shelf_board_1`. This does not prove safe grip force, human clearance, or safe release timing. |

**Target-definition issue to resolve before experiments:** The Box Table to
Shelf `task_config()` refers to `shelf_board_3`, whereas `_get_success_criteria()`
checks contact with `shelf_board_1`. Inspect the generated scene and intended
placement board before defining the placement rule or interpreting success.

The shipped task files define the cart, box, table, shelf, and target, but no
human actor. Human-in-path and hand-in-workspace rules therefore need a separate
human disturbance/scenario before they can be evaluated. The policy-training
projection contains a 43D robot state, one ego RGB view, and 35D WBC-goal
actions. That projected dataset alone does not supply metric human range,
grip/contact force, foot-contact validity, or a safety-rated stop signal.

## Rule vocabulary

- **ALLOW:** continue this proposed action after its required evidence passes.
- **HOLD:** pause task progress while the balance controller maintains stance;
  keep a held object supported and do not open the hands unintentionally.
- **SLOW:** constrain task motion under a measured and validated speed limit.
- **REPLAN:** reject the proposed path/goal and request a new one; use HOLD while
  waiting. A replanner response is subject to the same checks.
- **FAULT LATCH:** hold or enter a separately validated robot-specific fault
  response, request inspection, and require explicit human restart.

No numerical clearance, force, speed, freshness, or stability thresholds are
set here. They require system geometry, load properties, response time,
stopping performance, sensor uncertainty, and expert review. A missing or stale
measurement is **UNKNOWN**, never evidence of a clear path or stable hold.

## Always-on rules for either skill

These run independently of semantic rule retrieval and are checked before and
during execution of an action chunk. A 50-step policy action chunk must remain
interruptible; one check at the chunk boundary is insufficient.

| ID | Proposed rule and trigger | Required evidence | Response | HAZOP link |
| --- | --- | --- | --- | --- |
| C-01 | Do not start or continue hazardous task motion if essential state, command, or perception evidence is missing, stale, inconsistent, or out of order. | Sensor and command timestamps, sequence, quality, controller heartbeat. | HOLD; reacquire. Persistent equipment fault -> FAULT LATCH. | HP-08; I-01, T-08 |
| C-02 | Keep the humanoid within a verified balance/support envelope while moving or holding a load. | Base pose/velocity, IMU, joints, foot contacts, support state. | HOLD with balance control active; use a separately validated fall/fault response if support is lost. | T-01, T-04 |
| C-03 | Do not execute commands outside validated joint, speed, torque, and operating-mode constraints; observed direction must agree with command. | Joint position/velocity/effort, command, mode, limits and calibration. | Reject command; suspected feedback/configuration fault -> FAULT LATCH. | HP-04, HP-08; G-02, G-06, T-05, T-06 |
| C-04 | Do not move the robot, cart, or box through a person's occupied or unobserved relevant swept volume. | Human/hand track, metric 3D position, robot + payload geometry, route, coverage and uncertainty. | HOLD; REPLAN if another route exists. Resume only on fresh clearance and no other stop/fault. | HP-05; T-03, P-05 |
| C-05 | An active protective/operator stop overrides policy, task planner, and delayed action queues. | Stop state, controller mode, action-queue ownership, sequence. | Discard unsafe queued actions; HOLD or FAULT LATCH as appropriate. | T-05, T-08 |

## Skill A: Push Shelf Forward

| ID | Phase | Proposed rule and trigger | Required evidence | Response | HAZOP link |
| --- | --- | --- | --- | --- | --- |
| S-01 | Identify | Start pushing only after the selected mobile shelf, carried box, target zone, and intended push side are consistently localized. | Object identity/pose, target association, 3D geometry, observation validity. | HOLD and reacquire; REPLAN if approach is unsuitable. | HP-02; I-04, I-06, I-07 |
| S-02 | Prepare contact | Require the planned hand/cart contact points and nearby grip area to be clear before applying push force. Do not infer contact from a completed command. | Hand and cart poses, contact state, nearby hand/person occupancy. | HOLD until contact and clearance are established. | HP-03, HP-05; G-01, G-04, G-05 |
| S-03 | Push | Keep cart speed, push force/torque, direction, and robot balance within validated bounds. Monitor observed cart motion, not only requested velocity. | Cart and base velocity, joint effort, contact forces, trajectory, support state. | SLOW or HOLD; reverse/mismatched actuation -> FAULT LATCH. | HP-04, HP-05; T-02, T-06 |
| S-04 | Push | Keep the box supported on the cart and the cart upright throughout travel; detect box sliding, falling, or cart tipping before continuing. | Box/cart relative pose, contact, linear/angular velocity, tilt. | HOLD and stabilize; REPLAN or ask for help if load is no longer secure. | HP-03, HP-07; G-03, P-03, P-04 |
| S-05 | Push | Keep the full cart + box + robot envelope clear of humans and obstacles along the proposed swept path; recheck as the scene changes. | 3D occupancy, path prediction, metric range, time-aligned tracks. | HOLD before contact; REPLAN around a confirmed obstruction. | HP-05; T-03, T-07, T-08 |
| S-06 | Finish | Stop cart motion in the intended target region without overshoot; release push contact and withdraw only after cart and load are settled. | Target-relative cart pose/velocity, box contact, cart uprightness, withdrawal path. | HOLD until settled; REPLAN placement or ask for help if unstable. | HP-06, HP-07; P-01, P-05, P-08 |

## Skill B: Box Table to Shelf

| ID | Phase | Proposed rule and trigger | Required evidence | Response | HAZOP link |
| --- | --- | --- | --- | --- | --- |
| B-01 | Identify | Confirm the requested box, table, intended receiving board, available shelf region, and two-hand grasp poses before approach. Resolve the board-name mismatch above. | Object/board identity, 6D poses, occupancy, shelf geometry, valid transforms. | HOLD and reacquire; do not select a board by guesswork. | HP-02, HP-07; I-04, I-06, I-07 |
| B-02 | Grasp | Keep hands and other objects out of the closing region; apply a box-appropriate bounded grip and verify actual two-hand contact. | Grip-area occupancy, finger/joint state, contact/force and box pose. | HOLD; do not lift or increase force blindly. | HP-03, HP-04, HP-05; G-01, G-02, G-05, G-07 |
| B-03 | Lift | Lift only after a stable hold is established and load/robot balance remain within validated bounds. | Bilateral contact or equivalent hold evidence, box motion, effort, base/foot state. | HOLD if hold is uncertain; avoid unintended opening. | HP-03, HP-08; G-03, G-04, G-08, T-01 |
| B-04 | Transport | Retain the hold and keep box orientation, speed, and full payload path within validated limits. | Box/hand relative pose, contact/slip, box angular velocity, geometry, human/obstacle tracks. | SLOW or HOLD; REPLAN path if clearance fails. | HP-03, HP-05; G-03, T-02, T-03, T-08 |
| B-05 | Place | Use the designated shelf region with adequate margin from edges and clearance from people/objects. | Shelf board and box geometry, 3D occupancy, planned contact/edge margin. | HOLD; REPLAN placement or ask for help when no suitable area is known. | HP-05, HP-07; P-03, P-05, P-07 |
| B-06 | Release | Do not open either hand until box support on the receiving board and load transfer are confirmed. Proximity or task-success text alone is insufficient. | Box-board contact, box pose/velocity, hand forces/contact, support stability. | HOLD and recheck; do not release on UNKNOWN. | HP-06, HP-08; P-01, P-04, P-08 |
| B-07 | Withdraw | Withdraw hands only along a clear path while the released box remains stable; detect any renewed box motion. | Hand path, box pose/velocity, board contact, occupancy. | HOLD or REPLAN withdrawal. | HP-05, HP-07; P-05, P-06 |

## Background scheduler candidates

Fire/smoke, emergency-stop state, sensor health, and controller heartbeat are
independent of the active skill. The baseline MuJoCo scenes do not contain
fire/smoke events or suitable detectors; these rules become testable only after
the scenario and evidence are defined. Fire/smoke should be monitored by an
appropriate dedicated detector or validated sensor/model combination, not by
the task embedding score alone. Do not record an untested scene as "safe."

## What models and sensors are actually needed?

| Function | First implementation in MuJoCo | Model or sensor needed for a camera-based variant | Rule role |
| --- | --- | --- | --- |
| Joint, effort, contact, balance, cart/box stability, support | Deterministic checks on MuJoCo state and contacts; preserve the WBC during HOLD. | Encoders, force/torque or tactile feedback, IMU, foot-contact sensing, calibrated state estimator. | Direct low-latency rule evidence; no VLM required. |
| Box, cart, shelf, receiving board and human localization | Simulator object poses provide ground truth labels for evaluation only. | Object/hand/person detector or segmentation plus tracking, 6D pose estimation and calibrated camera geometry. | Identity and pose evidence, with uncertainty. |
| Human/path separation and occlusion | MuJoCo geometry/raycast/depth plus robot and load swept volumes. | Depth/stereo/LiDAR or another metric ranging source; coverage and freshness checks. | Direct clearance evidence. RGB similarity alone is not distance. |
| Rule selection from a large constitution | Task phase and intent first, then candidate retrieval. | SigLIP, EmbeddingGemma or Cosmos-Embed1 can rank relevant rules; compare recall and latency on reviewed clips. | Retrieval only; an embedding score is not a violation verdict. |
| Ambiguous semantic event or explanation | Escalate after fast checks; log evidence and uncertainty. | A VLM/reasoning model such as the configured Cosmos Reason service may help interpret an event and propose a new plan. | Asynchronous analysis; never the sole stop or force-limit path. |
| Fire/smoke background monitoring | Add defined events and simulator truth before claiming coverage. | Dedicated smoke/thermal sensing or validated visual detector; scheduler checks independent of active skill. | Background alert and interruption. |

With only these two tasks, task ID and phase can select the relevant rules
deterministically. An embedding encoder is **not needed** to load this small
rule set. SigLIP, EmbeddingGemma, and Cosmos-Embed1 remain useful research
comparators when the constitution grows and rule retrieval itself becomes a
measured bottleneck. Their recall must be assessed against reviewed labels;
retrieval misses cannot silently suppress an always-on rule.

**Minimum next experiment:** use the native MuJoCo state as an independent
oracle and instrument one rule per task before adding visual uncertainty:
`S-04` (cart-load retention) and `B-06` (support before release). Log the policy
proposal, evidence timestamp/source, rule decision, actual controller action,
and task outcome. Then compare an unmonitored baseline with the same seeds and
one phase-triggered disturbance. Human-clearance experiments require an added
human actor and perception setup. A task-success predicate is never a safety
metric.

## Sources and limits

- Prior user-led task HAZOP: `live-vlm-webui/docs/usage/combination_pliers_expanded_task_hazop.md`
  and `experiments/combined_task_hazop/study.json` in the sibling repository.
- Task and success definitions: `humanoidmimicgen/locomanipulation/envs/locomanip_push.py`,
  `locomanip_basic.py`, and `utils/scene/success_criteria.py` in this repository.
- [ISO/TS 15066:2016](https://www.iso.org/standard/62996.html) describes
  collaborative industrial robot safety principles. Its published scope is
  industrial robot systems; direct applicability to a mobile humanoid requires
  separate assessment. These candidate rules do not assign ISO thresholds.
