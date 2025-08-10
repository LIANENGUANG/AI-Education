# AI Education - 智能教育分析系统

基于AI的英语试卷分析和学生答题分析系统，支持自动批改、成绩统计和个性化分析。

## 🚀 功能特性

- **试卷分析**: 自动识别语法题、阅读题、完型填空等题型
- **智能批改**: AI解析学生答题卡，自动批改和计分
- **成绩统计**: 详细的班级成绩分析和可视化图表
- **题目分析**: 每道题的正确率和错误分布分析
- **个人分析**: AI深度分析学生学科能力和薄弱点
- **加权计分**: 不同题型采用不同权重的智能计分

## 🛠️ 技术栈

### 后端
- **Django 5.2** + **Django REST Framework**
- **百度千帆API** (DeepSeek-V3模型)
- **LangChain** 文档处理
- **SQLite** 数据库

### 前端
- **React 19** + **TypeScript**
- **Ant Design 5** UI组件库
- **Docker** 容器化部署

## 📦 快速部署

### 使用Docker部署 (推荐)

1. **克隆项目**
```bash
git clone <your-repo-url>
cd AI-Education
```

2. **配置环境变量**
```bash
# 在backend目录创建.env文件
cd backend
echo "QIANFAN_API_KEY=your_baidu_qianfan_api_key" > .env
```

3. **启动服务**
```bash
cd ..
docker-compose up -d --build
```

4. **访问应用**
- 前端: http://81.70.221.40 (或你的服务器IP)
- 后端API: http://81.70.221.40:9000 (或你的服务器IP:9000)

### 本地开发部署

#### 后端启动
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

#### 前端启动
```bash
cd frontend
npm install
npm start
```

## 🔧 配置说明

### 后端环境变量
```env
QIANFAN_API_KEY=your_baidu_qianfan_api_key
DEBUG=False
ALLOWED_HOSTS=81.70.221.40,localhost,127.0.0.1
```

### 前端API配置
- 开发环境: `http://localhost:8000`
- 生产环境: `http://81.70.221.40:9000`

## 📖 使用流程

1. **上传试卷**: 支持Word/PDF格式的试卷文档
2. **AI分析**: 自动识别题型并提取标准答案
3. **上传答题卡**: 支持Word格式的学生答题表格
4. **查看结果**: 
   - 班级成绩统计和分布
   - 题目答题分析
   - 个人AI分析报告

## 🔍 分数计算规则

采用加权计分系统，总分100分：
- **语法题**: 权重 1.0
- **阅读题**: 权重 1.5 (难度较高)
- **语言运用题**: 权重 1.2

## 📁 项目结构

```
AI-Education/
├── backend/           # Django后端
│   ├── english_review/    # 主要应用
│   ├── requirements.txt   # Python依赖
│   └── Dockerfile        # 后端Docker文件
├── frontend/          # React前端
│   ├── src/              # 源代码
│   ├── package.json      # Node依赖
│   └── Dockerfile        # 前端Docker文件
├── data/              # 测试数据
└── docker-compose.yml # Docker编排文件
```

## 🔨 开发命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

## 📞 技术支持

如有问题请联系开发团队。