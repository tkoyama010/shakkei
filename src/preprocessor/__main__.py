"""
前処理モジュールのCLIエントリーポイント

使用方法:
    python -m src.preprocessor
"""

import argparse
import logging


logger = logging.getLogger(__name__)


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        prog="python -m src.preprocessor",
        description="データの前処理（座標変換、メッシュ変換など）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="入力データディレクトリ"
    )
    parser.add_argument(
        "-o", "--output",
        default="data/processed",
        help="出力ディレクトリ"
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

    logger.info("前処理モジュールを実行")
    logger.info(f"入力: {args.input}")
    logger.info(f"出力: {args.output}")
    logger.warning("[スタブ] データ前処理は未実装です")


if __name__ == "__main__":
    main()
