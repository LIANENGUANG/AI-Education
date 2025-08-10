import React from 'react';
import { Form, Input, Button, Select, InputNumber } from 'antd';

const { Option } = Select;
const { TextArea } = Input;

const CreateExam: React.FC = () => {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Success:', values);
  };

  const onFinishFailed = (errorInfo: any) => {
    console.log('Failed:', errorInfo);
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <h2>创建英语考试</h2>
      <Form
        form={form}
        name="create-english-exam"
        labelCol={{ span: 6 }}
        wrapperCol={{ span: 18 }}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        autoComplete="off"
      >
        <Form.Item
          label="考试名称"
          name="name"
          rules={[{ required: true, message: '请输入考试名称!' }]}
        >
          <Input placeholder="请输入考试名称" />
        </Form.Item>

        <Form.Item
          label="考试描述"
          name="description"
        >
          <TextArea rows={4} placeholder="请输入考试描述" />
        </Form.Item>

        <Form.Item
          label="考试时长"
          name="duration"
          rules={[{ required: true, message: '请输入考试时长!' }]}
        >
          <InputNumber min={1} max={300} addonAfter="分钟" placeholder="120" />
        </Form.Item>

        <Form.Item
          label="考试类型"
          name="examType"
          rules={[{ required: true, message: '请选择考试类型!' }]}
        >
          <Select placeholder="请选择考试类型">
            <Option value="listening">听力测试</Option>
            <Option value="reading">阅读理解</Option>
            <Option value="writing">写作测试</Option>
            <Option value="comprehensive">综合测试</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="难度等级"
          name="difficulty"
          rules={[{ required: true, message: '请选择难度等级!' }]}
        >
          <Select placeholder="请选择难度等级">
            <Option value="easy">简单</Option>
            <Option value="medium">中等</Option>
            <Option value="hard">困难</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="总分"
          name="totalScore"
          rules={[{ required: true, message: '请输入总分!' }]}
        >
          <InputNumber min={1} max={200} addonAfter="分" placeholder="100" />
        </Form.Item>

        <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
          <Button type="primary" htmlType="submit" style={{ marginRight: 8 }}>
            创建考试
          </Button>
          <Button htmlType="button" onClick={() => form.resetFields()}>
            重置
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default CreateExam;