import React from 'react';
import { Card, Row, Col, Tag, Typography, Space, Divider } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface Question {
  question_number: number;
  correct_answer: string;
}

interface ReadingPassage {
  passage_title: string;
  questions: Question[];
}

interface LanguagePassage {
  questions: Question[];
}

interface AnalysisData {
  grammar_questions: Question[];
  reading_questions: ReadingPassage[];
  language_use_questions: LanguagePassage[];
}

interface AnswerSummaryProps {
  analysisData: AnalysisData;
  documentTitle?: string;
}

const AnswerSummary: React.FC<AnswerSummaryProps> = ({ analysisData, documentTitle }) => {
  // 提取所有答案并按题号排序
  const extractAllAnswers = () => {
    const allAnswers: { questionNumber: number; answer: string; type: string; section?: string }[] = [];
    
    // 语法题答案
    analysisData.grammar_questions?.forEach(q => {
      allAnswers.push({
        questionNumber: q.question_number,
        answer: q.correct_answer,
        type: '语法题'
      });
    });

    // 阅读题答案
    analysisData.reading_questions?.forEach(passage => {
      passage.questions?.forEach(q => {
        allAnswers.push({
          questionNumber: q.question_number,
          answer: q.correct_answer,
          type: '阅读题',
          section: `阅读${passage.passage_title}`
        });
      });
    });

    // 语言运用题答案
    analysisData.language_use_questions?.forEach(passage => {
      passage.questions?.forEach(q => {
        allAnswers.push({
          questionNumber: q.question_number,
          answer: q.correct_answer,
          type: '语言运用题'
        });
      });
    });

    // 按题号排序
    return allAnswers.sort((a, b) => a.questionNumber - b.questionNumber);
  };

  const allAnswers = extractAllAnswers();

  // 按类型分组显示
  const renderAnswersByType = () => {
    const grammarAnswers = allAnswers.filter(a => a.type === '语法题');
    const readingAnswers = allAnswers.filter(a => a.type === '阅读题');
    const languageAnswers = allAnswers.filter(a => a.type === '语言运用题');

    return (
      <Row gutter={[16, 16]}>
        {grammarAnswers.length > 0 && (
          <Col span={8}>
            <Card size="small" title={<><span style={{color: '#52c41a'}}>语法题答案</span></>}>
              <Space wrap>
                {grammarAnswers.map(answer => (
                  <Tag key={answer.questionNumber} color="green">
                    {answer.questionNumber}. {answer.answer}
                  </Tag>
                ))}
              </Space>
            </Card>
          </Col>
        )}
        
        {readingAnswers.length > 0 && (
          <Col span={8}>
            <Card size="small" title={<><span style={{color: '#1890ff'}}>阅读题答案</span></>}>
              <Space wrap>
                {readingAnswers.map(answer => (
                  <Tag key={answer.questionNumber} color="blue">
                    {answer.questionNumber}. {answer.answer}
                  </Tag>
                ))}
              </Space>
            </Card>
          </Col>
        )}
        
        {languageAnswers.length > 0 && (
          <Col span={8}>
            <Card size="small" title={<><span style={{color: '#722ed1'}}>语言运用题答案</span></>}>
              <Space wrap>
                {languageAnswers.map(answer => (
                  <Tag key={answer.questionNumber} color="purple">
                    {answer.questionNumber}. {answer.answer}
                  </Tag>
                ))}
              </Space>
            </Card>
          </Col>
        )}
      </Row>
    );
  };


  if (!analysisData || allAnswers.length === 0) {
    return null;
  }

  return (
    <Card 
      title={
        <Space>
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
          <span>标准答案汇总</span>
          {documentTitle && <Text type="secondary">- {documentTitle}</Text>}
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      {renderAnswersByType()}
    </Card>
  );
};

export default AnswerSummary;