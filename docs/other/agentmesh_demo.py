#!/usr/bin/env python3
"""
AgentMesh协议演示脚本
展示机器可读协议的实际使用
"""

import json
import time
from datetime import datetime
import requests
from typing import Dict, List, Any

class AgentMeshDemo:
    """AgentMesh协议演示类"""
    
    def __init__(self, agent_name: str = "demo-agent"):
        self.agent_name = agent_name
        self.agent_id = f"{agent_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.registry_url = "https://registry.agentmesh.net"  # 示例URL
        self.capabilities = []
        self.discovered_agents = []
        
    def create_registration_data(self) -> Dict[str, Any]:
        """创建Agent注册数据"""
        return {
            "agent": {
                "id": self.agent_id,
                "name": self.agent_name,
                "version": "1.0.0",
                "description": f"演示Agent: {self.agent_name}",
                "capabilities": [
                    {
                        "name": "file_operations",
                        "description": "文件操作演示",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/api/files/read",
                                "input_schema": {"path": "string"},
                                "output_schema": {"content": "string"}
                            }
                        ]
                    },
                    {
                        "name": "data_processing",
                        "description": "数据处理演示",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/api/process",
                                "input_schema": {"data": "array"},
                                "output_schema": {"result": "object"}
                            }
                        ]
                    }
                ],
                "metadata": {
                    "language": "zh-CN, en-US",
                    "timezone": "Asia/Shanghai",
                    "created": datetime.now().isoformat()
                },
                "network": {
                    "discovery_methods": [
                        {"dns_srv": "_agentmesh._tcp.agentmesh.net"},
                        {"mdns": "_agentmesh._tcp.local"}
                    ],
                    "communication": {
                        "protocols": ["http", "websocket"],
                        "encryption": "tls_1.3"
                    }
                }
            }
        }
    
    def create_heartbeat_data(self, status: str = "healthy") -> Dict[str, Any]:
        """创建心跳数据"""
        return {
            "heartbeat": {
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "metrics": {
                    "cpu_usage": "25%",
                    "memory_usage": "35%",
                    "uptime": f"{int(time.time() % 86400)}s"
                },
                "capabilities_status": {
                    "file_operations": "available",
                    "data_processing": "available"
                }
            }
        }
    
    def register_agent(self) -> bool:
        """注册Agent到网络"""
        print(f"[1/5] 注册Agent: {self.agent_id}")
        
        registration_data = self.create_registration_data()
        
        # 显示注册数据
        print("注册数据 (JSON格式):")
        print(json.dumps(registration_data, indent=2, ensure_ascii=False))
        
        # 在实际实现中，这里会发送HTTP请求
        # response = requests.post(
        #     f"{self.registry_url}/api/register",
        #     json=registration_data,
        #     headers={"Content-Type": "application/yaml"}
        # )
        
        print(f"✅ Agent {self.agent_id} 注册成功 (模拟)")
        return True
    
    def discover_agents(self, capability_filter: str = None) -> List[Dict[str, Any]]:
        """发现网络中的其他Agent"""
        print(f"[2/5] 发现网络中的Agent...")
        
        # 模拟发现结果
        self.discovered_agents = [
            {
                "id": "image-gen-001",
                "name": "image-generator",
                "description": "AI图像生成Agent",
                "capabilities": ["image_generation", "style_transfer"],
                "endpoints": [
                    {
                        "method": "POST",
                        "url": "https://image-gen.agentmesh.net/api/generate",
                        "input_schema": {"prompt": "string", "style": "string"}
                    }
                ]
            },
            {
                "id": "web-search-002",
                "name": "web-searcher",
                "description": "网络搜索Agent",
                "capabilities": ["web_search", "content_extraction"],
                "endpoints": [
                    {
                        "method": "POST",
                        "url": "https://search.agentmesh.net/api/search",
                        "input_schema": {"query": "string", "count": "number"}
                    }
                ]
            },
            {
                "id": "code-exec-003",
                "name": "code-executor",
                "description": "代码执行Agent",
                "capabilities": ["code_execution", "code_analysis"],
                "endpoints": [
                    {
                        "method": "POST",
                        "url": "https://code.agentmesh.net/api/execute",
                        "input_schema": {"code": "string", "language": "string"}
                    }
                ]
            }
        ]
        
        if capability_filter:
            filtered_agents = [
                agent for agent in self.discovered_agents
                if capability_filter in agent["capabilities"]
            ]
            print(f"找到 {len(filtered_agents)} 个具有 '{capability_filter}' 能力的Agent")
            return filtered_agents
        else:
            print(f"找到 {len(self.discovered_agents)} 个Agent")
            return self.discovered_agents
    
    def send_heartbeat(self) -> bool:
        """发送心跳"""
        print(f"[3/5] 发送心跳...")
        
        heartbeat_data = self.create_heartbeat_data()
        
        # 显示心跳数据
        print("心跳数据:")
        print(json.dumps(heartbeat_data, indent=2, ensure_ascii=False))
        
        # 在实际实现中，这里会发送HTTP请求
        # response = requests.post(
        #     f"{self.registry_url}/api/heartbeat",
        #     json=heartbeat_data
        # )
        
        print("✅ 心跳发送成功 (模拟)")
        return True
    
    def negotiate_capability(self, target_agent_id: str, capability: str) -> Dict[str, Any]:
        """协商能力使用"""
        print(f"[4/5] 与Agent {target_agent_id} 协商能力 '{capability}'...")
        
        negotiation_request = {
            "negotiation": {
                "request": {
                    "requester": self.agent_id,
                    "required_capability": capability,
                    "constraints": {
                        "latency": "<200ms",
                        "cost": "free",
                        "privacy": "standard"
                    }
                }
            }
        }
        
        print("协商请求:")
        print(json.dumps(negotiation_request, indent=2, ensure_ascii=False))
        
        # 模拟协商响应
        negotiation_response = {
            "negotiation": {
                "response": {
                    "provider": target_agent_id,
                    "capability": capability,
                    "terms": {
                        "rate_limit": "100 req/hour",
                        "authentication": "api_key",
                        "cost": "free_for_demo",
                        "endpoint": f"https://{target_agent_id}.agentmesh.net/api/{capability}"
                    }
                }
            }
        }
        
        print("协商响应:")
        print(json.dumps(negotiation_response, indent=2, ensure_ascii=False))
        
        print(f"✅ 能力 '{capability}' 协商成功")
        return negotiation_response
    
    def call_remote_capability(self, agent_info: Dict[str, Any], capability: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用远程Agent的能力"""
        print(f"[5/5] 调用Agent {agent_info['name']} 的能力 '{capability}'...")
        
        # 查找对应的端点
        endpoint = None
        for ep in agent_info.get("endpoints", []):
            if capability in ep.get("url", ""):
                endpoint = ep
                break
        
        if not endpoint:
            print(f"❌ 未找到能力 '{capability}' 的端点")
            return {"error": "Endpoint not found"}
        
        print(f"调用端点: {endpoint['method']} {endpoint['url']}")
        print(f"输入数据: {json.dumps(input_data, indent=2, ensure_ascii=False)}")
        
        # 模拟API调用响应
        if capability == "image_generation":
            response = {
                "result": {
                    "image_url": "https://agentmesh.net/generated/image-12345.png",
                    "generation_id": "img-12345",
                    "prompt": input_data.get("prompt", ""),
                    "size": input_data.get("size", "1024x1024"),
                    "processing_time": "2.5s"
                }
            }
        elif capability == "web_search":
            response = {
                "result": {
                    "query": input_data.get("query", ""),
                    "results": [
                        {
                            "title": "AgentMesh Protocol Documentation",
                            "url": "https://agentmesh.net/protocol",
                            "snippet": "Machine-readable protocol for AI agent networking"
                        },
                        {
                            "title": "AI Agent Collaboration Research",
                            "url": "https://arxiv.org/abs/agent-collab",
                            "snippet": "Recent advances in multi-agent systems"
                        }
                    ],
                    "total_results": 42
                }
            }
        else:
            response = {
                "result": {
                    "capability": capability,
                    "input": input_data,
                    "output": {"processed": True, "timestamp": datetime.now().isoformat()},
                    "agent": agent_info["name"]
                }
            }
        
        print("API响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        print(f"✅ 能力调用成功")
        return response
    
    def run_demo(self):
        """运行完整演示"""
        print("=" * 60)
        print("🤖 AgentMesh协议演示")
        print("=" * 60)
        
        # 1. 注册Agent
        self.register_agent()
        time.sleep(1)
        
        # 2. 发现其他Agent
        agents = self.discover_agents()
        time.sleep(1)
        
        # 3. 发送心跳
        self.send_heartbeat()
        time.sleep(1)
        
        # 4. 协商能力使用
        if agents:
            target_agent = agents[0]  # 选择第一个发现的Agent
            negotiation_result = self.negotiate_capability(
                target_agent["id"], 
                target_agent["capabilities"][0]
            )
            time.sleep(1)
            
            # 5. 调用远程能力
            if target_agent["capabilities"][0] == "image_generation":
                input_data = {
                    "prompt": "A cute robot cat helping with programming",
                    "style": "digital art",
                    "size": "1024x1024"
                }
            elif target_agent["capabilities"][0] == "web_search":
                input_data = {
                    "query": "AI agent collaboration protocols",
                    "count": 5
                }
            else:
                input_data = {"data": [1, 2, 3, 4, 5]}
            
            self.call_remote_capability(target_agent, target_agent["capabilities"][0], input_data)
        
        print("=" * 60)
        print("🎉 演示完成!")
        print("=" * 60)
        print("\n总结:")
        print(f"1. ✅ Agent注册: {self.agent_id}")
        print(f"2. ✅ 服务发现: 找到 {len(agents)} 个Agent")
        print(f"3. ✅ 心跳机制: 健康状态监控")
        print(f"4. ✅ 能力协商: 协议标准化")
        print(f"5. ✅ 远程调用: Agent间协作")
        print("\n这个演示展示了AgentMesh协议的核心功能:")
        print("- 机器可读的协议规范")
        print("- 自动服务发现")
        print("- 能力协商和调用")
        print("- 去中心化Agent网络")

def main():
    """主函数"""
    demo = AgentMeshDemo("nanobot-demo")
    demo.run_demo()
    
    # 显示协议文件信息
    print("\n📁 相关文件:")
    print("1. agentmesh_skill.md - 英文版协议文档 (evomap.ai风格)")
    print("2. agentmesh_skill_zh.md - 中文版协议文档")
    print("3. agentmesh_protocol_evomap_style.md - 详细协议文档")
    print("4. agentmesh_demo.py - 本演示脚本")
    
    print("\n🚀 下一步:")
    print("1. 查看协议文档: cat agentmesh_skill.md")
    print("2. 运行演示: python agentmesh_demo.py")
    print("3. 实现真实集成: 参考协议规范")

if __name__ == "__main__":
    main()