import React, { useState } from 'react';
import { Table, Button, Space, Tag, Card, Upload, message, Collapse, Divider, Typography } from 'antd';
import { EditOutlined, DeleteOutlined, EyeOutlined, UploadOutlined, FileTextOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Panel } = Collapse;
const { Title, Paragraph, Text } = Typography;

const ExamList: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [examList, setExamList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 获取试卷列表的函数
  const fetchExamList = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/english/documents/');
      if (response.ok) {
        const data = await response.json();
        setExamList(data);
      }
    } catch (error) {
      console.error('获取试卷列表失败:', error);
    }
    setLoading(false);
  };

  // 组件加载时获取数据
  React.useEffect(() => {
    fetchExamList();
  }, []);
  
  const columns = [
    {
      title: '文档名称',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '状态',
      dataIndex: 'has_content',
      key: 'has_content',
      render: (has_content: boolean) => (
        <Tag color={has_content ? 'green' : 'orange'}>
          {has_content ? '已处理' : '未处理'}
        </Tag>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (record: any) => (
        <Space size="middle">
          <Button icon={<EyeOutlined />} size="small">查看</Button>
          <Button icon={<EditOutlined />} size="small">分析</Button>
          <Button icon={<DeleteOutlined />} size="small" danger>删除</Button>
        </Space>
      ),
    },
  ];

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    try {
      // 检查文件类型
      const allowedTypes = ['.docx', '.pdf', '.txt'];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      if (!allowedTypes.includes(fileExtension)) {
        message.error('请上传 .docx、.pdf 或 .txt 格式的文件');
        setIsUploading(false);
        return false;
      }

      // 第一步：上传文档
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      message.loading('正在上传文档...', 0);
      
      const uploadResponse = await fetch('http://localhost:8000/api/english/documents/', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('文档上传失败');
      }

      const uploadResult = await uploadResponse.json();
      message.destroy();
      message.success('文档上传成功，开始分析题型...');

      // 第二步：分析题型
      const analyzeResponse = await fetch(`http://localhost:8000/api/english/documents/${uploadResult.id}/analyze_types/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!analyzeResponse.ok) {
        throw new Error('题型分析失败');
      }

      const analyzeResult = await analyzeResponse.json();
      message.success(`题型分析完成！识别到 ${analyzeResult.statistics.total_questions} 道题目`);
      
      // 保存分析结果到状态中
      setAnalysisResult(analyzeResult);
      
      // 刷新文档列表
      await fetchExamList();
      
    } catch (error) {
      message.error(error instanceof Error ? error.message : '处理失败');
    }
    
    setIsUploading(false);
    return false; // 阻止自动上传
  };

  const renderQuestionSection = (title: string, questions: any[], color: string) => {
    if (!questions || questions.length === 0) return null;

    return (
      <Card 
        title={<><span style={{color}}>{title}</span> ({questions.length}道题)</>}
        style={{ marginBottom: 16 }}
        size="small"
      >
        {questions.map((question: any, index: number) => (
          <div key={index} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: index < questions.length - 1 ? '1px solid #f0f0f0' : 'none' }}>
            <Text strong>第{question.question_number}题: </Text>
            <Text>{question.question_text}</Text>
            <div style={{ marginTop: 4 }}>
              {question.options?.map((option: string, i: number) => (
                <div key={i} style={{ marginLeft: 16, color: option.startsWith(question.correct_answer) ? '#52c41a' : 'inherit' }}>
                  <Text code={option.startsWith(question.correct_answer)}>{option}</Text>
                </div>
              ))}
            </div>
          </div>
        ))}
      </Card>
    );
  };

  const renderReadingSection = (readingData: any[]) => {
    if (!readingData || readingData.length === 0) return null;

    return (
      <Card 
        title={<><span style={{color: '#1890ff'}}>阅读题</span> ({readingData.reduce((acc: number, passage: any) => acc + (passage.questions?.length || 0), 0)}道题)</>}
        style={{ marginBottom: 16 }}
        size="small"
      >
        {readingData.map((passage: any, passageIndex: number) => (
          <div key={passageIndex} style={{ marginBottom: 20 }}>
            <Title level={5}>阅读材料 {passage.passage_title}</Title>
            <Paragraph style={{ background: '#f5f5f5', padding: 12, borderRadius: 6 }}>
              {passage.passage_text}
            </Paragraph>
            {passage.questions?.map((question: any, qIndex: number) => (
              <div key={qIndex} style={{ marginBottom: 12, marginLeft: 16 }}>
                <Text strong>第{question.question_number}题: </Text>
                <Text>{question.question_text}</Text>
                <div style={{ marginTop: 4 }}>
                  {question.options?.map((option: string, i: number) => (
                    <div key={i} style={{ marginLeft: 16, color: option.startsWith(question.correct_answer) ? '#52c41a' : 'inherit' }}>
                      <Text code={option.startsWith(question.correct_answer)}>{option}</Text>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
      </Card>
    );
  };

  const renderLanguageUseSection = (languageData: any[]) => {
    if (!languageData || languageData.length === 0) return null;

    return (
      <Card 
        title={<><span style={{color: '#722ed1'}}>语言运用题</span> ({languageData.reduce((acc: number, passage: any) => acc + (passage.questions?.length || 0), 0)}道题)</>}
        style={{ marginBottom: 16 }}
        size="small"
      >
        {languageData.map((passage: any, passageIndex: number) => (
          <div key={passageIndex} style={{ marginBottom: 20 }}>
            <Title level={5}>完型填空</Title>
            <Paragraph style={{ background: '#f0f2ff', padding: 12, borderRadius: 6 }}>
              {passage.passage_text}
            </Paragraph>
            {passage.questions?.map((question: any, qIndex: number) => (
              <div key={qIndex} style={{ marginBottom: 12, marginLeft: 16 }}>
                <Text strong>第{question.question_number}题: </Text>
                <div style={{ marginTop: 4 }}>
                  {question.options?.map((option: string, i: number) => (
                    <div key={i} style={{ marginLeft: 16, color: option.startsWith(question.correct_answer) ? '#52c41a' : 'inherit' }}>
                      <Text code={option.startsWith(question.correct_answer)}>{option}</Text>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
      </Card>
    );
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.docx,.pdf,.txt',
    beforeUpload: handleFileUpload,
    showUploadList: false,
  };

  return (
    <div>
      {/* 题型分析区域 */}
      <Card 
        title={<><FileTextOutlined /> 题型分析</>}
        style={{ marginBottom: 24 }}
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Upload {...uploadProps}>
            <Button 
              type="primary" 
              icon={<UploadOutlined />}
              size="large"
              loading={isUploading}
            >
              {isUploading ? '正在AI分析...' : '上传文档分析题型'}
            </Button>
          </Upload>
          <p style={{ marginTop: 12, color: '#666' }}>
            支持 Word(.docx)、PDF(.pdf)、文本(.txt) 格式，AI将分析试卷包含的题型种类
          </p>
        </div>
      </Card>

      {/* 分析结果展示 */}
      {analysisResult && (
        <Card 
          title={<>📊 试卷分析结果 - {analysisResult.document_title}</>}
          style={{ marginBottom: 24 }}
        >
          <div style={{ marginBottom: 16, padding: 16, background: '#f6ffed', borderRadius: 6 }}>
            <Text strong>统计信息: </Text>
            <Tag color="green">语法题: {analysisResult.statistics.grammar_count}道</Tag>
            <Tag color="blue">阅读题: {analysisResult.statistics.reading_count}道</Tag>
            <Tag color="purple">语言运用题: {analysisResult.statistics.language_use_count}道</Tag>
            <Tag color="red">总计: {analysisResult.statistics.total_questions}道</Tag>
          </div>
          
          <Collapse defaultActiveKey={['1', '2', '3']} ghost>
            <Panel header="第一部分：语法选择题" key="1">
              {renderQuestionSection('语法选择题', analysisResult.structured_data.grammar_questions, '#52c41a')}
            </Panel>
            <Panel header="第二部分：阅读题" key="2">
              {renderReadingSection(analysisResult.structured_data.reading_questions)}
            </Panel>
            <Panel header="第三部分：语言运用题" key="3">
              {renderLanguageUseSection(analysisResult.structured_data.language_use_questions)}
            </Panel>
          </Collapse>
        </Card>
      )}

      {/* 现有试卷列表 */}
      <Card title="文档列表">
        <div style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={fetchExamList} loading={loading}>刷新列表</Button>
        </div>
        <Table 
          columns={columns} 
          dataSource={examList.map(item => ({ ...item, key: item.id }))} 
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default ExamList;