#!/usr/bin/env python3
"""
AgentMesh 简单演示（修复版）
展示核心功能
"""

import asyncio
import sys
import os
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType, HealthStatus
from agentmesh.core.registry import AgentRegistry


async def main():
    print("🚀 AgentMesh 简单演示（修复版）")
    print("=" * 50)
    
    # 1. 创建注册中心
    print("\n1. 创建Agent注册中心...")
    registry = AgentRegistry()
    await registry.start()
    
    # 2. 创建示例Agent
    print("\n2. 创建示例Agent...")
    
    # 天气Agent
    weather_agent = AgentCard(
        id=f"weather-{uuid4().hex[:8]}",
        name="WeatherBot",
        version="1.0.0",
        description="天气查询服务",
        skills=[
            Skill(name="get_weather", description="获取天气"),
            Skill(name="get_forecast", description="获取预报")
        ],
        endpoint="http://localhost:8001/weather",
        protocol=ProtocolType.HTTP,
        tags=["weather", "api"],
        health_status=HealthStatus.HEALTHY
    )
    
    # 翻译Agent
    translation_agent = AgentCard(
        id=f"translate-{uuid4().hex[:8]}",
        name="TranslationBot",
        version="1.0.0",
        description="翻译服务",
        skills=[
            Skill(name="translate_text", description="翻译文本"),
            Skill(name="detect_language", description="检测语言")
        ],
        endpoint="http://localhost:8002/translate",
        protocol=ProtocolType.HTTP,
        tags=["translation", "nlp"],
        health_status=HealthStatus.HEALTHY
    )
    
    # 3. 注册Agent
    print("\n3. 注册Agent...")
    
    try:
        agent1_id = await registry.register_agent(weather_agent)
        print(f"   ✅ 注册: {weather_agent.name}")
        
        agent2_id = await registry.register_agent(translation_agent)
        print(f"   ✅ 注册: {translation_agent.name}")
    except Exception as e:
        print(f"   ❌ 注册失败: {e}")
        return
    
    # 4. 显示状态
    print("\n4. 注册中心状态:")
    stats = registry.get_stats()
    print(f"   总Agent数: {stats['total_agents']}")
    print(f"   总技能数: {stats['total_skills']}")
    
    # 5. 查找Agent
    print("\n5. 查找Agent:")
    
    # 按技能查找
    print("   a) 查找天气技能:")
    agents = await registry.discover_agents(skill_name="get_weather")
    for agent in agents:
        print(f"      - {agent.name}: {agent.description}")
    
    # 按标签查找（修复：使用tags而不是tag）
    print("\n   b) 查找NLP标签:")
    agents = await registry.discover_agents(tags=["nlp"])
    for agent in agents:
        print(f"      - {agent.name}: 标签: {', '.join(agent.tags or [])}")
    
    # 6. 获取Agent详情
    print("\n6. Agent详情:")
    agent = await registry.get_agent(agent1_id)
    if agent:
        print(f"   名称: {agent.name}")
        print(f"   技能: {', '.join([s.name for s in agent.skills])}")
        print(f"   端点: {agent.endpoint}")
        print(f"   状态: {agent.health_status}")
    
    # 7. 注销Agent
    print("\n7. 注销Agent:")
    success = await registry.deregister_agent(agent2_id)
    if success:
        print(f"   ✅ 注销: {translation_agent.name}")
        stats = registry.get_stats()
        print(f"   剩余Agent数: {stats['total_agents']}")
    
    # 8. 停止
    print("\n8. 停止注册中心...")
    await registry.stop()
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    # 激活虚拟环境
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if os.path.exists(venv_path):
        print(f"使用虚拟环境: {venv_path}")
    
    # 运行演示
    asyncio.run(main())
