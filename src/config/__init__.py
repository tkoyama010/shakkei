"""
設定モジュール.

座標定義とレンダリング設定を管理します。
"""

from .locations import FUJI, SOLACITY, TSUKUBA
from .rendering import CAMERA_SETTINGS, FOG_PRESETS

__all__ = ["CAMERA_SETTINGS", "FOG_PRESETS", "FUJI", "SOLACITY", "TSUKUBA"]
