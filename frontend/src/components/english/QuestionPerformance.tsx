import React, { useState } from 'react';
import { Card, Table, Progress, Tag, Button, message, Typography, Space, Statistic, Row, Col } from 'antd';
import { BarChartOutlined, FileSearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { API_BASE_URL } from '../../config/api';

const { Title, Text } = Typography;

interface QuestionStats {
  question_number: number;
  correct_count: number;
  wrong_count: number;
  missing_count: number;
  accuracy_rate: number;
  correct_answer: string;
}

interface QuestionPerformanceProps {
  gradeResults?: any[];
  isVisible?: boolean;
}

const QuestionPerformance: React.FC<QuestionPerformanceProps> = ({
  gradeResults = [],
  isVisible = true
}) => {
  const [loading, setLoading] = useState(false);
  const [questionStats, setQuestionStats] = useState<QuestionStats[]>([]);
  const [totalStudents, setTotalStudents] = useState(0);

  const handleAnalyze = async () => {
    if (!gradeResults || gradeResults.length === 0) {
      message.error('没有可分析的学生答题数据');
      return;
    }

    try {
      setLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/api/english/documents/analyze_question_performance/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          graded_results: gradeResults
        })
      });
      
      if (!response.ok) {
        throw new Error('分析请求失败');
      }
      
      const data = await response.json();
      
      setQuestionStats(data.questions);
      setTotalStudents(data.total_students);
      message.success('题目分析完成');
      
    } catch (error: any) {
      message.error('分析失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<QuestionStats> = [
    {
      title: '题号',
      dataIndex: 'question_number',
      key: 'question_number',
      width: 80,
      sorter: (a: QuestionStats, b: QuestionStats) => a.question_number - b.question_number,
      defaultSortOrder: 'ascend' as const,
      render: (num: number) => <Text strong>第{num}题</Text>
    },
    {
      title: '正确答案',
      dataIndex: 'correct_answer',
      key: 'correct_answer',
      width: 100,
      render: (answer: string) => (
        <Tag color="green" style={{ fontSize: '14px', fontWeight: 'bold' }}>
          {answer}
        </Tag>
      )
    },
    {
      title: '正确人数',
      dataIndex: 'correct_count',
      key: 'correct_count',
      width: 100,
      render: (count: number) => (
        <Tag color="success">{count}人</Tag>
      ),
      sorter: (a: QuestionStats, b: QuestionStats) => b.correct_count - a.correct_count
    },
    {
      title: '错误人数',
      dataIndex: 'wrong_count',
      key: 'wrong_count',
      width: 100,
      render: (count: number) => (
        <Tag color="error">{count}人</Tag>
      ),
      sorter: (a: QuestionStats, b: QuestionStats) => b.wrong_count - a.wrong_count
    },
    {
      title: '未答人数',
      dataIndex: 'missing_count',
      key: 'missing_count',
      width: 100,
      render: (count: number) => (
        <Tag color="warning">{count}人</Tag>
      ),
      sorter: (a: QuestionStats, b: QuestionStats) => b.missing_count - a.missing_count
    },
    {
      title: '正确率',
      dataIndex: 'accuracy_rate',
      key: 'accuracy_rate',
      width: 150,
      render: (rate: number) => (
        <Progress 
          percent={rate} 
          size="small"
          status={rate >= 80 ? 'success' : rate >= 60 ? 'active' : 'exception'}
          format={(percent) => `${percent}%`}
        />
      ),
      sorter: (a: QuestionStats, b: QuestionStats) => b.accuracy_rate - a.accuracy_rate
    }
  ];

  const renderSummaryStats = () => {
    if (questionStats.length === 0) return null;

    const avgAccuracy = questionStats.reduce((sum, q) => sum + q.accuracy_rate, 0) / questionStats.length;
    const hardestQuestion = questionStats.reduce((min, q) => q.accuracy_rate < min.accuracy_rate ? q : min);
    const highAccuracyCount = questionStats.filter(q => q.accuracy_rate >= 80).length;
    const lowAccuracyCount = questionStats.filter(q => q.accuracy_rate < 60).length;

    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic 
              title="平均正确率" 
              value={avgAccuracy} 
              precision={1}
              suffix="%" 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="高正确率题目" 
              value={highAccuracyCount}
              suffix={`题 (≥80%)`}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="低正确率题目" 
              value={lowAccuracyCount}
              suffix={`题 (<60%)`}
            />
          </Col>
          <Col span={6}>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>最难题目</Text><br />
              <Text strong>第{hardestQuestion.question_number}题 ({hardestQuestion.accuracy_rate}%)</Text>
            </div>
          </Col>
        </Row>
      </Card>
    );
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Card 
      title={
        <Space>
          <BarChartOutlined style={{ color: '#1890ff' }} />
          <span>题目答题分析</span>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      {gradeResults.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          <FileSearchOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <div>请先批改学生答题卡，获取答题数据后再分析题目表现</div>
        </div>
      ) : (
        <>
          {questionStats.length === 0 && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Button 
                type="primary" 
                icon={<BarChartOutlined />}
                onClick={handleAnalyze}
                loading={loading}
                size="large"
              >
                {loading ? '正在分析...' : '开始分析题目表现'}
              </Button>
              <p style={{ marginTop: 12, color: '#666' }}>
                将分析每道题的答题情况和正确率
              </p>
            </div>
          )}

          {questionStats.length > 0 && (
            <>
              <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Title level={5} style={{ margin: 0 }}>
                  题目表现统计 (共{totalStudents}名学生，{questionStats.length}道题目)
                </Title>
                <Button 
                  icon={<BarChartOutlined />}
                  onClick={handleAnalyze}
                  loading={loading}
                >
                  重新分析
                </Button>
              </div>

              {renderSummaryStats()}

              <Table
                columns={columns}
                dataSource={questionStats.map((item, index) => ({ 
                  ...item, 
                  key: index 
                }))}
                pagination={{ 
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                }}
                size="small"
                scroll={{ x: 700 }}
              />
            </>
          )}
        </>
      )}
    </Card>
  );
};

export default QuestionPerformance;