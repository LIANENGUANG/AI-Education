import React, { useState } from 'react';
import { ReadOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Layout, Menu, theme, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import EnglishExamList from './components/english/ExamList';

const { Header, Content } = Layout;

const items1: MenuProps['items'] = [{
  key: 'english',
  label: 'English',
}];

const App: React.FC = () => {
  const [selectedKeys, setSelectedKeys] = useState<string[]>(['english']);
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const handleMenuClick = ({ key }: { key: string }) => {
    setSelectedKeys([key]);
  };

  const renderContent = () => {
    const selectedKey = selectedKeys[0];
    switch (selectedKey) {
      case 'english':
        return <EnglishExamList />;
      default:
        return <div><h2>欢迎使用 AI Education</h2><p>English 学习系统</p></div>;
    }
  };

  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', paddingLeft: 20 }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold',
          marginRight: 40
        }}>
          <ReadOutlined style={{ fontSize: '24px', marginRight: '8px' }} />
          AI Education
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={selectedKeys}
          onClick={handleMenuClick}
          items={items1}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Layout style={{ padding: '24px' }}>
        <Content
          style={{
            padding: 24,
            margin: 0,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          {renderContent()}
        </Content>
      </Layout>
      </Layout>
    </ConfigProvider>
  );
};

export default App;
