import requests
import json
import re
import os
from datetime import datetime
from django.conf import settings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, UnstructuredWordDocumentLoader
from .models import Document

class BaiduQianfanAPI:
    """百度千帆API调用服务"""
    
    def __init__(self):
        self.url = "https://qianfan.baidubce.com/v2/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {getattr(settings, 'QIANFAN_API_KEY', 'your-api-key')}"
        }
    
    def analyze_question_types(self, text_content):
        """分析文档中的三种题型并结构化提取"""
        prompt = f"""请分析以下英语试卷内容，按照以下三种题型分类提取题目：

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
            "model": "deepseek-v3",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的英语试卷分析助手"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            print("使用requests调用AI分析题型...")
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=300)
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
        """从文档中提取文本，对于答题卡使用结构化解析"""
        file_path = document.file.path
        file_extension = file_path.split('.')[-1].lower()
        
        try:
            if file_extension == 'txt':
                loader = TextLoader(file_path)
                docs = loader.load()
                content = "\n".join([doc.page_content for doc in docs])
            elif file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                content = "\n".join([doc.page_content for doc in docs])
            elif file_extension in ['docx', 'doc']:
                # 检查是否是答题卡文件（包含表格结构）
                if self._is_answer_sheet(file_path):
                    print("检测到答题卡文档，使用结构化解析...")
                    loader = UnstructuredWordDocumentLoader(file_path, mode="elements")
                    docs = loader.load()
                    content = self._process_structured_elements(docs)
                else:
                    # 普通文档使用标准解析
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load()
                    content = "\n".join([doc.page_content for doc in docs])
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
            
            print(f"提取的文档内容长度: {len(content)} 字符")
            print(f"文档内容预览: {content[:200]}...")
            
            # 保存提取的内容到数据库
            document.content = content
            document.save()
            
            return content
            
        except Exception as e:
            print(f"文档处理错误: {e}")
            return ""
    
    def _is_answer_sheet(self, file_path):
        """检测是否是答题卡文件"""
        filename = os.path.basename(file_path).lower()
        # 简单的启发式检测
        return ('答题卡' in filename or 'answer' in filename or 
                '学生' in filename or 'student' in filename)
    
    def _process_structured_elements(self, docs):
        """处理结构化元素，重建表格格式"""
        print(f"处理 {len(docs)} 个文档元素...")
        
        # 分析元素类型
        table_elements = []
        text_elements = []
        
        for i, doc in enumerate(docs):
            category = doc.metadata.get('category', 'Unknown')
            content = doc.page_content.strip()
            
            if category == 'Table':
                table_elements.append((i, content))
                print(f"表格元素 [{i}]: {content[:50]}...")
            else:
                text_elements.append((i, category, content))
                if i < 10:  # 只显示前10个元素用于调试
                    print(f"文本元素 [{i}] ({category}): {content[:30]}...")
        
        if table_elements:
            print(f"找到 {len(table_elements)} 个表格元素")
            # 如果有表格元素，使用表格内容
            table_content = "\n".join([content for _, content in table_elements])
            return self._clean_table_content(table_content)
        else:
            print("未找到表格元素，使用智能重建...")
            # 如果没有表格元素，尝试智能重建表格结构
            return self._reconstruct_table_from_elements(text_elements)
    
    def _clean_table_content(self, table_content):
        """清理表格内容，去除多余空白"""
        lines = table_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and line not in ['', ' ', '\t']:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _reconstruct_table_from_elements(self, text_elements):
        """从文本元素重建表格结构"""
        print("重建表格结构...")
        
        # 查找关键元素
        students = []
        current_student = None
        answers = []
        
        for i, category, content in text_elements:
            content = content.strip()
            
            # 识别学生姓名（中文，2-4字符）
            if (content and len(content) >= 2 and len(content) <= 4 and 
                any('\u4e00' <= char <= '\u9fff' for char in content) and
                content != '姓名' and not content.isdigit() and 
                content not in ['A', 'B', 'C', 'D']):
                
                if current_student:
                    # 保存上一个学生
                    students.append(f"{current_student}: {' '.join(answers)}")
                
                current_student = content
                answers = []
                print(f"识别学生: {current_student}")
            
            # 识别答案
            elif content in ['A', 'B', 'C', 'D'] and current_student:
                answers.append(content)
            
            # 识别空答案（空字符串或题号后的空内容）
            elif content == '' and current_student and len(answers) < 43:
                answers.append('-')
        
        # 保存最后一个学生
        if current_student and answers:
            students.append(f"{current_student}: {' '.join(answers)}")
        
        print(f"重建完成，识别到 {len(students)} 名学生")
        return '\n\n'.join(students)

class SimpleAnalyzer:
    """简化的分析器 - 只分析题型"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ai_api = BaiduQianfanAPI()
    
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
            
            # 保存分析结果到JSON文件用于调试
            self._save_analysis_to_json(document.title, structured_data, content)
            
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
    
    def _save_analysis_to_json(self, document_title, structured_data, original_content):
        """保存分析结果到JSON文件用于调试"""
        try:
            # 创建调试目录
            debug_dir = os.path.join(os.path.dirname(__file__), '..', 'debug_json')
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}_{document_title.replace(' ', '_')}.json"
            filepath = os.path.join(debug_dir, filename)
            
            # 准备保存的数据
            debug_data = {
                "document_title": document_title,
                "analysis_time": datetime.now().isoformat(),
                "original_content_length": len(original_content),
                "original_content_preview": original_content[:500] + "..." if len(original_content) > 500 else original_content,
                "structured_data": structured_data,
                "statistics": {
                    "grammar_count": len(structured_data.get('grammar_questions', [])),
                    "reading_count": sum(len(passage.get('questions', [])) for passage in structured_data.get('reading_questions', [])),
                    "language_use_count": sum(len(passage.get('questions', [])) for passage in structured_data.get('language_use_questions', [])),
                    "total_questions": len(structured_data.get('grammar_questions', [])) + 
                                     sum(len(passage.get('questions', [])) for passage in structured_data.get('reading_questions', [])) +
                                     sum(len(passage.get('questions', [])) for passage in structured_data.get('language_use_questions', []))
                }
            }
            
            # 保存JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            
            print(f"调试信息已保存到: {filepath}")
            
        except Exception as e:
            print(f"保存调试JSON文件失败: {e}")

class StudentAnswerAPI:
    """专门用于解析学生答题卡的百度千帆API服务"""
    
    def __init__(self):
        self.url = "https://qianfan.baidubce.com/v2/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {getattr(settings, 'QIANFAN_API_KEY', 'your-api-key')}"
        }
    
    def parse_student_answers(self, content):
        """使用AI解析学生答题卡内容 - 处理全部内容"""
        print(f"开始AI解析学生答题卡，原始内容长度: {len(content)} 字符")
        
        prompt = f"""这是一个表格格式的答题卡数据，每行包含：姓名 + 题号序列 + 学生姓名 + 答案序列

示例：姓名 1 2 3... 王子萱 B A A C D...

请提取所有学生数据，返回JSON：
{{"students":[{{"name":"姓名","answers":{{"1":"A","2":"B"}},"total_answered":2}}]}}

数据：
{content}"""
        
        payload = {
            "model": "deepseek-v3",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的答题卡数据提取助手"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            print("正在调用AI解析...")
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            
            print(f"AI解析成功，返回内容长度: {len(ai_content)}")
            
            # 清理JSON内容
            cleaned = ai_content.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            elif cleaned.startswith('```'):
                cleaned = cleaned.replace('```', '').strip()
            
            print(f"清理后的JSON内容: {cleaned[:500]}...")
            
            # 尝试找到JSON结构的结束位置
            try:
                # 查找第一个完整的JSON对象
                json_end = cleaned.find('}')
                if json_end != -1:
                    # 找到所有匹配的大括号
                    brace_count = 0
                    for i, char in enumerate(cleaned):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    # 提取纯JSON部分
                    json_only = cleaned[:json_end]
                    print(f"提取的纯JSON: {json_only}")
                    
                    parsed_data = json.loads(json_only)
                else:
                    parsed_data = json.loads(cleaned)
            except json.JSONDecodeError:
                # 如果还是失败，尝试解析整个内容
                parsed_data = json.loads(cleaned)
            students_list = parsed_data.get('students', [])
            
            print(f"解析得到 {len(students_list)} 名学生")
            return students_list
            
        except Exception as e:
            print(f"AI解析失败: {e}")
            return []  # AI解析失败时返回空列表

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