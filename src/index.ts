import { Hono } from 'hono';
import { html } from 'hono/html';

interface Env {
  DB: D1Database;
  R2: R2Bucket;
}

interface Product {
  id: string;
  name: string;
  price: number;
  product_url: string;
  affiliate_url: string;
  image_url: string;
  site_name: string;
  last_scraped_at: string;
  created_at: string;
  updated_at: string;
}

const app = new Hono<{ Bindings: Env }>();

// ルートページ - 商品一覧
app.get('/', async (c) => {
  const { sort = 'price_asc', page = '1', limit = '20' } = c.req.query();
  
  const pageNum = parseInt(page);
  const limitNum = parseInt(limit);
  const offset = (pageNum - 1) * limitNum;

  // ソート条件の設定
  let orderBy = 'price ASC';
  switch (sort) {
    case 'price_desc':
      orderBy = 'price DESC';
      break;
    case 'updated_desc':
      orderBy = 'updated_at DESC';
      break;
    case 'price_asc':
    default:
      orderBy = 'price ASC';
  }

  try {
    // 総商品数を取得
    const countResult = await c.env.DB.prepare('SELECT COUNT(*) as total FROM products').first<{ total: number }>();
    const totalProducts = countResult?.total || 0;
    const totalPages = Math.ceil(totalProducts / limitNum);

    // 商品データを取得
    const products = await c.env.DB.prepare(
      `SELECT * FROM products ORDER BY ${orderBy} LIMIT ? OFFSET ?`
    )
      .bind(limitNum, offset)
      .all<Product>();

    // HTMLを生成
    const htmlContent = renderProductList(products.results || [], {
      currentPage: pageNum,
      totalPages,
      totalProducts,
      sort,
      limit: limitNum
    });

    return c.html(htmlContent);
  } catch (error) {
    console.error('Error fetching products:', error);
    return c.html(renderError('商品データの取得中にエラーが発生しました。'));
  }
});

// 商品一覧のHTMLをレンダリング
function renderProductList(
  products: Product[],
  pagination: {
    currentPage: number;
    totalPages: number;
    totalProducts: number;
    sort: string;
    limit: number;
  }
) {
  return html`
    <!DOCTYPE html>
    <html lang="ja">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>お米価格比較 - KomePa</title>
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }

          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
          }

          .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
          }

          .header {
            background-color: #fff;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }

          .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
          }

          .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
          }

          .sort-select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #fff;
            cursor: pointer;
          }

          .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
          }

          .product-card {
            background-color: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
          }

          .product-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          }

          .product-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            background-color: #f0f0f0;
          }

          .product-info {
            padding: 15px;
          }

          .product-name {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
            line-height: 1.4;
            height: 2.8em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
          }

          .product-price {
            font-size: 20px;
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 8px;
          }

          .product-site {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 12px;
          }

          .buy-button {
            display: block;
            width: 100%;
            padding: 10px;
            background-color: #3498db;
            color: #fff;
            text-align: center;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            transition: background-color 0.2s;
          }

          .buy-button:hover {
            background-color: #2980b9;
          }

          .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 30px;
          }

          .pagination a,
          .pagination span {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-decoration: none;
            color: #333;
            background-color: #fff;
          }

          .pagination a:hover {
            background-color: #f0f0f0;
          }

          .pagination .current {
            background-color: #3498db;
            color: #fff;
            border-color: #3498db;
          }

          .pagination .disabled {
            color: #999;
            cursor: not-allowed;
          }

          .no-products {
            text-align: center;
            padding: 60px 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }

          .no-products h2 {
            color: #7f8c8d;
            margin-bottom: 10px;
          }

          @media (max-width: 768px) {
            .controls {
              flex-direction: column;
              align-items: stretch;
            }

            .products-grid {
              grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
              gap: 15px;
            }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🌾 お米価格比較 - KomePa</h1>
            <p>複数のECサイトからお米の価格を比較できます</p>
          </div>

          ${products.length > 0 ? html`
            <div class="controls">
              <div>
                <span>全${pagination.totalProducts}件中 ${(pagination.currentPage - 1) * pagination.limit + 1}-${Math.min(pagination.currentPage * pagination.limit, pagination.totalProducts)}件を表示</span>
              </div>
              <select class="sort-select" onchange="changeSort(this.value)">
                <option value="price_asc" ${pagination.sort === 'price_asc' ? 'selected' : ''}>価格が安い順</option>
                <option value="price_desc" ${pagination.sort === 'price_desc' ? 'selected' : ''}>価格が高い順</option>
                <option value="updated_desc" ${pagination.sort === 'updated_desc' ? 'selected' : ''}>更新日が新しい順</option>
              </select>
            </div>

            <div class="products-grid">
              ${products.map(product => html`
                <div class="product-card">
                  ${product.image_url ? html`
                    <img src="${product.image_url}" alt="${product.name}" class="product-image" onerror="this.style.display='none'">
                  ` : ''}
                  <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-price">¥${product.price.toLocaleString()}</div>
                    <div class="product-site">${product.site_name}</div>
                    <a href="${product.affiliate_url || product.product_url}" target="_blank" rel="noopener noreferrer" class="buy-button">
                      詳細を見る
                    </a>
                  </div>
                </div>
              `)}
            </div>

            ${pagination.totalPages > 1 ? html`
              <div class="pagination">
                ${pagination.currentPage > 1 ? html`
                  <a href="?page=${pagination.currentPage - 1}&sort=${pagination.sort}">前へ</a>
                ` : html`
                  <span class="disabled">前へ</span>
                `}

                ${Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                  let pageNum;
                  if (pagination.totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (pagination.currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (pagination.currentPage >= pagination.totalPages - 2) {
                    pageNum = pagination.totalPages - 4 + i;
                  } else {
                    pageNum = pagination.currentPage - 2 + i;
                  }

                  if (pageNum === pagination.currentPage) {
                    return html`<span class="current">${pageNum}</span>`;
                  } else {
                    return html`<a href="?page=${pageNum}&sort=${pagination.sort}">${pageNum}</a>`;
                  }
                })}

                ${pagination.currentPage < pagination.totalPages ? html`
                  <a href="?page=${pagination.currentPage + 1}&sort=${pagination.sort}">次へ</a>
                ` : html`
                  <span class="disabled">次へ</span>
                `}
              </div>
            ` : ''}
          ` : html`
            <div class="no-products">
              <h2>商品が見つかりませんでした</h2>
              <p>データベースに商品情報がありません。</p>
            </div>
          `}
        </div>

        <script>
          function changeSort(value) {
            window.location.href = '?sort=' + value + '&page=1';
          }
        </script>
      </body>
    </html>
  `;
}

// エラー表示用のHTML
function renderError(message: string) {
  return html`
    <!DOCTYPE html>
    <html lang="ja">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>エラー - KomePa</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
          }
          .error-container {
            background-color: #fff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
          }
          .error-container h1 {
            color: #e74c3c;
            margin-bottom: 20px;
          }
          .error-container p {
            color: #7f8c8d;
            margin-bottom: 20px;
          }
          .back-link {
            color: #3498db;
            text-decoration: none;
          }
          .back-link:hover {
            text-decoration: underline;
          }
        </style>
      </head>
      <body>
        <div class="error-container">
          <h1>エラーが発生しました</h1>
          <p>${message}</p>
          <a href="/" class="back-link">トップページに戻る</a>
        </div>
      </body>
    </html>
  `;
}

export default app;