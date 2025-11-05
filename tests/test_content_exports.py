from game import combat, config, content
from game import combat, config, content, environment
from game.content_exports import (
    build_content_bundle,
    glyph_synergy_weapon_payloads,
    graveyard_biome_payload,
    launch_hunter_payloads,
)
from game.relics import relic_definitions
from native.client import ContentBundleDTO


def test_graveyard_biome_payload_matches_balance_tables():
    biome = graveyard_biome_payload()
    assert biome["id"] == "biome_graveyard"
    assert biome["final_boss"]["name"] == content.final_boss_blueprint()["name"]

    phase_one = next(entry for entry in biome["phases"] if entry["phase"] == 1)
    balance = phase_one["balance"]
    schedule = balance["spawn_schedule"]
    scaling = balance["wave_scaling"]

    assert schedule["max_density"] == config.SPAWN_PHASES[1].max_density
    assert scaling["base_enemy_count"] == 6
    assert scaling["per_wave_increment"] == 2

    roster_names = {enemy["name"] for enemy in phase_one["enemy_roster"]}
    assert {"Swarm Thrall", "Grave Bat"}.issubset(roster_names)
    assert not phase_one["elite_roster"]

    environment_entry = next(entry for entry in biome["environment"] if entry["phase"] == 1)
    hazard_names = {hazard["name"] for hazard in environment_entry["hazards"]}
    expected_hazards = {blueprint.name for blueprint in environment.hazard_blueprints_for_biome("Graveyard")}
    assert hazard_names == expected_hazards

    barricade_names = {barricade["name"] for barricade in environment_entry["barricades"]}
    expected_barricades = {
        blueprint.name for blueprint in environment.barricade_blueprints_for_biome("Graveyard")
    }
    assert barricade_names == expected_barricades

    weather_names = {weather["name"] for weather in environment_entry["weather_patterns"]}
    expected_weather = {
        blueprint.name for blueprint in environment.weather_patterns_for_biome("Graveyard")
    }
    assert weather_names == expected_weather

    hazard_schedule = environment_entry["schedules"]["hazard"]
    assert hazard_schedule["base_interval"] == config.HAZARD_PHASES[1].base_interval
    assert hazard_schedule["interval_variance"] == config.HAZARD_PHASES[1].interval_variance


def test_launch_hunters_and_weapons_roundtrip_through_importer():
    payload = build_content_bundle()
    bundle = ContentBundleDTO.from_dict(payload)

    assert bundle.version.startswith("vertical_slice")
    assert bundle.biomes and bundle.biomes[0].id == "biome_graveyard"
    assert bundle.biomes[0].final_boss is not None
    assert bundle.biomes[0].phases[0].balance.spawn_schedule.max_density == config.SPAWN_PHASES[1].max_density
    assert bundle.progression.glyph_set_size == config.GLYPH_SET_SIZE
    assert bundle.progression.max_upgrade_options == config.MAX_UPGRADE_OPTIONS
    assert bundle.progression.run_duration_seconds == config.RUN_DURATION_SECONDS

    hunter_ids = {hunter.id for hunter in bundle.hunters}
    expected_hunters = {entry["id"] for entry in launch_hunter_payloads()}
    assert hunter_ids == expected_hunters

    for hunter in bundle.hunters:
        if hunter.signature_glyph:
            assert hunter.signature_glyph in hunter.starting_glyphs
        assert hunter.abilities.dash is not None
        assert hunter.abilities.dash.cooldown == 2.0
        assert hunter.abilities.dash.strength == 26.0

    weapon_synergies = {weapon.glyph_synergy for weapon in bundle.weapons}
    assert {"blood", "storm", "verdant", "inferno"}.issubset(weapon_synergies)
    assert all(len(weapon.tiers) == 4 for weapon in bundle.weapons)

    relic_names = {relic.name for relic in bundle.relics}
    expected_relics = {definition.name for definition in relic_definitions()}
    assert relic_names == expected_relics


def test_weapon_payload_includes_upgrade_descriptions():
    payload = glyph_synergy_weapon_payloads()
    library = combat.weapon_library()

    for weapon in payload:
        tiers = {tier["tier"] for tier in weapon["tiers"]}
        assert tiers == set(library[weapon["name"]].keys())
        assert any(tier.get("description") for tier in weapon["tiers"])
