"""Accessibility utilities for the Nightfall Survivors prototype."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessibilitySettings:
    """Collection of knobs that make the prototype more approachable."""

    auto_aim_radius: float = 0.8
    damage_taken_multiplier: float = 1.0
    game_speed_multiplier: float = 1.0
    projectile_speed_multiplier: float = 1.0
    high_contrast: bool = False
    message_log_size: int = 8

    def normalized(self) -> "AccessibilitySettings":
        """Clamp all numeric values so they stay within expected ranges."""

        radius = min(max(self.auto_aim_radius, 0.25), 3.0)
        damage = min(max(self.damage_taken_multiplier, 0.1), 2.0)
        speed = min(max(self.game_speed_multiplier, 0.25), 1.5)
        projectile_speed = min(max(self.projectile_speed_multiplier, 0.25), 3.0)
        log_size = max(1, min(self.message_log_size, 20))
        if (
            radius == self.auto_aim_radius
            and damage == self.damage_taken_multiplier
            and speed == self.game_speed_multiplier
            and projectile_speed == self.projectile_speed_multiplier
            and log_size == self.message_log_size
        ):
            return self
        return AccessibilitySettings(
            auto_aim_radius=radius,
            damage_taken_multiplier=damage,
            game_speed_multiplier=speed,
            projectile_speed_multiplier=projectile_speed,
            high_contrast=self.high_contrast,
            message_log_size=log_size,
        )
