"""
Swagger UI 中文配置
"""

# Swagger UI 中文翻译
SWAGGER_UI_PARAMETERS = {
    "docExpansion": "none",  # 默认折叠所有端点
    "defaultModelsExpandDepth": 1,  # 模型展开深度
    "displayRequestDuration": True,  # 显示请求持续时间
    "filter": True,  # 启用过滤器
    "showExtensions": True,  # 显示扩展
    "showCommonExtensions": True,  # 显示通用扩展
    "tryItOutEnabled": True,  # 启用"试一试"功能
    "syntaxHighlight.theme": "monokai",  # 语法高亮主题
    "persistAuthorization": True,  # 持久化授权
}

# 自定义 CSS 用于汉化 Swagger UI
CUSTOM_CSS = """
<style>
/* 汉化 Swagger UI 按钮和标签 */
.swagger-ui .btn.authorize:after { content: " 授权"; }
.swagger-ui .btn.authorize svg { display: none; }
.swagger-ui .btn.authorize span { display: none; }
.swagger-ui .btn.authorize:before { content: "🔐"; }

.swagger-ui .btn.execute:after { content: " 执行"; }
.swagger-ui .btn.execute { font-size: 14px; }

.swagger-ui .btn.btn-clear:after { content: " 清除"; }

.swagger-ui .btn.cancel:after { content: " 取消"; }

.swagger-ui .opblock-summary-method { font-weight: bold; }

.swagger-ui .tab-header .tablinks:after { content: ""; }
.swagger-ui .tab-header .tablinks { font-size: 16px; }

/* 请求和响应标签 */
.swagger-ui .opblock .opblock-section-header h4 span:after { content: ""; }
.swagger-ui .opblock .opblock-section-header h4 { font-size: 16px; }

/* 模型标签 */
.swagger-ui .model-box-control .model-toggle::after { content: " 模型"; }

/* 参数标签 */
.swagger-ui table thead tr th:first-child:after { content: ""; }
.swagger-ui table thead tr th { font-size: 14px; }

/* 响应标签 */
.swagger-ui .responses-inner h4:after { content: ""; }
.swagger-ui .responses-inner h5:after { content: ""; }

/* 尝试执行按钮 */
.swagger-ui .try-out__btn:after { content: " 试一试"; }
.swagger-ui .try-out__btn { padding: 5px 20px; }

/* 授权按钮 */
.swagger-ui .auth-wrapper .authorize:after { content: " 授权"; }
.swagger-ui .auth-wrapper .btn-done:after { content: " 完成"; }

/* 示例值/模型切换 */
.swagger-ui .model-example .tab-header .tablinks[data-name="example"]:after { content: " 示例值"; }
.swagger-ui .model-example .tab-header .tablinks[data-name="model"]:after { content: " 模型"; }
</style>
"""

# 自定义 JavaScript 用于更深度的汉化
CUSTOM_JS = """
<script>
// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 定时器确保 Swagger UI 完全加载
    setTimeout(function() {
        // 汉化文本替换映射
        const translations = {
            'Responses': '响应',
            'Response body': '响应体',
            'Response headers': '响应头',
            'Request body': '请求体',
            'Parameters': '参数',
            'Try it out': '试一试',
            'Execute': '执行',
            'Clear': '清除',
            'Cancel': '取消',
            'Authorize': '授权',
            'Close': '关闭',
            'Available authorizations': '可用授权',
            'Authorized': '已授权',
            'Authorization': '授权',
            'Value': '值',
            'Name': '名称',
            'Description': '描述',
            'Type': '类型',
            'Required': '必需',
            'Schema': '架构',
            'Example Value': '示例值',
            'Model': '模型',
            'Models': '模型',
            'Download': '下载',
            'Servers': '服务器',
            'Server variables': '服务器变量',
            'No parameters': '无参数',
            'Loading...': '加载中...',
            'Failed to fetch': '获取失败',
            'Possible Reasons': '可能的原因',
            'Fetch error': '获取错误',
            'NetworkError when attempting to fetch resource.': '尝试获取资源时出现网络错误。',
            'No response': '无响应',
            'Media type': '媒体类型',
            'Example value': '示例值',
            'No example available': '无可用示例',
            'Parameter content type': '参数内容类型',
            'Response content type': '响应内容类型',
        };
        
        // 递归替换文本节点
        function replaceText(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                let text = node.textContent;
                for (const [en, zh] of Object.entries(translations)) {
                    if (text.includes(en)) {
                        node.textContent = text.replace(new RegExp(en, 'g'), zh);
                    }
                }
            } else {
                for (let child of node.childNodes) {
                    replaceText(child);
                }
            }
        }
        
        // 执行替换
        replaceText(document.body);
        
        // 监听 DOM 变化，持续汉化动态内容
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        replaceText(node);
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }, 1000);
});
</script>
"""

def get_swagger_ui_html(*, openapi_url: str, title: str) -> str:
    """
    生成自定义的 Swagger UI HTML
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>{title}</title>
        {CUSTOM_CSS}
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '{openapi_url}',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout",
            ...{str(SWAGGER_UI_PARAMETERS).replace("'", '"')}
        }})
        </script>
        {CUSTOM_JS}
    </body>
    </html>
    """

def get_redoc_html(*, openapi_url: str, title: str) -> str:
    """
    生成自定义的 ReDoc HTML
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url="{openapi_url}" 
               language="zh-CN"
               native-scrollbars
               scroll-y-offset="body > nav"
               path-in-middle-panel
               untrusted-spec
               expand-responses="200,201"
               json-sample-expand-level="all"
               hide-download-button="false"
               disable-search="false"
               menu-toggle="true"
               no-auto-auth="false"
               theme='{{
                   "spacing": {{
                       "unit": 5,
                       "sectionHorizontal": 40,
                       "sectionVertical": 40
                   }},
                   "colors": {{
                       "primary": {{
                           "main": "#32329f"
                       }}
                   }},
                   "typography": {{
                       "fontSize": "14px",
                       "lineHeight": "1.5em",
                       "code": {{
                           "fontSize": "13px",
                           "fontFamily": "Courier, monospace"
                       }}
                   }}
               }}'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """