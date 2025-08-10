import requests
import json
import re
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

class StudentAnswerAPI:
    """专门用于解析学生答题卡的AI API服务"""
    
    def __init__(self):
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            "Authorization": "Bearer sk-tesxufjhmzthuaqbkaszquzgsyqjcoefrwbgaurfokzdwpco",
            "Content-Type": "application/json"
        }
    
    def parse_student_answers(self, content):
        """使用AI解析学生答题卡内容"""
        # 限制内容长度，避免超时
        if len(content) > 2500:
            content = content[:2500] + "\n...(内容已截断)"
        
        prompt = f"""
请仔细分析以下学生答题卡内容，准确提取每个学生的姓名和选择题答案。

重要说明：
1. 这是一个包含多名学生答题信息的文档
2. 每个学生都有中文姓名（如：王子萱、张紫煜等）
3. 题目编号从1到43，答案选项为A、B、C、D
4. 请逐个学生识别，确保不遗漏任何已填写的答案
5. 如果学生某题确实未作答，则不要在answers中包含该题

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "students": [
        {{
            "name": "王子萱",
            "answers": {{
                "1": "A",
                "2": "B",
                "5": "D"
            }},
            "total_answered": 3
        }}
    ]
}}

答题卡原文：
{content}"""
        
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 3000,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=45)
            response.raise_for_status()
            
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            
            print(f"学生答题卡AI返回内容长度: {len(ai_content)} 字符")
            
            # 清理内容，移除可能的markdown标记
            cleaned_content = ai_content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content.replace('```json', '').replace('```', '').strip()
            elif cleaned_content.startswith('```'):
                cleaned_content = cleaned_content.replace('```', '').strip()
            
            # 解析JSON
            parsed_data = json.loads(cleaned_content)
            students_list = parsed_data.get('students', [])
            
            return students_list
            
        except Exception as e:
            print(f"学生答题卡AI解析失败: {e}")
            return []

class StudentAnswerProcessor:
    """学生答题卡处理器"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.student_ai_api = StudentAnswerAPI()  # 使用专门的API
    
    def parse_student_answers(self, answer_sheet_path):
        """使用AI解析学生答题卡文档"""
        try:
            # 创建临时文档对象
            class TempDoc:
                def __init__(self, file_path):
                    self.file = type('obj', (object,), {'path': file_path})()
                    self.content = ""
                
                def save(self):
                    pass
            
            temp_doc = TempDoc(answer_sheet_path)
            content = self.document_processor.extract_text(temp_doc)
            
            if not content:
                return {"error": "无法提取文档内容"}
            
            # 使用专门的AI解析学生答案
            students_data = self._process_ai_parse_result(
                self.student_ai_api.parse_student_answers(content)
            )
            
            if not students_data:
                return {"error": "AI解析失败，未识别到学生数据"}
            
            return {
                "students": students_data,
                "total_students": len(students_data),
                "message": f"成功解析 {len(students_data)} 名学生的答题卡"
            }
            
        except Exception as e:
            return {"error": f"解析失败: {str(e)}"}
    
    def _process_ai_parse_result(self, students_list):
        """处理AI解析结果，标准化数据格式"""
        if not students_list:
            return []
        
        standardized_students = []
        for student in students_list:
            if 'name' in student and 'answers' in student:
                # 确保answers中的键是整数
                standardized_answers = {}
                for q_num, answer in student['answers'].items():
                    try:
                        standardized_answers[int(q_num)] = answer
                    except (ValueError, TypeError):
                        continue
                
                standardized_student = {
                    "name": student['name'],
                    "answers": standardized_answers,
                    "total_answered": len(standardized_answers)
                }
                standardized_students.append(standardized_student)
        
        print(f"最终标准化结果: 识别到 {len(standardized_students)} 名学生")
        for i, student in enumerate(standardized_students[:5]):  # 显示前5个学生
            print(f"  {i+1}. {student['name']}: 答题{student['total_answered']}题")
        
        return standardized_students
    
    def _ai_parse_answer_content(self, content):
        """使用AI解析答题卡内容"""
        # 限制内容长度，避免超时
        if len(content) > 2000:
            content = content[:2000] + "\n...(内容已截断)"
        
        prompt = f"""
请仔细分析以下学生答题卡内容，准确提取每个学生的姓名和选择题答案。

重要说明：
1. 这是一个包含多名学生答题信息的文档
2. 每个学生都有中文姓名（如：王子萱、张紫煜等）
3. 题目编号从1到43，答案选项为A、B、C、D
4. 请逐个学生识别，确保不遗漏任何已填写的答案
5. 如果学生某题确实未作答，则不要在answers中包含该题

请严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "students": [
        {{
            "name": "王子萱",
            "answers": {{
                "1": "A",
                "2": "B",
                "5": "D"
            }},
            "total_answered": 3
        }}
    ]
}}

答题卡原文：
{content}"""
        
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.ai_api.url, json=payload, headers=self.ai_api.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"AI返回原始内容长度: {len(content)} 字符")
            
            # 清理内容，移除可能的markdown标记
            cleaned_content = content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content.replace('```json', '').replace('```', '').strip()
            elif cleaned_content.startswith('```'):
                cleaned_content = cleaned_content.replace('```', '').strip()
            
            # 解析JSON
            parsed_data = json.loads(cleaned_content)
            students_list = parsed_data.get('students', [])
            
            # 验证和标准化数据格式
            standardized_students = []
            for student in students_list:
                if 'name' in student and 'answers' in student:
                    # 确保answers中的键是整数
                    standardized_answers = {}
                    for q_num, answer in student['answers'].items():
                        try:
                            standardized_answers[int(q_num)] = answer
                        except (ValueError, TypeError):
                            continue
                    
                    standardized_student = {
                        "name": student['name'],
                        "answers": standardized_answers,
                        "total_answered": len(standardized_answers)
                    }
                    standardized_students.append(standardized_student)
            
            print(f"AI解析结果: 识别到 {len(standardized_students)} 名学生")
            for i, student in enumerate(standardized_students[:5]):  # 显示前5个学生
                print(f"  {i+1}. {student['name']}: 答题{student['total_answered']}题")
            
            return standardized_students
            
        except Exception as e:
            print(f"AI解析失败: {e}")
            return []  # AI解析失败时返回空列表
    
    def grade_answers(self, students_data, standard_answers):
        """批改学生答案"""
        try:
            # 提取标准答案映射
            correct_answers = self._extract_standard_answers(standard_answers)
            
            graded_results = []
            
            for student in students_data:
                student_result = {
                    "name": student["name"],
                    "answers": student["answers"],
                    "total_answered": student["total_answered"],
                    "correct_count": 0,
                    "wrong_count": 0,
                    "missing_count": 0,
                    "score": 0,
                    "details": {}
                }
                
                # 逐题批改
                for question_num, correct_answer in correct_answers.items():
                    student_answer = student["answers"].get(question_num, None)
                    
                    if student_answer is None:
                        # 未答题
                        student_result["missing_count"] += 1
                        student_result["details"][question_num] = {
                            "student_answer": None,
                            "correct_answer": correct_answer,
                            "is_correct": False,
                            "status": "missing"
                        }
                    elif student_answer == correct_answer:
                        # 答对
                        student_result["correct_count"] += 1
                        student_result["details"][question_num] = {
                            "student_answer": student_answer,
                            "correct_answer": correct_answer,
                            "is_correct": True,
                            "status": "correct"
                        }
                    else:
                        # 答错
                        student_result["wrong_count"] += 1
                        student_result["details"][question_num] = {
                            "student_answer": student_answer,
                            "correct_answer": correct_answer,
                            "is_correct": False,
                            "status": "wrong"
                        }
                
                # 计算分数（每题2分，满分100分，43题实际满分86分）
                total_questions = len(correct_answers)
                points_per_question = 100 / total_questions if total_questions > 0 else 0
                student_result["score"] = round(student_result["correct_count"] * points_per_question, 1)
                
                graded_results.append(student_result)
            
            # 统计信息
            statistics = self._calculate_statistics(graded_results, len(correct_answers))
            
            return {
                "graded_results": graded_results,
                "statistics": statistics,
                "total_questions": len(correct_answers),
                "message": "批改完成"
            }
            
        except Exception as e:
            return {"error": f"批改失败: {str(e)}"}
    
    def _extract_standard_answers(self, analysis_result):
        """从AI分析结果中提取标准答案"""
        correct_answers = {}
        
        # 语法题答案
        for question in analysis_result.get('grammar_questions', []):
            correct_answers[question['question_number']] = question['correct_answer']
        
        # 阅读题答案
        for passage in analysis_result.get('reading_questions', []):
            for question in passage.get('questions', []):
                correct_answers[question['question_number']] = question['correct_answer']
        
        # 语言运用题答案
        for passage in analysis_result.get('language_use_questions', []):
            for question in passage.get('questions', []):
                correct_answers[question['question_number']] = question['correct_answer']
        
        return correct_answers
    
    def _calculate_statistics(self, graded_results, total_questions):
        """计算统计信息"""
        if not graded_results:
            return {}
        
        scores = [student["score"] for student in graded_results]
        correct_counts = [student["correct_count"] for student in graded_results]
        
        # 分数段统计
        score_ranges = {
            "90-100": len([s for s in scores if s >= 90]),
            "80-89": len([s for s in scores if 80 <= s < 90]),
            "70-79": len([s for s in scores if 70 <= s < 80]),
            "60-69": len([s for s in scores if 60 <= s < 70]),
            "0-59": len([s for s in scores if s < 60])
        }
        
        return {
            "total_students": len(graded_results),
            "average_score": round(sum(scores) / len(scores), 1),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "average_correct": round(sum(correct_counts) / len(correct_counts), 1),
            "pass_rate": round(len([s for s in scores if s >= 60]) / len(scores) * 100, 1),
            "score_distribution": score_ranges,
            "total_questions": total_questions
        }