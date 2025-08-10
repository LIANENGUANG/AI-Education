from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .services import SimpleAnalyzer

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
