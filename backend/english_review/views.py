from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .services import SimpleAnalyzer, StudentAnswerProcessor
import os

class DocumentViewSet(viewsets.ModelViewSet):
    """文档管理API"""
    queryset = Document.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    
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
            
            if not student_data or not standard_answers:
                return Response({'error': '请提供学生数据和标准答案'}, status=status.HTTP_400_BAD_REQUEST)
            
            import json
            if isinstance(student_data, str):
                student_data = json.loads(student_data)
            if isinstance(standard_answers, str):
                standard_answers = json.loads(standard_answers)
            
            # 使用AI分析学生表现
            analysis_result = self._analyze_student_with_ai(student_data, standard_answers, test_questions)
            
            return Response(analysis_result)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _analyze_student_with_ai(self, student_data, standard_answers, test_questions):
        """使用AI分析学生的学科能力和薄弱点"""
        from .services import BaiduQianfanAPI
        
        # 提取学生答题详情
        student_name = student_data.get('name', '学生')
        student_answers = student_data.get('details', {})
        score = student_data.get('score', 0)
        correct_count = student_data.get('correct_count', 0)
        wrong_count = student_data.get('wrong_count', 0)
        
        # 构建分析数据
        analysis_data = []
        wrong_questions = []
        correct_questions = []
        
        for q_num, detail in student_answers.items():
            question_info = {
                'question_number': q_num,
                'student_answer': detail.get('student_answer'),
                'correct_answer': detail.get('correct_answer'),
                'status': detail.get('status')
            }
            
            analysis_data.append(question_info)
            
            if detail.get('status') == 'wrong':
                wrong_questions.append(q_num)
            elif detail.get('status') == 'correct':
                correct_questions.append(q_num)
        
        # 构建AI分析prompt
        prompt = f"""请分析以下学生的英语考试表现，给出学科能力评价和薄弱点分析：

学生姓名：{student_name}
考试得分：{score}分
答对题数：{correct_count}题
答错题数：{wrong_count}题

答题详情：
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

请从以下几个方面进行分析并返回JSON格式：
{{
    "overall_assessment": "整体评价（学生的英语水平如何）",
    "strengths": ["优势点1", "优势点2"],
    "weaknesses": ["薄弱点1", "薄弱点2"],  
    "subject_abilities": {{
        "grammar": {{"score": 分数, "analysis": "语法能力分析"}},
        "reading": {{"score": 分数, "analysis": "阅读能力分析"}},
        "language_use": {{"score": 分数, "analysis": "语言运用能力分析"}}
    }},
    "improvement_suggestions": ["建议1", "建议2", "建议3"]
}}

请严格按照JSON格式返回，不要包含其他文字。"""

        try:
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
            import requests
            response = requests.post(api.url, json=payload, headers=api.headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            
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
            
            return analysis_result
            
        except Exception as e:
            print(f"AI分析失败: {e}")
            # 返回基础分析结果
            return {
                'student_info': {
                    'name': student_name,
                    'score': score,
                    'correct_count': correct_count, 
                    'wrong_count': wrong_count,
                    'total_questions': len(student_answers)
                },
                'overall_assessment': f'{student_name}得分{score}分，需要进一步分析',
                'strengths': [],
                'weaknesses': [],
                'subject_abilities': {
                    'grammar': {'score': 0, 'analysis': '分析失败'},
                    'reading': {'score': 0, 'analysis': '分析失败'},
                    'language_use': {'score': 0, 'analysis': '分析失败'}
                },
                'improvement_suggestions': ['请重试分析'],
                'error': str(e)
            }
