"""
データダウンロードモジュール.

PLATEAUの建物データと国土地理院のDEMデータをダウンロードします。
"""

from .dem import download_dem
from .plateau import download_plateau

__all__ = ["download_dem", "download_plateau"]
