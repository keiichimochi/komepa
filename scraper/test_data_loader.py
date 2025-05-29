#!/usr/bin/env python3
"""
テスト用のお米商品データをD1に登録するスクリプト
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict
import hashlib
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class CloudflareD1Client:
    """Cloudflare D1クライアント"""
    
    def __init__(self, account_id: str, database_id: str, api_token: str):
        self.account_id = account_id
        self.database_id = database_id
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def execute_query(self, query: str, params: List = None) -> Dict:
        """D1データベースにクエリを実行"""
        url = f"{self.base_url}/query"
        
        payload = {
            "sql": query,
            "params": params or []
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error executing query: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise

def generate_product_id(site_name: str, product_url: str) -> str:
    """商品IDを生成"""
    hash_input = f"{site_name}_{product_url}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]

def main():
    """テストデータを登録"""
    # 環境変数から設定を読み込み
    cf_account_id = os.getenv("CF_ACCOUNT_ID")
    cf_database_id = os.getenv("CF_DATABASE_ID")
    cf_api_token = os.getenv("CF_API_TOKEN")
    
    if not all([cf_account_id, cf_database_id, cf_api_token]):
        print("必要な環境変数が設定されていません")
        return
    
    # D1クライアントの初期化
    d1_client = CloudflareD1Client(cf_account_id, cf_database_id, cf_api_token)
    
    # テスト用のお米商品データ
    test_products = [
        {
            "name": "新潟県産コシヒカリ 5kg",
            "price": 2980,
            "product_url": "https://example-shop1.com/koshihikari-5kg",
            "affiliate_url": "https://affiliate.example.com/track?id=1234",
            "image_url": "https://placehold.co/300x300/e8f4f8/2c3e50?text=コシヒカリ+5kg",
            "site_name": "楽天市場"
        },
        {
            "name": "秋田県産あきたこまち 10kg",
            "price": 4580,
            "product_url": "https://example-shop2.com/akitakomachi-10kg",
            "affiliate_url": "https://affiliate.example.com/track?id=5678",
            "image_url": "https://placehold.co/300x300/f8e8e8/2c3e50?text=あきたこまち+10kg",
            "site_name": "Amazon"
        },
        {
            "name": "北海道産ゆめぴりか 5kg",
            "price": 3480,
            "product_url": "https://example-shop3.com/yumepirika-5kg",
            "affiliate_url": "https://affiliate.example.com/track?id=9012",
            "image_url": "https://placehold.co/300x300/e8e8f8/2c3e50?text=ゆめぴりか+5kg",
            "site_name": "楽天市場"
        },
        {
            "name": "山形県産つや姫 5kg",
            "price": 3280,
            "product_url": "https://example-shop4.com/tsuyahime-5kg",
            "affiliate_url": "https://affiliate.example.com/track?id=3456",
            "image_url": "https://placehold.co/300x300/f8f4e8/2c3e50?text=つや姫+5kg",
            "site_name": "Amazon"
        },
        {
            "name": "宮城県産ひとめぼれ 10kg",
            "price": 4280,
            "product_url": "https://example-shop5.com/hitomebore-10kg",
            "affiliate_url": "https://affiliate.example.com/track?id=7890",
            "image_url": "https://placehold.co/300x300/e8f8e8/2c3e50?text=ひとめぼれ+10kg",
            "site_name": "楽天市場"
        },
        {
            "name": "福岡県産夢つくし 5kg お買い得品",
            "price": 2480,
            "product_url": "https://example-shop6.com/yumetsukushi-5kg",
            "affiliate_url": "https://affiliate.example.com/track?id=2468",
            "image_url": "https://placehold.co/300x300/f4f8e8/2c3e50?text=夢つくし+5kg",
            "site_name": "Amazon"
        }
    ]
    
    # 各商品をD1に登録
    success_count = 0
    for product in test_products:
        # 商品IDの生成
        product_id = generate_product_id(product["site_name"], product["product_url"])
        
        # INSERT文の実行
        query = """
        INSERT INTO products (
            id, name, price, product_url, affiliate_url, 
            image_url, site_name, last_scraped_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            price = excluded.price,
            affiliate_url = excluded.affiliate_url,
            image_url = excluded.image_url,
            last_scraped_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = [
            product_id,
            product["name"],
            product["price"],
            product["product_url"],
            product["affiliate_url"],
            product["image_url"],
            product["site_name"]
        ]
        
        try:
            result = d1_client.execute_query(query, params)
            print(f"✅ 登録成功: {product['name']} - ¥{product['price']:,}")
            success_count += 1
        except Exception as e:
            print(f"❌ 登録失敗: {product['name']} - エラー: {str(e)}")
    
    print(f"\n合計: {success_count}/{len(test_products)} 件の商品を登録しました")
    
    # 登録データの確認
    try:
        result = d1_client.execute_query("SELECT COUNT(*) as count FROM products")
        count = result['result'][0]['results'][0]['count']
        print(f"現在のデータベース内の商品数: {count} 件")
    except Exception as e:
        print(f"データ数の確認に失敗: {str(e)}")

if __name__ == "__main__":
    main()