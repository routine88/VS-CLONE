"""Core package for Nightfall Survivors prototype logic."""

from .accessibility import AccessibilitySettings  # noqa: F401
from .analytics import (  # noqa: F401
    AggregateMetrics,
    RunMetrics,
    aggregate_metrics,
    derive_metrics,
    from_transcripts,
    kpi_snapshot,
    render_report,
)
from .audio import (  # noqa: F401
    AudioEngine,
    AudioFrame,
    MusicInstruction,
    MusicTrack,
    SoundClip,
    SoundInstruction,
)
from .export import UnityFrameExporter  # noqa: F401
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
from .cloud import CloudSlot, CloudSync, run_cli as cloud_cli  # noqa: F401
from .environment import EnvironmentDirector  # noqa: F401
from .graphics import (  # noqa: F401
    AnimationClip,
    AnimationFrame,
    Camera,
    GraphicsEngine,
    LayerSettings,
    RenderFrame,
    RenderInstruction,
    SceneNode,
    Sprite,
)
from .mvp import (  # noqa: F401
    EnemyArchetype,
    MvpConfig,
    MvpEnemySnapshot,
    MvpFrameSnapshot,
    MvpReport,
    run_mvp_simulation,
    run_mvp_with_snapshots,
)
from .mvp_graphics import (  # noqa: F401
    MvpVisualizationResult,
    MvpVisualSettings,
    MvpVisualizer,
)
from .mvp_viewer import (  # noqa: F401
    CanvasDrawable,
    CanvasTranslator,
    MvpViewerApp,
    run_viewer,
)
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
    RequirementStatus,
    SigilLedger,
    UnlockTelemetry,
    Unlockable,
    default_unlocks,
)
from .monetization import (  # noqa: F401
    CosmeticInventory,
    CosmeticItem,
    CurrencyWallet,
    DlcPack,
    Storefront,
    default_cosmetics,
    default_dlc_packs,
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
from .entities import EnemyLane  # noqa: F401
from .session import RunResult, RunSimulator, score_run  # noqa: F401
from .storage import decrypt_data, encrypt_data, load_profile, save_profile  # noqa: F401
