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
