# Nightfall Survivors MVP Repeatability Check

- Generated: 2025-11-05 03:41:55 UTC
- Output JSON: `logs/repeatability_20251105T034155Z.json`
- Simulation duration: 300.0s
- Tick rate: 0.50s
- Runs per seed: 2

## Determinism

- Seed 12345: **PASS**
  - ✅ seed
  - ✅ survived
  - ✅ duration
  - ✅ enemies_defeated
  - ✅ enemy_type_counts
  - ✅ level_reached
  - ✅ soul_shards
  - ✅ upgrades_applied
  - ✅ dash_count
  - ✅ events
  - ✅ final_health
  - ✅ event_count
  - ✅ event_digest
  - ✅ events_truncated

- Seed 67890: **PASS**
  - ✅ seed
  - ✅ survived
  - ✅ duration
  - ✅ enemies_defeated
  - ✅ enemy_type_counts
  - ✅ level_reached
  - ✅ soul_shards
  - ✅ upgrades_applied
  - ✅ dash_count
  - ✅ events
  - ✅ final_health
  - ✅ event_count
  - ✅ event_digest
  - ✅ events_truncated

- Seed 424242: **PASS**
  - ✅ seed
  - ✅ survived
  - ✅ duration
  - ✅ enemies_defeated
  - ✅ enemy_type_counts
  - ✅ level_reached
  - ✅ soul_shards
  - ✅ upgrades_applied
  - ✅ dash_count
  - ✅ events
  - ✅ final_health
  - ✅ event_count
  - ✅ event_digest
  - ✅ events_truncated

## Aggregate Metrics

| Metric | Value |
| --- | --- |
| Total Runs | 6 |
| Survival Rate | 1.0 |
| Average Duration | 300.0 |
| Median Duration | 300.0 |
| Average Enemies Defeated | 237.333 |
| Average Swarm Defeated | 53.333 |
| Average Bruiser Defeated | 65.667 |
| Average Level Reached | 5 |
| Average Soul Shards | 119 |
| Average Final Health | 120.0 |
| Average Dash Count | 1 |

## Per-Seed Reports

### Seed 12345

Run 1:

| Field | Value |
| --- | --- |
| seed | 12345 |
| survived | True |
| duration | 300.0 |
| enemies_defeated | 238 |
| enemy_type_counts | {'swarm': 42, 'bruiser': 77} |
| level_reached | 5 |
| soul_shards | 119 |
| upgrades_applied | ['Damage Boost', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire'] |
| dash_count | 2 |
| events | ['Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player dashed to safety', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Hunter reached level 2', 'Applied upgrade: Damage Boost', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp'] |
| final_health | 120.0 |
| event_count | 535 |
| event_digest | bcd54e3014badba5486978adbd746a20655219f9bb6393e18814eff8ea944c08 |
| events_truncated | 485 |

Run 2:

| Field | Value |
| --- | --- |
| seed | 12345 |
| survived | True |
| duration | 300.0 |
| enemies_defeated | 238 |
| enemy_type_counts | {'swarm': 42, 'bruiser': 77} |
| level_reached | 5 |
| soul_shards | 119 |
| upgrades_applied | ['Damage Boost', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire'] |
| dash_count | 2 |
| events | ['Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player dashed to safety', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Hunter reached level 2', 'Applied upgrade: Damage Boost', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp'] |
| final_health | 120.0 |
| event_count | 535 |
| event_digest | bcd54e3014badba5486978adbd746a20655219f9bb6393e18814eff8ea944c08 |
| events_truncated | 485 |

### Seed 67890

Run 1:

| Field | Value |
| --- | --- |
| seed | 67890 |
| survived | True |
| duration | 300.0 |
| enemies_defeated | 237 |
| enemy_type_counts | {'swarm': 62, 'bruiser': 57} |
| level_reached | 5 |
| soul_shards | 119 |
| upgrades_applied | ['Damage Boost', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire'] |
| dash_count | 0 |
| events | ['Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Hunter reached level 2', 'Applied upgrade: Damage Boost', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp'] |
| final_health | 120.0 |
| event_count | 491 |
| event_digest | 58ab827b4d04f85b97d7120d8f0c81a2283cc598874ffa5b62bb791835c3e096 |
| events_truncated | 441 |

Run 2:

| Field | Value |
| --- | --- |
| seed | 67890 |
| survived | True |
| duration | 300.0 |
| enemies_defeated | 237 |
| enemy_type_counts | {'swarm': 62, 'bruiser': 57} |
| level_reached | 5 |
| soul_shards | 119 |
| upgrades_applied | ['Damage Boost', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire'] |
| dash_count | 0 |
| events | ['Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Hunter reached level 2', 'Applied upgrade: Damage Boost', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp'] |
| final_health | 120.0 |
| event_count | 491 |
| event_digest | 58ab827b4d04f85b97d7120d8f0c81a2283cc598874ffa5b62bb791835c3e096 |
| events_truncated | 441 |

### Seed 424242

Run 1:

| Field | Value |
| --- | --- |
| seed | 424242 |
| survived | True |
| duration | 300.0 |
| enemies_defeated | 237 |
| enemy_type_counts | {'swarm': 56, 'bruiser': 63} |
| level_reached | 5 |
| soul_shards | 119 |
| upgrades_applied | ['Damage Boost', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire'] |
| dash_count | 1 |
| events | ['Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Hunter reached level 2', 'Applied upgrade: Damage Boost', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp'] |
| final_health | 120.0 |
| event_count | 504 |
| event_digest | afbebc15e347f234130d718f1b24745ba688fc8b9902203f03f248de2b8e1318 |
| events_truncated | 454 |

Run 2:

| Field | Value |
| --- | --- |
| seed | 424242 |
| survived | True |
| duration | 300.0 |
| enemies_defeated | 237 |
| enemy_type_counts | {'swarm': 56, 'bruiser': 63} |
| level_reached | 5 |
| soul_shards | 119 |
| upgrades_applied | ['Damage Boost', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire', 'Rapid Fire'] |
| dash_count | 1 |
| events | ['Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Hunter reached level 2', 'Applied upgrade: Damage Boost', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp', 'Player struck Grave Wisp', 'Collected soul shard from Grave Wisp', 'Spawned Grave Wisp'] |
| final_health | 120.0 |
| event_count | 504 |
| event_digest | afbebc15e347f234130d718f1b24745ba688fc8b9902203f03f248de2b8e1318 |
| events_truncated | 454 |
