"""
可視化モジュールのCLIエントリーポイント.

使用方法:
    python -m src.visualizer
"""

import argparse
import logging

logger = logging.getLogger(__name__)


def main() -> None:
    """メインエントリーポイント."""
    parser = argparse.ArgumentParser(
        prog="python -m src.visualizer",
        description="3D可視化の実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-b", "--buildings", help="建物データのパス")
    parser.add_argument("-t", "--terrain", help="地形データのパス")
    parser.add_argument(
        "--fog",
        choices=["clear", "hazy", "cloudy"],
        default="clear",
        help="フォグプリセット",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細な出力")

    args = parser.parse_args()

    # ログレベルの設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("可視化モジュールを実行")
    logger.info(f"建物データ: {args.buildings}")
    logger.info(f"地形データ: {args.terrain}")
    logger.info(f"フォグ: {args.fog}")
    logger.warning("[スタブ] 3D可視化は未実装です")


if __name__ == "__main__":
    main()
