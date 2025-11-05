from game import combat, config, content
from game.content_exports import (
    build_content_bundle,
    glyph_synergy_weapon_payloads,
    graveyard_biome_payload,
    launch_hunter_payloads,
)
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


def test_launch_hunters_and_weapons_roundtrip_through_importer():
    payload = build_content_bundle()
    bundle = ContentBundleDTO.from_dict(payload)

    assert bundle.version.startswith("vertical_slice")
    assert bundle.biomes and bundle.biomes[0].id == "biome_graveyard"
    assert bundle.biomes[0].final_boss is not None
    assert bundle.biomes[0].phases[0].balance.spawn_schedule.max_density == config.SPAWN_PHASES[1].max_density

    hunter_ids = {hunter.id for hunter in bundle.hunters}
    expected_hunters = {entry["id"] for entry in launch_hunter_payloads()}
    assert hunter_ids == expected_hunters

    weapon_synergies = {weapon.glyph_synergy for weapon in bundle.weapons}
    assert {"blood", "storm", "verdant", "inferno"}.issubset(weapon_synergies)
    assert all(len(weapon.tiers) == 4 for weapon in bundle.weapons)


def test_weapon_payload_includes_upgrade_descriptions():
    payload = glyph_synergy_weapon_payloads()
    library = combat.weapon_library()

    for weapon in payload:
        tiers = {tier["tier"] for tier in weapon["tiers"]}
        assert tiers == set(library[weapon["name"]].keys())
        assert any(tier.get("description") for tier in weapon["tiers"])
