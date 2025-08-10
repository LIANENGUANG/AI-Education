from django.db import models

class Document(models.Model):
    """上传的文档"""
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Exam(models.Model):
    """试卷"""
    title = models.CharField(max_length=200)
    source_document = models.ForeignKey(Document, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Question(models.Model):
    """题目"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    content = models.TextField()
    options = models.JSONField(default=list)  # 选择题选项
    correct_answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.exam.title} - 题目"