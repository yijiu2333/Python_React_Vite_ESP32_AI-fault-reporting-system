import { useState, useEffect } from 'react';
import DeviceOverviewCard from '../components/DeviceOverviewCard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import { io } from 'socket.io-client';

export default function Home() {
  const [streamData, setStreamData] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [device, setDevice] = useState('');
  const [time, setTime] = useState('');
  const [workCenter, setWorkCenter] = useState('');
  const [line, setLine] = useState('');
  const [maintenanceData, setMaintenanceData] = useState([]);


  useEffect(() => {
    // 连接Socket.IO服务器
    const socket = io('http://192.168.20.14:3001');//修改为后端地址
    
    socket.on('connect', () => {
      console.log('已连接到Socket.IO服务器');
    });

    // 在接收数据时处理特殊字符
    const cleanMarkdown = (raw) => {
      // 转义HTML标签
      let cleaned = raw.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      // 修复被分割的代码块
      cleaned = cleaned.replace(/(```[\s\S]*?)(?=```|$)/g, (match) => {
        if (!match.endsWith('```')) return match + '\n```';
        return match;
      });
      return cleaned;
    };

    // 监听DeepSeek流式输出
    socket.on('deepseek_stream', (data) => {
      if (!device) return; // 等待设备信息初始化
      if (data.device === device && data.content) {
        setStreamData(prev => prev + data.content);
      }
      if (data.completed) {
        setIsLoading(false);
      }
    });
    
    socket.on('data_update', (message) => {
      
      // 解构消息对象，获取所需的信息
      const { timestamp, device, work_center, line, data } = message;
      
      // 更新所有状态
      setTime(timestamp);
      setDevice(device);
      setWorkCenter(work_center);
      setLine(line);
      setMaintenanceData(data);
      setStreamData(''); // 清空之前的流数据
      setIsLoading(true); // 开始加载
      
      // 使用这些信息进行相应的处理
      console.log('Timestamp:', timestamp);
      console.log('Device:', device);
      console.log('Work Center:', work_center);
      console.log('Line:', line);
      console.log('Data:', data);
    });
    
    return () => {
      socket.disconnect();
    };
  }, [device]);

  return (
    <div className="grid-container">
      <h1>欢迎使用设备管理平台</h1>
      
      {(workCenter || line) && (
        <DeviceOverviewCard 
          timeData={time}
          deviceData={device}
          workCenterData={workCenter}
          lineData={line}
          maintenanceData={maintenanceData}
          aiAdvice={streamData ? [
            <ReactMarkdown
              key="ai-response"
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, rehypeHighlight]}
            >
              {streamData}
            </ReactMarkdown>
          ] : null}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
