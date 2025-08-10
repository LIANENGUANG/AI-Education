from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Document
from .services import SimpleAnalyzer, StudentAnswerProcessor
import os

class DocumentViewSet(viewsets.ModelViewSet):
    """文档管理API"""
    queryset = Document.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def create(self, request):
        """上传文档"""
        try:
            file = request.FILES.get('file')
            title = request.data.get('title', file.name if file else 'Untitled')
            
            if not file:
                return Response({'error': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
            
            document = Document.objects.create(
                title=title,
                file=file
            )
            
            return Response({
                'id': document.id,
                'title': document.title,
                'created_at': document.created_at,
                'message': '文档上传成功'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def list(self, request):
        """获取文档列表"""
        documents = Document.objects.all().order_by('-created_at')
        data = [{
            'id': doc.id,
            'title': doc.title,
            'has_content': bool(doc.content),
            'created_at': doc.created_at
        } for doc in documents]
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def analyze_types(self, request, pk=None):
        """分析文档题型"""
        try:
            analyzer = SimpleAnalyzer()
            result = analyzer.analyze_document_types(pk)
            
            if 'error' in result:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def grade_answer_sheet(self, request):
        """批改学生答题卡"""
        try:
            # 获取上传的答题卡文件
            answer_file = request.FILES.get('answer_sheet')
            if not answer_file:
                return Response({'error': '请上传答题卡文件'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取标准答案数据
            standard_answers = request.data.get('standard_answers')
            if not standard_answers:
                return Response({'error': '请提供标准答案'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 保存临时文件
            temp_file_path = f'/tmp/{answer_file.name}'
            with open(temp_file_path, 'wb+') as destination:
                for chunk in answer_file.chunks():
                    destination.write(chunk)
            
            try:
                # 处理答题卡
                processor = StudentAnswerProcessor()
                
                # 解析学生答案
                parse_result = processor.parse_student_answers(temp_file_path)
                if 'error' in parse_result:
                    return Response({'error': parse_result['error']}, status=status.HTTP_400_BAD_REQUEST)
                
                # 批改答案
                import json
                if isinstance(standard_answers, str):
                    standard_answers = json.loads(standard_answers)
                
                grade_result = processor.grade_answers(parse_result['students'], standard_answers)
                if 'error' in grade_result:
                    return Response({'error': grade_result['error']}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'parse_result': parse_result,
                    'grade_result': grade_result,
                    'message': '答题卡批改完成'
                })
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def analyze_question_performance(self, request):
        """分析题目答题情况和得分率"""
        try:
            # 获取批改结果数据
            graded_results = request.data.get('graded_results')
            if not graded_results:
                return Response({'error': '请提供批改结果数据'}, status=status.HTTP_400_BAD_REQUEST)
            
            import json
            if isinstance(graded_results, str):
                graded_results = json.loads(graded_results)
            
            # 分析题目表现
            question_analysis = self._analyze_question_performance(graded_results)
            
            return Response(question_analysis)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _analyze_question_performance(self, graded_results):
        """分析每道题的答题情况"""
        question_stats = {}
        total_students = len(graded_results)
        
        if total_students == 0:
            return {'questions': [], 'total_students': 0}
        
        # 统计每道题的情况
        for student in graded_results:
            details = student.get('details', {})
            for question_num, detail in details.items():
                q_num = int(question_num)
                
                if q_num not in question_stats:
                    question_stats[q_num] = {
                        'question_number': q_num,
                        'correct_count': 0,
                        'wrong_count': 0,
                        'missing_count': 0,
                        'correct_answer': detail.get('correct_answer')
                    }
                
                status_val = detail.get('status', 'missing')
                
                if status_val == 'correct':
                    question_stats[q_num]['correct_count'] += 1
                elif status_val == 'wrong':
                    question_stats[q_num]['wrong_count'] += 1
                else:  # missing
                    question_stats[q_num]['missing_count'] += 1
        
        # 计算得分率
        questions_list = []
        for q_num, stats in question_stats.items():
            total_answered = stats['correct_count'] + stats['wrong_count']
            accuracy_rate = (stats['correct_count'] / total_students * 100) if total_students > 0 else 0
            
            questions_list.append({
                'question_number': q_num,
                'correct_count': stats['correct_count'],
                'wrong_count': stats['wrong_count'],
                'missing_count': stats['missing_count'],
                'accuracy_rate': round(accuracy_rate, 1),
                'correct_answer': stats['correct_answer']
            })
        
        # 按题号排序
        questions_list.sort(key=lambda x: x['question_number'])
        
        return {
            'questions': questions_list,
            'total_students': total_students
        }

    @action(detail=False, methods=['post'])
    def analyze_student_performance(self, request):
        """分析单个学生的学科能力和薄弱点"""
        try:
            # 获取数据
            student_data = request.data.get('student_data')
            standard_answers = request.data.get('standard_answers') 
            test_questions = request.data.get('test_questions', '')
            
            print(f"学生分析API调用 - student_data类型: {type(student_data)}, standard_answers类型: {type(standard_answers)}")
            
            if not student_data or not standard_answers:
                return Response({'error': '请提供学生数据和标准答案'}, status=status.HTTP_400_BAD_REQUEST)
            
            import json
            if isinstance(student_data, str):
                student_data = json.loads(student_data)
            if isinstance(standard_answers, str):
                standard_answers = json.loads(standard_answers)
            
            print(f"解析后 - 学生姓名: {student_data.get('name', '未知')}, 详情数量: {len(student_data.get('details', {}))}")
            
            # 使用AI分析学生表现
            analysis_result = self._analyze_student_with_ai(student_data, standard_answers, test_questions)
            
            return Response(analysis_result)
            
        except Exception as e:
            print(f"学生分析API异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _analyze_student_with_ai(self, student_data, standard_answers, test_questions):
        """使用AI分析学生的学科能力和薄弱点"""
        from .services import BaiduQianfanAPI
        import json
        
        try:
            # 提取学生答题详情
            student_name = student_data.get('name', '学生')
            student_answers = student_data.get('details', {})
            score = student_data.get('score', 0)
            correct_count = student_data.get('correct_count', 0)
            wrong_count = student_data.get('wrong_count', 0)
            
            print(f"开始AI分析 - 学生: {student_name}, 答题详情数量: {len(student_answers)}")
            
            # 构建分析数据，包含题目内容
            analysis_data = []
            wrong_questions = []
            correct_questions = []
            
            # 从标准答案中获取题目内容
            all_questions_map = {}
            
            # 收集语法题
            if 'grammar_questions' in standard_answers:
                for q in standard_answers['grammar_questions']:
                    all_questions_map[str(q['question_number'])] = {
                        'type': '语法题',
                        'question_text': q.get('question_text', ''),
                        'options': q.get('options', []),
                        'correct_answer': q.get('correct_answer', '')
                    }
            
            # 收集阅读题
            if 'reading_questions' in standard_answers:
                for passage in standard_answers['reading_questions']:
                    for q in passage.get('questions', []):
                        all_questions_map[str(q['question_number'])] = {
                            'type': '阅读题',
                            'passage_text': passage.get('passage_text', ''),
                            'question_text': q.get('question_text', ''),
                            'options': q.get('options', []),
                            'correct_answer': q.get('correct_answer', '')
                        }
            
            # 收集语言运用题
            if 'language_use_questions' in standard_answers:
                for passage in standard_answers['language_use_questions']:
                    for q in passage.get('questions', []):
                        all_questions_map[str(q['question_number'])] = {
                            'type': '语言运用题',
                            'passage_text': passage.get('passage_text', ''),
                            'question_text': q.get('question_text', ''),
                            'options': q.get('options', []),
                            'correct_answer': q.get('correct_answer', '')
                        }
            
            for q_num, detail in student_answers.items():
                question_info = {
                    'question_number': q_num,
                    'student_answer': detail.get('student_answer'),
                    'correct_answer': detail.get('correct_answer'),
                    'status': detail.get('status')
                }
                
                # 添加题目详细信息
                if q_num in all_questions_map:
                    question_detail = all_questions_map[q_num]
                    question_info.update({
                        'question_type': question_detail['type'],
                        'question_text': question_detail['question_text'],
                        'options': question_detail['options'],
                        'passage_text': question_detail.get('passage_text', '')
                    })
                
                analysis_data.append(question_info)
                
                if detail.get('status') == 'wrong':
                    wrong_questions.append(q_num)
                elif detail.get('status') == 'correct':
                    correct_questions.append(q_num)
            
            # 构建AI分析prompt
            prompt = f"""请详细分析以下学生的英语考试表现，基于具体题目内容给出学科能力评价和薄弱点分析：

学生姓名：{student_name}
考试得分：{score}分
答对题数：{correct_count}题
答错题数：{wrong_count}题

详细答题分析：
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

请基于具体的题目内容和学生的答题情况，从以下几个方面进行深入分析并返回JSON格式：

分析要求：
1. 仔细查看每道错题的题目类型、具体内容、正确答案和学生答案
2. 识别学生在语法、词汇、阅读理解等方面的具体问题
3. 根据错题分布分析学生的知识薄弱点
4. 给出针对性的学习建议

返回格式：
{{
    "overall_assessment": "整体评价（基于具体答题表现的综合评估）",
    "strengths": ["具体优势点1", "具体优势点2"],
    "weaknesses": ["具体薄弱点1（如：时态语法掌握不佳）", "具体薄弱点2（如：词汇理解有误）"],  
    "subject_abilities": {{
        "grammar": {{"score": 分数, "analysis": "基于语法题答题情况的具体分析"}},
        "reading": {{"score": 分数, "analysis": "基于阅读题答题情况的具体分析"}},
        "language_use": {{"score": 分数, "analysis": "基于语言运用题答题情况的具体分析"}}
    }},
    "improvement_suggestions": ["针对性建议1", "针对性建议2", "针对性建议3"],
    "error_patterns": ["错误模式1", "错误模式2"]
}}

请严格按照JSON格式返回，基于具体题目内容进行分析，不要给出泛泛的评价。"""

            api = BaiduQianfanAPI()
            
            # 调用AI分析
            payload = {
                "model": "deepseek-v3",
                "messages": [
                    {
                        "role": "system", 
                        "content": "你是一个专业的英语学科分析师，擅长分析学生的学习表现"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            print("调用AI分析学生表现...")
            print("=" * 80)
            print("完整的AI分析Prompt:")
            print(prompt)
            print("=" * 80)
            import requests
            response = requests.post(api.url, json=payload, headers=api.headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            
            print(f"AI响应原始内容: {ai_content[:200]}...")
            
            # 清理和解析JSON
            cleaned = ai_content.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            elif cleaned.startswith('```'):
                cleaned = cleaned.replace('```', '').strip()
            
            analysis_result = json.loads(cleaned)
            
            # 添加基础统计信息
            analysis_result['student_info'] = {
                'name': student_name,
                'score': score,
                'correct_count': correct_count,
                'wrong_count': wrong_count,
                'total_questions': len(student_answers)
            }
            
            print(f"AI分析成功，返回结果")
            return analysis_result
            
        except Exception as e:
            print(f"AI分析失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回基础分析结果
            student_name = student_data.get('name', '学生')
            score = student_data.get('score', 0)
            correct_count = student_data.get('correct_count', 0)
            wrong_count = student_data.get('wrong_count', 0)
            student_answers = student_data.get('details', {})
            
            return {
                'student_info': {
                    'name': student_name,
                    'score': score,
                    'correct_count': correct_count, 
                    'wrong_count': wrong_count,
                    'total_questions': len(student_answers)
                },
                'overall_assessment': f'{student_name}得分{score}分，AI分析暂时失败，请稍后重试',
                'strengths': ['答题积极性高'],
                'weaknesses': ['需要进一步练习'],
                'subject_abilities': {
                    'grammar': {'score': max(0, score-10), 'analysis': '需要更多练习'},
                    'reading': {'score': max(0, score-5), 'analysis': '需要更多练习'},
                    'language_use': {'score': max(0, score), 'analysis': '需要更多练习'}
                },
                'improvement_suggestions': ['多做练习', '重点复习错题', '加强基础知识学习'],
                'error': f'AI分析失败: {str(e)}'
            }
