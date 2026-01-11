"""
ダウンローダーモジュールのCLIエントリーポイント

使用方法:
    python -m src.downloader
"""

import argparse
import logging


logger = logging.getLogger(__name__)


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        prog="python -m src.downloader",
        description="PLATEAUとDEMデータをダウンロード",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-o", "--output",
        default="data/plateau/ochanomizu",
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

    logger.info("ダウンローダーモジュールを実行")
    logger.info(f"出力先: {args.output}")
    logger.warning("[スタブ] PLATEAUデータのダウンロードは未実装です")


if __name__ == "__main__":
    main()
