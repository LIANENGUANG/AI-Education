import React, { useState } from 'react';
import { Card, Button, Modal, Spin, message, Typography, Row, Col, Progress, Tag, List } from 'antd';
import { UserOutlined, BarChartOutlined } from '@ant-design/icons';
import { API_BASE_URL } from '../../config/api';

const { Text, Paragraph } = Typography;

interface StudentAnalysisProps {
  student: any;
  standardAnswers: any;
  onClose: () => void;
}

const StudentAnalysis: React.FC<StudentAnalysisProps> = ({
  student,
  standardAnswers,
  onClose
}) => {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/api/english/documents/analyze_student_performance/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_data: student,
          standard_answers: standardAnswers
        })
      });
      
      if (!response.ok) {
        throw new Error('分析请求失败');
      }
      
      const data = await response.json();
      
      setAnalysisResult(data);
      message.success('学生分析完成');
      
    } catch (error: any) {
      message.error('分析失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const renderSubjectAbility = (subject: string, data: any) => {
    const scoreColor = data.score >= 80 ? '#52c41a' : data.score >= 60 ? '#faad14' : '#f5222d';
    
    return (
      <Card size="small" style={{ marginBottom: 12 }}>
        <Row align="middle">
          <Col span={8}>
            <Text strong>{getSubjectName(subject)}</Text>
          </Col>
          <Col span={8}>
            <Progress 
              percent={data.score} 
              size="small" 
              strokeColor={scoreColor}
              format={(percent) => `${percent}分`}
            />
          </Col>
          <Col span={8}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {data.analysis}
            </Text>
          </Col>
        </Row>
      </Card>
    );
  };

  const getSubjectName = (subject: string) => {
    const names = {
      grammar: '语法能力',
      reading: '阅读能力', 
      language_use: '语言运用'
    };
    return names[subject as keyof typeof names] || subject;
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <UserOutlined style={{ marginRight: 8 }} />
          {student?.name || '学生'} - 学科能力分析
        </div>
      }
      open={true}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button key="analyze" type="primary" onClick={handleAnalyze} loading={loading}>
          <BarChartOutlined /> AI分析
        </Button>
      ]}
    >
      <Spin spinning={loading} tip="AI正在分析学生表现...">
        <div style={{ minHeight: 400 }}>
          {/* 学生基本信息 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={24}>
              <Col span={6}>
                <Text type="secondary">学生姓名</Text><br />
                <Text strong>{student?.name || '未知'}</Text>
              </Col>
              <Col span={6}>
                <Text type="secondary">考试得分</Text><br />
                <Text strong style={{ color: '#1890ff' }}>{student?.score || 0}分</Text>
              </Col>
              <Col span={6}>
                <Text type="secondary">答对题数</Text><br />
                <Text strong style={{ color: '#52c41a' }}>{student?.correct_count || 0}题</Text>
              </Col>
              <Col span={6}>
                <Text type="secondary">答错题数</Text><br />
                <Text strong style={{ color: '#f5222d' }}>{student?.wrong_count || 0}题</Text>
              </Col>
            </Row>
          </Card>

          {/* AI分析结果 */}
          {analysisResult ? (
            <div>
              {/* 整体评价 */}
              <Card title="整体评价" size="small" style={{ marginBottom: 16 }}>
                <Paragraph>{analysisResult.overall_assessment}</Paragraph>
              </Card>

              <Row gutter={16}>
                {/* 优势点 */}
                <Col span={12}>
                  <Card title="优势点" size="small" style={{ marginBottom: 16 }}>
                    {analysisResult.strengths?.length > 0 ? (
                      <List
                        size="small"
                        dataSource={analysisResult.strengths}
                        renderItem={(item: string) => (
                          <List.Item>
                            <Tag color="green">{item}</Tag>
                          </List.Item>
                        )}
                      />
                    ) : (
                      <Text type="secondary">暂无明显优势</Text>
                    )}
                  </Card>
                </Col>

                {/* 薄弱点 */}
                <Col span={12}>
                  <Card title="薄弱点" size="small" style={{ marginBottom: 16 }}>
                    {analysisResult.weaknesses?.length > 0 ? (
                      <List
                        size="small"
                        dataSource={analysisResult.weaknesses}
                        renderItem={(item: string) => (
                          <List.Item>
                            <Tag color="red">{item}</Tag>
                          </List.Item>
                        )}
                      />
                    ) : (
                      <Text type="secondary">表现均衡</Text>
                    )}
                  </Card>
                </Col>
              </Row>

              {/* 学科能力分析 */}
              <Card title="学科能力分析" size="small" style={{ marginBottom: 16 }}>
                {analysisResult.subject_abilities && (
                  <div>
                    {Object.entries(analysisResult.subject_abilities).map(([subject, data]: [string, any]) => 
                      renderSubjectAbility(subject, data)
                    )}
                  </div>
                )}
              </Card>

              {/* 改进建议 */}
              <Card title="改进建议" size="small" style={{ marginBottom: 16 }}>
                {analysisResult.improvement_suggestions?.length > 0 ? (
                  <List
                    size="small"
                    dataSource={analysisResult.improvement_suggestions}
                    renderItem={(item: string, index: number) => (
                      <List.Item>
                        <Text>{index + 1}. {item}</Text>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Text type="secondary">继续保持当前学习状态</Text>
                )}
              </Card>

              {/* 错误模式 */}
              {analysisResult.error_patterns && analysisResult.error_patterns.length > 0 && (
                <Card title="错误模式分析" size="small">
                  <List
                    size="small"
                    dataSource={analysisResult.error_patterns}
                    renderItem={(item: string, index: number) => (
                      <List.Item>
                        <Tag color="orange">{index + 1}. {item}</Tag>
                      </List.Item>
                    )}
                  />
                </Card>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Text type="secondary">点击"AI分析"按钮开始分析学生表现</Text>
            </div>
          )}
        </div>
      </Spin>
    </Modal>
  );
};

export default StudentAnalysis;