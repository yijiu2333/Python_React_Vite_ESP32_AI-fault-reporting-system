from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
from datetime import datetime
import requests
from openai import OpenAI, APIError
from threading import Thread, Lock
import os


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*" , async_mode='threading')  # 允许跨域

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), 
                base_url="https://api.deepseek.com")

connected_clients = {}

# 设备列表，用于在线程触发时锁定id，防止重复报修
devicelist = {}

# 创建一个线程锁对象
device_id_lock = Lock()

# 启动DeepSeek API调用
def analyze_with_deepseek(data, device, device_id):
    """
    调用DeepSeek API并流式返回结果
    """
    try:
        # 1. 优化序列化
        data_text = json.dumps(
            data,
            separators=(',', ':'),
            ensure_ascii=False
        )
        
        # 2. 构造紧凑消息
        content = f"设备{device}数据：{data_text}"

        # 你是高级电气及机械工程师，请基于以下设备维修记录，按以下模板严格生成Markdown格式报告，包含量化指标和安全警示：
        structured_prompt = f"""
        你是高级电气及机械工程师，请基于以下设备维修记录，按以下模板生成结构化维护建议：
        
        设备维修预测及相关优化建议
        
        一、历史故障数据分析
        1.1 高频故障类型
        - XX故障（占比xx%）
        - 主要表现：[具体现象]
        - 原因分析：[具体原因]
        - 维修方案：[具体措施]
        - 备件替换（如果有）：[名称及数量]
        
        二、故障预测与预防措施
        2.1 关键部件寿命预测
         部件名称        平均寿命    剩余寿命预测 
         [部件1]         [x个月]    [剩余x-x个月]
        
        2.2 预防性维护建议
        1. 系统分类
        - [具体措施]（[执行标准]）
        
        三、现场作业规范提醒
        3.1 安全操作重点
        ⚠️ 高危操作警示：
        - [具体安全要求]（[技术参数]）
        
        四、优化维保方案
        1. 管理改进
        - [具体方案]（[实施标准]）
        
        > 安全提示：
        """

        # 创建流式响应
        stream = client.chat.completions.create(
            model='deepseek-chat',
            messages=[
                {
                    'role': 'system', 
                    'content': structured_prompt
                },
                {
                    'role': 'user', 
                    'content': device + content
                }
            ],
            temperature=0.3,
            stream=True
        )
            
        # 流式处理每个chunk
        for chunk in stream:
            # 安全获取delta对象
            if not chunk.choices:
                continue
        
            # 获取第一个choice的delta
            delta = chunk.choices[0].delta
            
            # 安全获取content
            content = delta.content if delta and delta.content else ''

            socketio.emit('deepseek_stream', {
                'id': device_id,
                'content': content,
                'completed': False
            })
                
        # 发送完成标记
        socketio.emit('deepseek_stream', {
            'id': device_id,
            'content': None,
            'completed': True
        })
        
    except requests.exceptions.ConnectionError:
        socketio.emit('deepseek_stream', {
            'id': device_id,
            'content': '\n错误: 网络连接中断',
            'completed': True
        })

    except Exception as e:
        error_msg = f'\n错误: {str(e)}'
        if isinstance(e, APIError):  # 新版检测方式
            error_msg = f'\nAPI错误: {str(e)}'
        elif 'Connection' in str(e):
            error_msg = '\n网络连接失败，请检查服务器状态'

        socketio.emit('deepseek_stream', {
            'id': device_id,
            'content': error_msg,
            'completed': True
        })

    except Exception as e:
        print(f'DeepSeek API调用出错: {str(e)}')
        socketio.emit('deepseek_stream', {
            'id': device_id,
            'content': f'\n错误: {str(e)}',
            'completed': True
        })
    

# API配置
API_HOST = "http://192.168.0.70:3002"
API_KEY = 'default_key'  # 使用与服务器相同的API密钥

def get_data_from_api():
    """
    从API获取JSON数据
    """
    url = f"{API_HOST}/api/json"
    headers = {
        "X-API-KEY": API_KEY
    }
    
    try:
        # 发起GET请求
        response = requests.get(url, headers=headers)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 返回JSON数据
            return response.json()
        else:
            # 如果API返回错误，抛出异常
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # 处理请求错误
        print(f"API调用失败: {e}")
        return None

# 使用函数获取数据
data = get_data_from_api()

if data:
    print("成功获取数据")
else:
    print("未能获取数据")

def filter_data(device):
    messages = []
    for i in data:
        if device in i:
            messages += data[i]
    return messages

# 基本权限验证
API_KEY = 'default_key'

# 接收 ESP32 数据的端点
@app.route('/espdata', methods=['POST'])
def receive_esp_data():
    try:
        # 获取表单数据
        message = request.form.get('message', '')
        print(f"收到设备请求: {message}")
        messagelist = message.split(',')
        device_id = messagelist[0]
        device = messagelist[1]
        work_center = messagelist[2]
        line  = messagelist[3]
        mac_address = messagelist[4]
        
        # 获取最新数据
        latest_data = filter_data(device)
        print(f"最新数据来自mac地址: {mac_address}")

        # 使用锁来确保对 processing_devices 字典的访问是线程安全的
        with device_id_lock:
            if device_id in devicelist:
                # 如果设备 ID 已经在处理中，返回特定响应
                print(f"设备 {device_id} 正在处理中，丢弃新请求")
                return jsonify({"status": "pending", "message": "设备数据正在处理中"}), 202
            
            # 将设备 ID 添加到字典中，表示正在处理
            devicelist[device_id] = True
        
        # 获取最新数据
        latest_data = filter_data(device)
        print(f"最新数据: {line}")
        
        # 通过Socket.IO推送给所有客户端
        socketio.emit('data_update', {
            'id': device_id,
            'device': device,
            'work_center': work_center,
            'line': line,
            'data': latest_data
        })

        # 启动DeepSeek分析的线程
        thread = Thread(target=analyze_with_deepseek, args=(latest_data, device, device_id))
        thread.start()
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
# http://192.168.20.14:3001/end_work_order
@app.route('/end_work_order', methods=['POST'])
def end_work_order():
    try:
        # 解析请求体中的JSON数据
        data = request.get_json()
        
        # 检查是否包含deviceId字段
        if 'deviceId' not in data:
            return jsonify({"error": "Missing deviceId in request body"}), 400
        
        # 获取deviceId
        device_id = data['deviceId']
        print(f"Received device ID: {device_id}")
        
        # 删除后对应删除，确保释放锁并从字典中移除设备 ID
        with device_id_lock:
            if device_id in devicelist:
                del devicelist[device_id]
                print(f"设备 {device_id} 已解锁")
        
        return jsonify({"status": "success", "message": f"Work order for device {device_id} ended"}), 200
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/status', methods=['GET', 'POST'])
def status_check():
    return jsonify({'status': '运行中'}), 200

# WebSocket连接事件处理
@socketio.on('connect')
def handle_connect():
    print(f'客户端已连接: {request.sid}')
    connected_clients[request.sid] = {'timestamp': datetime.now()}
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'客户端断开: {request.sid}')
    if request.sid in connected_clients:
        del connected_clients[request.sid]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3001, debug=True)