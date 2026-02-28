#!/usr/bin/env python3
"""
AgentMesh 端到端演示
启动服务器并测试所有功能
"""

import asyncio
import sys
import os
import httpx
import json
from uuid import uuid4
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🚀 AgentMesh 端到端演示")
print("=" * 70)

async def main():
    # 1. 启动服务器
    print("\n1. 🚀 启动AgentMesh服务器...")
    
    from agentmesh.api.server import create_server
    
    # 创建服务器实例（使用不同端口避免冲突）
    server = create_server(host="127.0.0.1", port=8080, debug=True)
    
    # 在后台启动服务器
    import threading
    
    def run_server():
        import uvicorn
        uvicorn.run(server.app, host="127.0.0.1", port=8080, log_level="info")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("   ✅ 服务器启动中...")
    time.sleep(3)  # 等待服务器启动
    
    # 2. 测试API
    print("\n2. 📡 测试API端点...")
    
    base_url = "http://127.0.0.1:8080/api/v1"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 2.1 健康检查
            print("   a) 健康检查...")
            response = await client.get("http://127.0.0.1:8080/health")
            if response.status_code == 200:
                print(f"      ✅ 服务器健康: {response.json()}")
            else:
                print(f"      ❌ 健康检查失败: {response.status_code}")
                return
            
            # 2.2 生成密钥对
            print("\n   b) 生成密钥对...")
            response = await client.post(f"{base_url}/security/keypair")
            if response.status_code == 200:
                keypair = response.json()
                print(f"      ✅ 密钥对生成成功")
                private_key = keypair["private_key"]
                public_key = keypair["public_key"]
            else:
                print(f"      ❌ 密钥对生成失败: {response.status_code}")
                return
            
            # 2.3 数据签名
            print("\n   c) 数据签名...")
            test_data = "Hello AgentMesh!"
            sign_payload = {
                "data": test_data,
                "private_key": private_key,
                "algorithm": "ed25519"
            }
            response = await client.post(f"{base_url}/security/sign", json=sign_payload)
            if response.status_code == 200:
                signature = response.json()["signature"]
                print(f"      ✅ 数据签名成功")
            else:
                print(f"      ❌ 签名失败: {response.status_code}")
                return
            
            # 2.4 验证签名
            print("\n   d) 验证签名...")
            verify_payload = {
                "data": test_data,
                "signature": signature,
                "public_key": public_key,
                "algorithm": "ed25519"
            }
            response = await client.post(f"{base_url}/security/verify", json=verify_payload)
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ 签名验证: {'通过' if result['data']['valid'] else '失败'}")
            else:
                print(f"      ❌ 验证失败: {response.status_code}")
                return
            
            # 2.5 注册Agent
            print("\n   e) 注册Agent...")
            agent_id = f"weather-bot-{uuid4().hex[:8]}"
            agent_data = {
                "id": agent_id,
                "name": "WeatherBot",
                "version": "1.0.0",
                "description": "天气查询服务",
                "skills": [
                    {"name": "get_weather", "description": "获取天气"},
                    {"name": "get_forecast", "description": "获取预报"}
                ],
                "endpoint": "http://localhost:8001/weather",
                "protocol": "http",
                "tags": ["weather", "api", "public"],
                "health_status": "healthy"
            }
            
            response = await client.post(f"{base_url}/agents", json=agent_data)
            if response.status_code == 201:
                result = response.json()
                print(f"      ✅ Agent注册成功: {result['agent_id']}")
            else:
                print(f"      ❌ Agent注册失败: {response.status_code}")
                print(f"      错误信息: {response.text}")
                return
            
            # 2.6 获取Agent信息
            print("\n   f) 获取Agent信息...")
            response = await client.get(f"{base_url}/agents/{agent_id}")
            if response.status_code == 200:
                agent_info = response.json()
                print(f"      ✅ Agent信息获取成功")
                print(f"      名称: {agent_info['name']}")
                print(f"      技能: {[s['name'] for s in agent_info['skills']]}")
                print(f"      端点: {agent_info['endpoint']}")
            else:
                print(f"      ❌ 获取Agent信息失败: {response.status_code}")
                return
            
            # 2.7 发现Agent
            print("\n   g) 发现Agent...")
            response = await client.get(f"{base_url}/discover?skill=get_weather")
            if response.status_code == 200:
                agents = response.json()["agents"]
                print(f"      ✅ 发现 {len(agents)} 个天气Agent")
                for agent in agents:
                    print(f"      - {agent['name']}: {agent['description']}")
            else:
                print(f"      ❌ 发现Agent失败: {response.status_code}")
                return
            
            # 2.8 获取统计信息
            print("\n   h) 获取统计信息...")
            response = await client.get(f"{base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"      ✅ 统计信息:")
                print(f"      总Agent数: {stats['total_agents']}")
                print(f"      总技能数: {stats['total_skills']}")
                print(f"      健康Agent数: {stats['healthy_agents']}")
            else:
                print(f"      ❌ 获取统计信息失败: {response.status_code}")
                return
            
            # 2.9 注销Agent
            print("\n   i) 注销Agent...")
            response = await client.delete(f"{base_url}/agents/{agent_id}")
            if response.status_code == 200:
                print(f"      ✅ Agent注销成功")
            else:
                print(f"      ❌ Agent注销失败: {response.status_code}")
                return
            
            # 2.10 再次获取统计信息
            print("\n   j) 验证注销...")
            response = await client.get(f"{base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"      ✅ 注销后统计:")
                print(f"      总Agent数: {stats['total_agents']} (应为0)")
            else:
                print(f"      ❌ 获取统计信息失败: {response.status_code}")
                return
            
            print("\n" + "=" * 70)
            print("🎉 所有API测试通过！")
            print("=" * 70)
            
        except httpx.ConnectError:
            print("   ❌ 无法连接到服务器，请确保服务器已启动")
        except Exception as e:
            print(f"   ❌ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 3. 显示API文档地址
    print("\n3. 📚 API文档:")
    print(f"   Swagger UI: http://127.0.0.1:8080/docs")
    print(f"   ReDoc: http://127.0.0.1:8080/redoc")
    
    print("\n4. 🎯 使用示例:")
    print("   # 注册Agent")
    print(f'   curl -X POST {base_url}/agents \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"id": "my-agent", "name": "MyAgent", "version": "1.0.0", "description": "我的Agent"}\'')
    
    print("\n   # 发现Agent")
    print(f'   curl "{base_url}/discover?skill=get_weather"')
    
    print("\n" + "=" * 70)
    print("🌟 AgentMesh 演示完成！")
    print("=" * 70)
    
    # 保持服务器运行一段时间
    print("\n服务器将在30秒后自动关闭...")
    time.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
