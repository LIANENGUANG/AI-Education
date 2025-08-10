import requests
import json
from django.conf import settings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from .models import Document

class SiliconFlowAPI:
    """SiliconFlow API调用服务"""
    
    def __init__(self):
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {getattr(settings, 'SILICONFLOW_API_KEY', 'your-api-key')}",
            "Content-Type": "application/json"
        }
    
    def analyze_question_types(self, text_content):
        """分析文档中的三种题型并结构化提取"""
        prompt = f"""
        请分析以下英语试卷内容，按照以下三种题型分类提取题目：

        1. 语法选择题 - 通常在第一部分，测试语法知识
        2. 阅读题 - 包含阅读材料和相关问题  
        3. 语言运用题 - 完型填空，在短文中选择最佳选项

        请按以下JSON格式返回：
        {{
            "grammar_questions": [
                {{
                    "question_number": 1,
                    "question_text": "题目内容",
                    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                    "correct_answer": "A"
                }}
            ],
            "reading_questions": [
                {{
                    "passage_title": "A",
                    "passage_text": "阅读材料原文",
                    "questions": [
                        {{
                            "question_number": 21,
                            "question_text": "题目内容",
                            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                            "correct_answer": "A"
                        }}
                    ]
                }}
            ],
            "language_use_questions": [
                {{
                    "passage_text": "语言运用（完型填空）原文（用___表示空格）",
                    "questions": [
                        {{
                            "question_number": 29,
                            "blank_number": 29,
                            "options": ["A. study", "B. rent", "C. visit", "D. settle"],
                            "correct_answer": "D"
                        }}
                    ]
                }}
            ]
        }}

        文档内容：
        {text_content}

        请严格按照JSON格式返回，不要包含其他解释文字。
        """
        
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"AI返回原始内容: {content}")
            print(f"内容长度: {len(content)} 字符")
            
            # 清理内容，移除可能的markdown标记
            cleaned_content = content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content.replace('```json', '').replace('```', '').strip()
            elif cleaned_content.startswith('```'):
                cleaned_content = cleaned_content.replace('```', '').strip()
            
            print(f"清理后的内容: {cleaned_content}")
            
            # 解析JSON
            structured_data = json.loads(cleaned_content)
            
            # 统计题目数量
            grammar_count = len(structured_data.get('grammar_questions', []))
            reading_count = sum(len(passage.get('questions', [])) for passage in structured_data.get('reading_questions', []))
            language_use_count = sum(len(passage.get('questions', [])) for passage in structured_data.get('language_use_questions', []))
            
            print(f"提取结果：语法题{grammar_count}道，阅读题{reading_count}道，语言运用题{language_use_count}道")
            
            return structured_data
            
        except Exception as e:
            print(f"处理失败: {e}")
            # 返回空结构，让前端知道失败了
            return {
                "grammar_questions": [],
                "reading_questions": [],
                "language_use_questions": []
            }

class DocumentProcessor:
    """文档处理服务"""
    
    def extract_text(self, document):
        """从文档中提取文本"""
        file_path = document.file.path
        file_extension = file_path.split('.')[-1].lower()
        
        try:
            if file_extension == 'txt':
                loader = TextLoader(file_path)
            elif file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension in ['docx', 'doc']:
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
            
            docs = loader.load()
            content = "\n".join([doc.page_content for doc in docs])
            
            print(f"提取的文档内容长度: {len(content)} 字符")
            print(f"文档内容预览: {content[:200]}...")
            
            # 保存提取的内容到数据库
            document.content = content
            document.save()
            
            return content
            
        except Exception as e:
            print(f"文档处理错误: {e}")
            return ""

class SimpleAnalyzer:
    """简化的分析器 - 只分析题型"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ai_api = SiliconFlowAPI()
    
    def analyze_document_types(self, document_id):
        """分析文档题型"""
        try:
            # 1. 获取文档
            document = Document.objects.get(id=document_id)
            print(f"开始分析文档: {document.title}")
            
            # 2. 提取文档文本
            if not document.content:
                content = self.document_processor.extract_text(document)
            else:
                content = document.content
            
            if not content:
                print("错误: 无法提取文档内容")
                return {"error": "无法提取文档内容"}
            
            # 3. 使用AI分析题型
            structured_data = self.ai_api.analyze_question_types(content)
            
            # 统计题目数量
            grammar_count = len(structured_data.get('grammar_questions', []))
            reading_count = sum(len(passage.get('questions', [])) for passage in structured_data.get('reading_questions', []))
            language_use_count = sum(len(passage.get('questions', [])) for passage in structured_data.get('language_use_questions', []))
            total_questions = grammar_count + reading_count + language_use_count
            
            print(f"=== 题型分析结果 ===")
            print(f"文档: {document.title}")
            print(f"语法选择题: {grammar_count}道")
            print(f"阅读题: {reading_count}道") 
            print(f"语言运用题: {language_use_count}道")
            print(f"总题目数: {total_questions}道")
            print("==================")
            
            return {
                "document_title": document.title,
                "structured_data": structured_data,
                "statistics": {
                    "grammar_count": grammar_count,
                    "reading_count": reading_count,
                    "language_use_count": language_use_count,
                    "total_questions": total_questions
                },
                "message": "题型分析完成"
            }
            
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"错误: {error_msg}")
            return {"error": error_msg}