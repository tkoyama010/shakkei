"""
設定モジュールのCLIエントリーポイント

使用方法:
    python -m src.config
"""

import argparse
import logging


logger = logging.getLogger(__name__)


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        prog="python -m src.config",
        description="設定情報の表示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--show-locations",
        action="store_true",
        help="登録済み地点の座標を表示"
    )
    parser.add_argument(
        "--show-fog-presets",
        action="store_true",
        help="フォグプリセットを表示"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細な出力"
    )

    args = parser.parse_args()

    # ログレベルの設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("設定モジュール")

    if args.show_locations:
        logger.info("\n=== 登録済み地点 ===")
        logger.info("御茶ノ水ソラシティ: (緯度: 35.6996, 経度: 139.7645, 標高: 70m)")
        logger.info("富士山: (緯度: 35.3606, 経度: 138.7274, 標高: 3776m)")
        logger.info("筑波山: (緯度: 36.2256, 経度: 140.1064, 標高: 877m)")

    if args.show_fog_presets:
        logger.info("\n=== フォグプリセット ===")
        logger.info("clear (晴天): density=0.000015")
        logger.info("hazy (霞): density=0.000025")
        logger.info("cloudy (曇天): density=0.000040")

    if not args.show_locations and not args.show_fog_presets:
        logger.warning("[スタブ] 設定情報は未実装です")
        logger.info("オプションを指定してください: --show-locations, --show-fog-presets")


if __name__ == "__main__":
    main()
