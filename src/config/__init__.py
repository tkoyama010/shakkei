"""
設定モジュール

座標定義とレンダリング設定を管理します。
"""

from .locations import SOLACITY, FUJI, TSUKUBA
from .rendering import FOG_PRESETS, CAMERA_SETTINGS

__all__ = ["SOLACITY", "FUJI", "TSUKUBA", "FOG_PRESETS", "CAMERA_SETTINGS"]
