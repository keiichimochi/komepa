#!/usr/bin/env python3
"""
お米商品情報スクレイピングスクリプト
Gemini APIを使用してECサイトから商品情報を抽出し、Cloudflare D1に保存
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Product(BaseModel):
    """商品情報のモデル"""
    id: str
    name: str
    price: int
    product_url: str
    affiliate_url: Optional[str] = None
    image_url: Optional[str] = None
    site_name: str

class GeminiScraper:
    """Gemini APIを使用したスクレイパー"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def extract_products(self, url: str, site_name: str) -> List[Product]:
        """指定URLからお米商品情報を抽出"""
        prompt = f"""
        以下のECサイトのURLから、お米の商品情報を抽出してください。
        URL: {url}
        
        各商品について以下の情報をJSON形式で抽出してください：
        - name: 商品名（お米の銘柄、容量など）
        - price: 価格（数値のみ、円単位）
        - product_url: 商品詳細ページのURL
        - image_url: 商品画像のURL
        
        出力形式：
        {{
            "products": [
                {{
                    "name": "商品名",
                    "price": 価格（数値）,
                    "product_url": "URL",
                    "image_url": "画像URL"
                }}
            ]
        }}
        
        注意事項：
        - お米以外の商品は除外してください
        - 価格は税込み価格を抽出してください
        - URLは完全な形式（https://から始まる）で抽出してください
        """
        
        try:
            # 実際の実装では、ここでウェブページの内容を取得し、
            # Geminiに渡して解析する処理を行います
            response = self.model.generate_content(prompt)
            
            # レスポンスからJSON部分を抽出
            result_text = response.text
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                data = json.loads(json_str)
                
                products = []
                for item in data.get('products', []):
                    # 商品IDの生成
                    product_id = self._generate_product_id(site_name, item['product_url'])
                    
                    product = Product(
                        id=product_id,
                        name=item['name'],
                        price=item['price'],
                        product_url=item['product_url'],
                        image_url=item.get('image_url'),
                        site_name=site_name
                    )
                    products.append(product)
                
                return products
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting products from {url}: {str(e)}")
            return []
    
    def _generate_product_id(self, site_name: str, product_url: str) -> str:
        """商品IDを生成"""
        hash_input = f"{site_name}_{product_url}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

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
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def upsert_product(self, product: Product) -> bool:
        """商品情報をアップサート"""
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
            product.id,
            product.name,
            product.price,
            product.product_url,
            product.affiliate_url,
            product.image_url,
            product.site_name
        ]
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Error upserting product {product.id}: {str(e)}")
            return False

async def main():
    """メイン処理"""
    # 環境変数から設定を読み込み
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    cf_account_id = os.getenv("CF_ACCOUNT_ID")
    cf_database_id = os.getenv("CF_DATABASE_ID")
    cf_api_token = os.getenv("CF_API_TOKEN")
    
    if not all([gemini_api_key, cf_account_id, cf_database_id, cf_api_token]):
        logger.error("必要な環境変数が設定されていません")
        return
    
    # スクレイピング対象のサイト
    target_sites = [
        {
            "name": "楽天市場",
            "url": "https://search.rakuten.co.jp/search/mall/お米/"
        },
        {
            "name": "Amazon",
            "url": "https://www.amazon.co.jp/s?k=お米"
        }
    ]
    
    # クライアントの初期化
    scraper = GeminiScraper(gemini_api_key)
    d1_client = CloudflareD1Client(cf_account_id, cf_database_id, cf_api_token)
    
    # 各サイトから商品情報を取得
    for site in target_sites:
        logger.info(f"Scraping {site['name']}...")
        products = await scraper.extract_products(site['url'], site['name'])
        
        logger.info(f"Found {len(products)} products from {site['name']}")
        
        # D1に保存
        success_count = 0
        for product in products:
            if d1_client.upsert_product(product):
                success_count += 1
        
        logger.info(f"Saved {success_count}/{len(products)} products from {site['name']}")
    
    logger.info("Scraping completed")

if __name__ == "__main__":
    asyncio.run(main())