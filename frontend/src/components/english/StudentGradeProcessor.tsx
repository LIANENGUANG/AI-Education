import React, { useState } from 'react';
import { Card, Upload, Button, message, Table, Tag, Statistic, Row, Col, Progress, Collapse, Space, Typography } from 'antd';
import { UploadOutlined, FileSearchOutlined, CheckCircleOutlined, CloseCircleOutlined, MinusCircleOutlined, UserOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import StudentAnalysis from './StudentAnalysis';
import QuestionPerformance from './QuestionPerformance';
import { API_BASE_URL } from '../../config/api';

const { Panel } = Collapse;
const { Title, Text } = Typography;

interface StudentGradeProcessorProps {
  standardAnswers?: any;
  documentTitle?: string;
}

interface StudentResult {
  name: string;
  answers: { [key: number]: string };
  correct_count: number;
  wrong_count: number;
  missing_count: number;
  score: number;
  details: { [key: number]: any };
}

interface GradeStatistics {
  total_students: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  pass_rate: number;
  score_distribution: { [key: string]: number };
  total_questions: number;
}

const StudentGradeProcessor: React.FC<StudentGradeProcessorProps> = ({ 
  standardAnswers, 
  documentTitle 
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [gradeResults, setGradeResults] = useState<StudentResult[]>([]);
  const [statistics, setStatistics] = useState<GradeStatistics | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<StudentResult | null>(null);

  const handleAnswerSheetUpload = async (file: File) => {
    if (!standardAnswers) {
      message.error('请先分析试卷获取标准答案');
      return false;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('answer_sheet', file);
      formData.append('standard_answers', JSON.stringify(standardAnswers));

      message.loading('正在解析答题卡...', 0);

      const response = await fetch(`${API_BASE_URL}/api/english/documents/grade_answer_sheet/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('答题卡处理失败');
      }

      const result = await response.json();
      message.destroy();
      
      if (result.error) {
        message.error(result.error);
        return false;
      }

      message.success(`成功批改 ${result.parse_result.total_students} 名学生的答题卡`);
      
      setGradeResults(result.grade_result.graded_results);
      setStatistics(result.grade_result.statistics);

    } catch (error) {
      message.destroy();
      message.error(error instanceof Error ? error.message : '处理失败');
    }

    setIsUploading(false);
    return false;
  };

  const uploadProps: UploadProps = {
    name: 'answer_sheet',
    multiple: false,
    accept: '.docx,.pdf,.txt',
    beforeUpload: handleAnswerSheetUpload,
    showUploadList: false,
  };

  const studentColumns: ColumnsType<StudentResult> = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 100,
    },
    {
      title: '得分',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score: number) => (
        <Text strong style={{ color: score >= 60 ? '#52c41a' : '#ff4d4f' }}>
          {score}分
        </Text>
      ),
      sorter: (a: StudentResult, b: StudentResult) => b.score - a.score,
    },
    {
      title: '正确',
      dataIndex: 'correct_count',
      key: 'correct_count',
      width: 80,
      render: (count: number) => (
        <Tag icon={<CheckCircleOutlined />} color="success">
          {count}题
        </Tag>
      ),
    },
    {
      title: '错误',
      dataIndex: 'wrong_count',
      key: 'wrong_count',
      width: 80,
      render: (count: number) => (
        <Tag icon={<CloseCircleOutlined />} color="error">
          {count}题
        </Tag>
      ),
    },
    {
      title: '未答',
      dataIndex: 'missing_count',
      key: 'missing_count',
      width: 80,
      render: (count: number) => (
        <Tag icon={<MinusCircleOutlined />} color="warning">
          {count}题
        </Tag>
      ),
    },
    {
      title: '答题率',
      key: 'completion_rate',
      width: 100,
      render: (record: StudentResult) => {
        const total = statistics?.total_questions || 0;
        const completed = total - record.missing_count;
        const rate = total > 0 ? (completed / total * 100) : 0;
        return (
          <Progress 
            percent={Math.round(rate)} 
            size="small" 
            status={rate >= 90 ? 'success' : rate >= 70 ? 'active' : 'exception'}
          />
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (record: StudentResult) => (
        <Button
          type="link"
          size="small"
          icon={<UserOutlined />}
          onClick={() => setSelectedStudent(record)}
        >
          AI分析
        </Button>
      ),
    },
  ];

  const renderScoreDistribution = () => {
    if (!statistics) return null;

    return (
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Statistic title="总人数" value={statistics.total_students} />
        </Col>
        <Col span={6}>
          <Statistic 
            title="平均分" 
            value={statistics.average_score} 
            precision={1}
            suffix="分" 
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="及格率" 
            value={statistics.pass_rate} 
            precision={1}
            suffix="%" 
          />
        </Col>
        <Col span={6}>
          <Statistic title="最高分" value={statistics.highest_score} suffix="分" />
        </Col>
      </Row>
    );
  };

  const renderDistributionChart = () => {
    if (!statistics) return null;

    const { score_distribution } = statistics;
    const ranges = ['90-100', '80-89', '70-79', '60-69', '0-59'];
    const colors = ['#52c41a', '#1890ff', '#faad14', '#ff7a45', '#ff4d4f'];

    return (
      <div style={{ marginTop: 16 }}>
        <Title level={5}>分数分布</Title>
        {ranges.map((range, index) => {
          const count = score_distribution[range] || 0;
          const percentage = statistics.total_students > 0 ? 
            (count / statistics.total_students * 100) : 0;
          
          return (
            <div key={range} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span>{range}分</span>
                <span>{count}人 ({percentage.toFixed(1)}%)</span>
              </div>
              <Progress 
                percent={percentage} 
                showInfo={false}
                strokeColor={colors[index]}
                size="small"
              />
            </div>
          );
        })}
      </div>
    );
  };

  if (!standardAnswers) {
    return (
      <Card 
        title={
          <Space>
            <FileSearchOutlined style={{ color: '#faad14' }} />
            <span>学生答题卡批改</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          <FileSearchOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <div>请先上传并分析试卷，获取标准答案后再批改学生答题卡</div>
        </div>
      </Card>
    );
  }

  return (
    <Card 
      title={
        <Space>
          <FileSearchOutlined style={{ color: '#1890ff' }} />
          <span>学生答题卡批改</span>
          {documentTitle && <Text type="secondary">- {documentTitle}</Text>}
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      {/* 上传区域 */}
      {gradeResults.length === 0 && (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Upload {...uploadProps}>
            <Button 
              type="primary" 
              icon={<UploadOutlined />}
              size="large"
              loading={isUploading}
            >
              {isUploading ? '正在批改中...' : '上传学生答题卡'}
            </Button>
          </Upload>
          <p style={{ marginTop: 12, color: '#666' }}>
            支持 Word(.docx)、PDF(.pdf)、文本(.txt) 格式，将自动解析学生答案并批改
          </p>
        </div>
      )}

      {/* 批改结果 */}
      {gradeResults.length > 0 && statistics && (
        <>
          {/* 统计信息 */}
          <div style={{ marginBottom: 24 }}>
            {renderScoreDistribution()}
            {renderDistributionChart()}
          </div>

          {/* 题目分析 */}
          <QuestionPerformance 
            gradeResults={gradeResults}
            isVisible={true}
          />

          {/* 详细成绩表 */}
          <Collapse defaultActiveKey={['students']} ghost>
            <Panel header={`学生成绩详情 (${gradeResults.length}人)`} key="students">
              <Table
                columns={studentColumns}
                dataSource={gradeResults.map((student, index) => ({ 
                  ...student, 
                  key: index 
                }))}
                pagination={{ pageSize: 10 }}
                size="small"
                scroll={{ x: 600 }}
              />
            </Panel>
          </Collapse>

          {/* 重新上传按钮 */}
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />} loading={isUploading}>
                重新上传答题卡
              </Button>
            </Upload>
          </div>
        </>
      )}

      {/* 学生分析弹窗 */}
      {selectedStudent && (
        <StudentAnalysis
          student={selectedStudent}
          standardAnswers={standardAnswers}
          onClose={() => setSelectedStudent(null)}
        />
      )}
    </Card>
  );
};

export default StudentGradeProcessor;