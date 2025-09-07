import requests
import json
import time
import csv
import argparse
import sys
from typing import List, Dict, Optional
from datetime import datetime
from settings import NOTION_TOKEN, DEFAULT_JSON_OUTPUT, DEFAULT_CSV_OUTPUT

class NotionPublicPageScanner:
    def __init__(self, notion_token: str):
        """
        Notion 公開ページスキャナーの初期化
        
        Args:
            notion_token: Notion Integration Token
        """
        self.token = notion_token
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.notion.com/v1"
        
    def search_all_pages(self) -> List[Dict]:
        """全ページの検索"""
        all_pages = []
        start_cursor = None
        
        while True:
            url = f"{self.base_url}/search"
            payload = {
                "filter": {"property": "object", "value": "page"},
                "page_size": 100
            }
            
            if start_cursor:
                payload["start_cursor"] = start_cursor
                
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"ページ検索エラー: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            all_pages.extend(data.get("results", []))
            
            if not data.get("has_more", False):
                break
                
            start_cursor = data.get("next_cursor")
            time.sleep(0.1)  # API制限の回避
            
        return all_pages
    
    def get_page_details(self, page_id: str) -> Optional[Dict]:
        """ページ詳細情報の取得"""
        url = f"{self.base_url}/pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"ページ {page_id} の取得エラー: {response.status_code}")
            return None
    
    def check_page_sharing(self, page_data: Dict) -> Dict:
        """
        ページの公開設定確認
        
        注意: Notion APIでは直接的な公開設定を確認できないため、
        間接的な指標により判断します。
        """
        page_id = page_data.get("id", "")
        title = self.extract_title(page_data)
        
        # 公開状況を確認する方法
        sharing_info = {
            "page_id": page_id,
            "title": title,
            "url": page_data.get("url", ""),
            "created_time": page_data.get("created_time", ""),
            "last_edited_time": page_data.get("last_edited_time", ""),
            "created_by": page_data.get("created_by", {}).get("id", ""),
            "parent_type": page_data.get("parent", {}).get("type", ""),
            "archived": page_data.get("archived", False),
            "public_indicators": []
        }
        
        # 公開可能性の指標チェック
        if page_data.get("public_url"):
            sharing_info["public_indicators"].append("公開URLあり")
            
        # URLパターンによる公開状況の推定
        notion_url = page_data.get("url", "")
        if notion_url and not any(x in notion_url for x in ["private", "workspace"]):
            sharing_info["public_indicators"].append("URLパターンが公開を示唆")
            
        return sharing_info
    
    def extract_title(self, page_data: Dict) -> str:
        """ページタイトルの抽出"""
        properties = page_data.get("properties", {})
        
        # Title属性を検索
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return "".join([t.get("plain_text", "") for t in title_array])
        
        return "無題"
    
    def test_public_access(self, page_url: str) -> bool:
        """
        ページの公開アクセス可能性テスト
        （認証なしでアクセス試行）
        
        注意: この方法は実際の公開状況を100%保証しません。
        """
        try:
            # 認証ヘッダーなしでリクエスト
            response = requests.get(page_url, timeout=10)
            
            # 200レスポンスかつログインページにリダイレクトされない場合
            if response.status_code == 200:
                content = response.text.lower()
                if "sign in" not in content and "login" not in content:
                    return True
                    
        except Exception as e:
            print(f"{page_url} の公開アクセステストエラー: {e}")
            
        return False
    
    def generate_security_report(self, pages_info: List[Dict]) -> Dict:
        """セキュリティ脆弱性レポートの生成"""
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_pages_scanned": len(pages_info),
            "potential_public_pages": [],
            "security_recommendations": [],
            "risk_summary": {
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0
            }
        }
        
        for page_info in pages_info:
            risk_level = "low"
            
            # リスクレベル評価
            if page_info["public_indicators"]:
                if len(page_info["public_indicators"]) > 1:
                    risk_level = "high"
                else:
                    risk_level = "medium"
                    
                report["potential_public_pages"].append({
                    **page_info,
                    "risk_level": risk_level
                })
                
                report["risk_summary"][f"{risk_level}_risk"] += 1
        
        # セキュリティ推奨事項
        if report["risk_summary"]["high_risk"] > 0:
            report["security_recommendations"].append(
                "【最優先】高リスクページの公開設定を直ちに確認してください。"
            )
        
        if report["risk_summary"]["medium_risk"] > 0:
            report["security_recommendations"].append(
                "【中優先】疑いのあるページのアクセス権限を確認してください。"
            )
            
        report["security_recommendations"].extend([
            "定期的にページの公開設定を監査してください。",
            "機密情報を含むページは特に注意深く管理してください。",
            "チームメンバーにページ公開設定について教育を実施してください。",
            "公開ページの一覧を定期的にレビューし、不要な公開を停止してください。",
            "重要なページには適切なアクセス制御を設定してください。"
        ])
        
        return report
    
    def save_to_csv(self, report: Dict, csv_file: str):
        """スキャン結果をCSVファイルに保存"""
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # ヘッダー行
            writer.writerow(['ページタイトル', 'URL', 'リスクレベル', '公開指標', '最終編集日時'])
            
            # データ行
            for page in report['potential_public_pages']:
                writer.writerow([
                    page['title'],
                    page['url'],
                    page['risk_level'],
                    ', '.join(page['public_indicators']),
                    page['last_edited_time']
                ])

    def scan_and_report(self, output_file: str = DEFAULT_JSON_OUTPUT, csv_file: str = DEFAULT_CSV_OUTPUT):
        """全体スキャン実行とレポート生成"""
        print("🔍 Notionページスキャン開始...")
        
        # 全ページの検索
        all_pages = self.search_all_pages()
        print(f"📄 合計 {len(all_pages)} 個のページを発見しました。")
        
        # 各ページの公開設定確認
        pages_info = []
        for i, page in enumerate(all_pages, 1):
            print(f"🔍 ページ分析中... ({i}/{len(all_pages)})", end="\r")
            
            page_details = self.get_page_details(page["id"])
            if page_details:
                sharing_info = self.check_page_sharing(page_details)
                pages_info.append(sharing_info)
                
            time.sleep(0.1)  # API制限の回避
        
        print(f"\n✅ ページ分析完了！")
        
        # セキュリティレポート生成
        security_report = self.generate_security_report(pages_info)
        
        # 結果保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(security_report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 セキュリティスキャン結果が {output_file} に保存されました。")

        # CSV出力
        if csv_file:
            self.save_to_csv(security_report, csv_file)
            print(f"📊 CSVレポートが {csv_file} に保存されました。")
        
        # 概要出力
        self.print_summary(security_report)
        
        return security_report
    
    def print_summary(self, report: Dict):
        """スキャン結果概要の出力"""
        print("\n" + "="*60)
        print("🛡️  NOTION セキュリティスキャン結果概要")
        print("="*60)
        print(f"📅 スキャン日時: {report['scan_timestamp']}")
        print(f"📄 総ページ数: {report['total_pages_scanned']}")
        print(f"⚠️  疑いページ数: {len(report['potential_public_pages'])}")
        print()
        print("🚨 リスク分布:")
        print(f"   - 高リスク: {report['risk_summary']['high_risk']} ページ")
        print(f"   - 中リスク: {report['risk_summary']['medium_risk']} ページ")
        print(f"   - 低リスク: {report['risk_summary']['low_risk']} ページ")
        
        if report['potential_public_pages']:
            print("\n🔍 疑いページ一覧（上位5件）:")
            for page in report['potential_public_pages'][:5]:
                risk_level_ja = {
                    "high": "高",
                    "medium": "中", 
                    "low": "低"
                }.get(page['risk_level'], page['risk_level'])
                
                print(f"   - {page['title']} (リスクレベル: {risk_level_ja})")
                print(f"     URL: {page['url']}")
                if page['public_indicators']:
                    print(f"     指標: {', '.join(page['public_indicators'])}")
        
        print("\n📋 セキュリティ推奨事項:")
        for i, recommendation in enumerate(report['security_recommendations'], 1):
            print(f"   {i}. {recommendation}")
        
        # 追加の警告メッセージ
        if report['risk_summary']['high_risk'] > 0:
            print("\n🚨 【緊急注意】")
            print("   高リスクページが検出されました。")
            print("   これらのページには機密情報が含まれている可能性があります。")
            print("   直ちに公開設定を確認し、必要に応じて非公開に設定してください。")
        
        print("="*60)


def setup_parser():
    """コマンドライン引数の設定"""
    parser = argparse.ArgumentParser(
        description='Notionの公開ページをスキャンしてセキュリティレポートを生成します',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 必須のオプショングループを作成
    required = parser.add_argument_group('必須オプション')
    required.add_argument(
        '-f', '--format',
        choices=['json', 'csv', 'both'],
        help='出力形式を指定:\n'
             'json: JSONファイルのみ出力\n'
             'csv: CSVファイルのみ出力\n'
             'both: 両方のファイル形式で出力',
        required=True
    )
    
    # 出力ファイル名を指定
    parser.add_argument(
        '-o', '--output',
        default=DEFAULT_JSON_OUTPUT,
        help='出力ファイル名 (拡張子含む)\n'
             '例: -o report.json または -o result.csv'
    )
    
    return parser

def main():
    """メイン実行関数"""
    parser = setup_parser()
    
    # 引数がない場合はヘルプを表示して終了
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    if NOTION_TOKEN == "your_notion_integration_token_here":
        print("❌ Notion Integration Tokenを設定してください！")
        print("設定手順:")
        print("1. https://www.notion.so/my-integrations で新しいIntegrationを作成")
        print("2. Tokenをコピーしてこのスクリプトの NOTION_TOKEN 変数に設定")
        print("3. Integrationにワークスペースへのアクセス権限を付与")
        print("4. 必要に応じてページレベルでの権限も設定")
        return
    
    scanner = NotionPublicPageScanner(NOTION_TOKEN)
    
    try:
        print("🔐 Notionセキュリティスキャナーを開始します...")
        print("このツールは潜在的な公開ページを検出し、セキュリティリスクを評価します。")
        print(f"出力形式: {args.format.upper()}")
        print(f"出力ファイル: {args.output}")
        print()
        
        # 出力ファイルの設定
        if args.format == 'json':
            report = scanner.scan_and_report(output_file=args.output, csv_file=None)
        elif args.format == 'csv':
            report = scanner.scan_and_report(output_file=None, csv_file=args.output)
        else:  # both
            report = scanner.scan_and_report(
                output_file=args.output,
                csv_file=args.output.rsplit('.', 1)[0] + '.csv'
            )
        
        # 高リスクページ発見時の追加警告
        if report['risk_summary']['high_risk'] > 0:
            print("\n🚨 【重要な警告】")
            print("高リスクページが発見されました！")
            print("以下の対応を直ちに実施してください:")
            print("1. 該当ページの公開設定を確認")
            print("2. 機密情報が含まれていないかチェック")
            print("3. 必要に応じて非公開に変更")
            print("4. 関係者への通知と対応報告")
            
        # 出力ファイルの案内
        if args.format in ['json', 'both']:
            print(f"\n📄 JSONレポート: '{args.output}'")
        if args.format in ['csv', 'both']:
            csv_file = args.output if args.format == 'csv' else args.output.rsplit('.', 1)[0] + '.csv'
            print(f"📄 CSVレポート: '{csv_file}'")
            
    except Exception as e:
        print(f"❌ スキャン中にエラーが発生しました: {e}")
        print("以下の点を確認してください:")
        print("- Notion Tokenが正しく設定されているか")
        print("- インターネット接続が安定しているか") 
        print("- Notionワークスペースへのアクセス権限があるか")


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()

