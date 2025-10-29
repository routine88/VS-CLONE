"""Core package for Nightfall Survivors prototype logic."""

from .analytics import (  # noqa: F401
    AggregateMetrics,
    RunMetrics,
    aggregate_metrics,
    derive_metrics,
    from_transcripts,
    kpi_snapshot,
    render_report,
)
from .challenges import (  # noqa: F401
    ChallengeConfig,
    build_config,
    decode_challenge,
    describe_challenge,
    encode_challenge,
)
from .distribution import (  # noqa: F401
    BuildTarget,
    DemoRestrictions,
    Platform,
    apply_demo_restrictions,
    configure_simulator_for_demo,
    default_build_matrix,
    default_demo_restrictions,
    demo_duration,
    validate_build_targets,
)
from .environment import EnvironmentDirector  # noqa: F401
from .game_state import GameState  # noqa: F401
from .live_ops import (  # noqa: F401
    SeasonalEvent,
    activate_event,
    active_event,
    find_event,
    seasonal_schedule,
)
from .meta import (  # noqa: F401
    MetaProgressionSystem,
    MetaRequirement,
    SigilLedger,
    Unlockable,
    default_unlocks,
)
from .profile import HunterDefinition, PlayerProfile, default_hunters  # noqa: F401
from .prototype import (  # noqa: F401
    PrototypeSession,
    PrototypeTranscript,
    format_transcript,
    save_transcript,
    simulator_default_duration,
    transcript_to_dict,
)
from .interactive import (  # noqa: F401
    ArcadeEngine,
    FrameSnapshot,
    InputFrame,
    launch_playable,
)
from .localization import (  # noqa: F401
    LocalizationCatalog,
    Translator,
    default_catalog,
    get_translator,
)
from .session import RunResult, RunSimulator, score_run  # noqa: F401
from .storage import decrypt_data, encrypt_data, load_profile, save_profile  # noqa: F401
