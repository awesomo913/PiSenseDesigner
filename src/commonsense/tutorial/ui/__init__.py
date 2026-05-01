"""UI layer for the tutorial — Phase 2.

Public surface:
    TutorialController   wires TutorialRunner callbacks to all the UI bits
    WidgetRegistry       named widget lookup (editor registers; UI resolves)
    THEME                bright kid-friendly tutorial colors

Implementation pieces (importable but rarely needed directly):
    Spotlight            4-toplevel dim around target rectangle
    SpeechBubble         floating speech bubble next to spotlight
    SparkyMascot         8x8 pixel-art animated character
    TargetPulse          pulsing yellow ring around target widget
    Confetti             burst of falling pixel rectangles on a step complete
"""
from .controller import TutorialController
from .registry import WidgetRegistry
from .theme import THEME

__all__ = ["THEME", "TutorialController", "WidgetRegistry"]
