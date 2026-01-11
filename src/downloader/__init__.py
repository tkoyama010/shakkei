"""
データダウンロードモジュール

PLATEAUの建物データと国土地理院のDEMデータをダウンロードします。
"""

from .plateau import download_plateau
from .dem import download_dem

__all__ = ["download_plateau", "download_dem"]
