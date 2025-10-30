"""Localization utilities for translating prototype strings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping


class SafeFormatDict(dict):
    """Dictionary that leaves unknown fields untouched during formatting."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class LocalizationCatalog:
    """Holds string tables for multiple languages."""

    _languages: Dict[str, Dict[str, str]]

    def __init__(self) -> None:  # type: ignore[override]
        object.__setattr__(self, "_languages", {})

    def register_language(
        self,
        code: str,
        entries: Mapping[str, str],
        *,
        inherit_from: str | None = None,
    ) -> None:
        """Register a language table, optionally inheriting from another."""

        if not code:
            raise ValueError("language code must be provided")
        if inherit_from:
            base = dict(self._languages.get(inherit_from, {}))
        else:
            base = {}
        base.update(entries)
        self._languages[code] = base

    def available_languages(self) -> Iterable[str]:
        return tuple(sorted(self._languages))

    def translator(self, language: str, fallback: str | None = None) -> "Translator":
        if not self._languages:
            raise RuntimeError("no languages registered in catalog")
        primary = language if language in self._languages else fallback or next(iter(self._languages))
        resolved_fallback = fallback or next(iter(self._languages))
        return Translator(self, primary, resolved_fallback)

    def resolve(self, language: str, key: str) -> str | None:
        table = self._languages.get(language)
        if not table:
            return None
        return table.get(key)


class Translator:
    """Translates keys using a catalog with fallback semantics."""

    def __init__(self, catalog: LocalizationCatalog, language: str, fallback: str) -> None:
        self._catalog = catalog
        self._language = language
        self._fallback = fallback

    @property
    def language(self) -> str:
        return self._language

    def translate(self, key: str, **params) -> str:
        template = self._catalog.resolve(self._language, key)
        if template is None:
            template = self._catalog.resolve(self._fallback, key)
        if template is None:
            return key
        return template.format_map(SafeFormatDict(params))


def _build_default_catalog() -> LocalizationCatalog:
    catalog = LocalizationCatalog()

    english_strings: Dict[str, str] = {
        "game.phase_advance": "Phase advanced to {phase}.",
        "game.hazard_trigger": "Hazard triggered: {name} in the {biome} (-{damage} HP).",
        "game.hazard_slow": "Movement hindered by {name}: speed reduced by {percent}% for {duration}s.",
        "game.environment_defeat": "The hunter is overwhelmed by the environment.",
        "game.barricade_cleared": "Barricade cleared: {name} yielded {salvage} salvage.",
        "game.salvage_collected": "Collected {name} for {amount} salvage.",
        "game.weather_clear": "Weather shift: conditions normalize and movement returns to baseline.",
        "game.weather_change": "Weather shift: {name} ({description}) movement {movement:+d}% vision {vision:+d}%",
        "game.upgrade_presented": "Upgrade options presented.",
        "game.glyph_unlocked": "Ultimate unlocked for {family}!",
        "game.glyph_added": "Glyph added: {family}.",
        "game.weapon_upgraded": "Weapon upgraded: {name} tier {tier}.",
        "game.perk_acquired": "Survival perk acquired: {name}.",
        "game.wave_incoming": "Wave {number} incoming with {count} foes.",
        "game.miniboss_incoming": "Miniboss {name} approaches!",
        "game.relic_acquired": "Relic acquired: {name}.",
        "game.final_boss": "The final boss {name} descends for the last stand.",
        "game.final_boss_generic": "The final confrontation begins.",
        "game.encounter_resolved": "Resolved {label} defeating {count} foes in {duration:.1f}s.",
        "game.encounter_aftermath": "Combat aftermath: -{damage} HP, +{healing} HP.",
        "game.player_fallen": "The hunter succumbs to the onslaught.",
        "game.player_survived": "Dawn breaks! The hunter endures the night.",
        "systems.level_up": "Level up! Reached level {level}.",
        "systems.ultimate_unlocked": "Ultimate unlocked for {family} glyphs!",
        "ui.arcade_status": "Time {time:5.1f}s  Phase {phase}  Level {level}  XP {xp}/{next_xp}  HP {hp}/{max_hp}  Score {score}",
        "ui.upgrade_prompt": "Choose Upgrade [1-3]:",
        "ui.upgrade_option": "{index}. {name}",
        "ui.upgrade_selected": "Upgrade chosen: {name}.",
        "ui.damage_taken": "Hit by {enemy} for {damage} damage!",
        "ui.ultimate_ready": "Ultimate unleashed, purging the horde!",
        "ui.run_failed": "RUN FAILED",
        "ui.run_survived": "DAWN REACHED",
        "cli.description": "Nightfall Survivors playable prototype",
        "cli.help.duration": "Session duration in seconds",
        "cli.help.fps": "Target frames per second",
        "cli.help.language": "Language code for UI text",
        "cli.help.assist_radius": "Auto-aim radius modifier for projectiles",
        "cli.help.damage_multiplier": "Incoming damage multiplier (lower for assist)",
        "cli.help.speed_scale": "Game speed multiplier (<1 slows the action)",
        "cli.help.projectile_speed": "Projectile speed multiplier",
        "cli.help.high_contrast": "Enable high-contrast rendering",
        "cli.help.message_log": "Number of messages to keep visible",
        "cli.help.demo": "Apply demo restrictions (limited content)",
        "cli.help.event_id": "Activate a seasonal event by identifier",
        "cli.help.event_year": "Year used when evaluating the seasonal schedule",
        "cli.help.profile_path": "Path to an encrypted profile to load",
        "cli.help.key": "Decryption key for the supplied profile",
    }

    spanish_strings: Dict[str, str] = {
        "game.phase_advance": "Fase avanzada a {phase}.",
        "game.hazard_trigger": "Peligro activado: {name} en {biome} (-{damage} PS).",
        "game.hazard_slow": "Movimiento afectado por {name}: velocidad reducida {percent}% durante {duration}s.",
        "game.environment_defeat": "El cazador cae ante el entorno.",
        "game.barricade_cleared": "Barricada despejada: {name} entregó {salvage} chatarra.",
        "game.salvage_collected": "Recolectado {name} obteniendo {amount} chatarra.",
        "game.weather_clear": "Cambio climático: las condiciones se normalizan.",
        "game.weather_change": "Cambio climático: {name} ({description}) movimiento {movement:+d}% visión {vision:+d}%",
        "game.upgrade_presented": "Mejoras disponibles.",
        "game.glyph_unlocked": "Definitiva desbloqueada para {family}!",
        "game.glyph_added": "Glifo añadido: {family}.",
        "game.weapon_upgraded": "Arma mejorada: {name} nivel {tier}.",
        "game.perk_acquired": "Ventaja obtenida: {name}.",
        "game.wave_incoming": "Oleada {number} con {count} enemigos.",
        "game.miniboss_incoming": "Minijefe {name} se aproxima!",
        "game.relic_acquired": "Reliquia obtenida: {name}.",
        "game.final_boss": "El jefe final {name} desciende para el último asalto.",
        "game.final_boss_generic": "Comienza la confrontación final.",
        "game.encounter_resolved": "{label} resuelto eliminando {count} enemigos en {duration:.1f}s.",
        "game.encounter_aftermath": "Balance de combate: -{damage} PS, +{healing} PS.",
        "game.player_fallen": "El cazador sucumbe al asedio.",
        "game.player_survived": "Amanece. El cazador sobrevive a la noche.",
        "systems.level_up": "¡Subes de nivel! Alcanzaste el nivel {level}.",
        "systems.ultimate_unlocked": "Definitiva desbloqueada para glifos {family}!",
        "ui.arcade_status": "Tiempo {time:5.1f}s  Fase {phase}  Nivel {level}  XP {xp}/{next_xp}  PS {hp}/{max_hp}  Puntuación {score}",
        "ui.upgrade_prompt": "Elige mejora [1-3]:",
        "ui.upgrade_option": "{index}. {name}",
        "ui.upgrade_selected": "Mejora elegida: {name}.",
        "ui.damage_taken": "Golpe de {enemy} por {damage} daño!",
        "ui.ultimate_ready": "Definitiva desatada, limpiando la horda!",
        "ui.run_failed": "DERROTA",
        "ui.run_survived": "AMANECER LOGRADO",
        "cli.description": "Prototipo jugable de Nightfall Survivors",
        "cli.help.duration": "Duración de la sesión en segundos",
        "cli.help.fps": "Objetivo de fotogramas por segundo",
        "cli.help.language": "Código de idioma para la interfaz",
        "cli.help.assist_radius": "Modificador de autoapuntado para proyectiles",
        "cli.help.damage_multiplier": "Multiplicador de daño recibido (menor para asistencia)",
        "cli.help.speed_scale": "Multiplicador de velocidad del juego (<1 lo desacelera)",
        "cli.help.projectile_speed": "Multiplicador de velocidad de proyectiles",
        "cli.help.high_contrast": "Activa representación de alto contraste",
        "cli.help.message_log": "Cantidad de mensajes visibles en pantalla",
        "cli.help.demo": "Aplicar restricciones de demo (contenido limitado)",
        "cli.help.event_id": "Activar un evento de temporada por identificador",
        "cli.help.event_year": "Año usado para evaluar el calendario estacional",
        "cli.help.profile_path": "Ruta a un perfil cifrado para cargar",
        "cli.help.key": "Clave de descifrado para el perfil proporcionado",
    }

    catalog.register_language("en", english_strings)
    catalog.register_language("es", spanish_strings, inherit_from="en")
    return catalog


_DEFAULT_CATALOG = _build_default_catalog()


def default_catalog() -> LocalizationCatalog:
    """Return the default project catalog."""

    return _DEFAULT_CATALOG


def get_translator(language: str = "en", fallback: str | None = None) -> Translator:
    """Fetch a translator for the requested language."""

    catalog = default_catalog()
    return catalog.translator(language, fallback=fallback)

