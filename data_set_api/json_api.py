from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# 配置文件路径
DATA_FILE = '全部维修记录.json'

# 基本权限验证
API_KEY = 'default_key'

@app.route('/api/json', methods=['GET'])
def get_json():
    # 验证API_KEY
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # 添加文件存在性检查
        if not os.path.exists(DATA_FILE):
            return jsonify({'error': 'File not found'}), 404
            
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return jsonify(data)
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET', 'POST'])
def status_check():
    return jsonify({'status': '运行中'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)