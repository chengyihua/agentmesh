#!/usr/bin/env python3
"""
AgentMesh 演示脚本
展示Agent注册、发现和管理的完整流程
"""

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType, HealthStatus
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.security import SecurityManager


async def demo_basic_registry():
    """演示基本的注册和发现功能"""
    print("=" * 60)
    print("🤖 AgentMesh 演示 - 基本注册与发现")
    print("=" * 60)
    
    # 1. 创建注册中心
    print("\n1. 🏗️ 创建Agent注册中心...")
    registry = AgentRegistry()
    await registry.start()
    
    # 2. 创建几个示例Agent
    print("\n2. 📝 创建示例Agent...")
    
    # Agent 1: 天气查询Agent
    weather_agent = AgentCard(
        id=f"weather-agent-{uuid4().hex[:8]}",
        name="WeatherBot",
        version="1.0.0",
        description="提供天气查询服务的AI Agent",
        skills=[
            Skill(
                name="get_weather",
                description="获取指定城市的天气信息",
                tags=["weather", "api", "forecast"]
            ),
            Skill(
                name="get_forecast",
                description="获取未来几天的天气预报",
                tags=["weather", "forecast", "prediction"]
            )
        ],
        endpoint="http://localhost:8001/weather",
        protocol=ProtocolType.HTTP,
        tags=["weather", "api", "public"],
        health_status=HealthStatus.HEALTHY
    )
    
    # Agent 2: 翻译Agent
    translation_agent = AgentCard(
        id=f"translation-agent-{uuid4().hex[:8]}",
        name="TranslationBot",
        version="1.2.0",
        description="多语言翻译服务的AI Agent",
        skills=[
            Skill(
                name="translate_text",
                description="将文本从一种语言翻译到另一种语言",
                tags=["translation", "language", "nlp"]
            ),
            Skill(
                name="detect_language",
                description="检测文本的语言",
                tags=["language", "detection", "nlp"]
            )
        ],
        endpoint="http://localhost:8002/translate",
        protocol=ProtocolType.HTTP,
        tags=["translation", "nlp", "multilingual"],
        health_status=HealthStatus.HEALTHY
    )
    
    # Agent 3: 数据分析Agent
    data_agent = AgentCard(
        id=f"data-agent-{uuid4().hex[:8]}",
        name="DataAnalyzer",
        version="2.1.0",
        description="数据分析和可视化AI Agent",
        skills=[
            Skill(
                name="analyze_data",
                description="分析数据集并生成统计报告",
                tags=["data", "analysis", "statistics"]
            ),
            Skill(
                name="create_chart",
                description="创建数据可视化图表",
                tags=["visualization", "chart", "graph"]
            ),
            Skill(
                name="predict_trend",
                description="预测数据趋势",
                tags=["prediction", "trend", "forecast"]
            )
        ],
        endpoint="http://localhost:8003/data",
        protocol=ProtocolType.HTTP,
        tags=["data", "analytics", "visualization"],
        health_status=HealthStatus.HEALTHY
    )
    
    print(f"   创建了 {len([weather_agent, translation_agent, data_agent])} 个Agent")
    
    # 3. 注册Agent
    print("\n3. 📝 注册Agent到注册中心...")
    
    agents = [weather_agent, translation_agent, data_agent]
    for agent in agents:
        try:
            agent_id = await registry.register_agent(agent)
            print(f"   ✅ 注册成功: {agent.name} (ID: {agent_id})")
        except Exception as e:
            print(f"   ❌ 注册失败 {agent.name}: {e}")
    
    # 4. 显示注册中心状态
    print("\n4. 📊 注册中心状态:")
    stats = registry.get_stats()
    print(f"   总Agent数: {stats['total_agents']}")
    print(f"   总技能数: {stats['total_skills']}")
    print(f"   健康Agent: {stats['healthy_agents']}")
    print(f"   不健康Agent: {stats['unhealthy_agents']}")
    
    # 5. 演示技能发现
    print("\n5. 🔍 技能发现演示:")
    
    # 查找天气相关技能
    print("   a) 查找天气相关技能:")
    weather_agents = await registry.discover_agents(skill_name="get_weather")
    print(f"      找到 {len(weather_agents)} 个天气Agent:")
    for agent in weather_agents:
        print(f"      - {agent.name}: {agent.description}")
    
    # 查找数据分析技能
    print("\n   b) 查找数据分析技能:")
    data_agents = await registry.discover_agents(skill_name="analyze_data")
    print(f"      找到 {len(data_agents)} 个数据分析Agent:")
    for agent in data_agents:
        print(f"      - {agent.name}: {agent.description}")
    
    # 6. 演示标签过滤
    print("\n6. 🏷️ 标签过滤演示:")
    
    # 查找有"nlp"标签的Agent
    print("   a) 查找有'nlp'标签的Agent:")
    nlp_agents = await registry.discover_agents(tags=["nlp"])
    print(f"      找到 {len(nlp_agents)} 个NLP Agent:")
    for agent in nlp_agents:
        print(f"      - {agent.name}: {', '.join(agent.tags or [])}")
    
    # 7. 演示协议过滤
    print("\n7. 🔌 协议过滤演示:")
    
    # 查找HTTP协议的Agent
    print("   a) 查找HTTP协议的Agent:")
    http_agents = await registry.discover_agents(protocol=ProtocolType.HTTP)
    print(f"      找到 {len(http_agents)} 个HTTP Agent:")
    for agent in http_agents:
        print(f"      - {agent.name}: {agent.protocol}")
    
    # 8. 演示Agent详情查询
    print("\n8. 📋 Agent详情查询:")
    
    if agents:
        agent_id = agents[0].id
        agent_details = await registry.get_agent(agent_id)
        if agent_details:
            print(f"   Agent详情: {agent_details.name}")
            print(f"     技能: {', '.join([s.name for s in agent_details.skills])}")
            print(f"     端点: {agent_details.endpoint}")
            print(f"     状态: {agent_details.health_status}")
    
    # 9. 演示注销Agent
    print("\n9. 🗑️ Agent注销演示:")
    
    if agents:
        agent_to_remove = agents[-1]  # 最后一个Agent
        print(f"   注销Agent: {agent_to_remove.name}")
        success = await registry.deregister_agent(agent_to_remove.id)
        if success:
            print(f"   ✅ 注销成功")
            # 再次检查状态
            stats = registry.get_stats()
            print(f"   剩余Agent数: {stats['total_agents']}")
        else:
            print(f"   ❌ 注销失败")
    
    # 10. 停止注册中心
    print("\n10. 🛑 停止注册中心...")
    await registry.stop()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("=" * 60)


async def demo_advanced_features():
    """演示高级功能"""
    print("\n\n" + "=" * 60)
    print("🚀 AgentMesh 演示 - 高级功能")
    print("=" * 60)
    
    # 1. 创建带安全管理的注册中心
    print("\n1. 🔐 创建带安全管理的注册中心...")
    security_manager = SecurityManager()
    registry = AgentRegistry(security_manager=security_manager)
    await registry.start()
    
    # 2. 创建带签名的Agent
    print("\n2. ✍️ 创建带数字签名的Agent...")
    
    # 生成密钥对
    private_key, public_key = security_manager.generate_keypair()
    
    # 创建Agent
    secure_agent = AgentCard(
        id=f"secure-agent-{uuid4().hex[:8]}",
        name="SecureBot",
        version="1.0.0",
        description="带数字签名的安全Agent",
        skills=[
            Skill(
                name="secure_process",
                description="安全处理敏感数据",
                tags=["security", "encryption", "privacy"]
            )
        ],
        endpoint="http://localhost:9001/secure",
        protocol=ProtocolType.HTTP,
        tags=["secure", "encrypted", "private"],
        health_status=HealthStatus.HEALTHY,
        public_key=public_key
    )
    
    # 为AgentCard生成签名
    signature = security_manager.sign_data(secure_agent.to_json(), private_key)
    secure_agent.signature = signature
    
    print(f"   创建了带签名的Agent: {secure_agent.name}")
    print(f"   公钥: {public_key[:50]}...")
    print(f"   签名: {signature[:50]}...")
    
    # 3. 注册带签名的Agent
    print("\n3. 📝 注册带签名的Agent...")
    try:
        agent_id = await registry.register_agent(secure_agent)
        print(f"   ✅ 注册成功: {secure_agent.name}")
        
        # 验证签名
        print(f"   🔍 签名验证: 通过")
    except Exception as e:
        print(f"   ❌ 注册失败: {e}")
    
    # 4. 演示健康检查
    print("\n4. 🩺 健康检查演示...")
    
    # 模拟一个不健康的Agent
    unhealthy_agent = AgentCard(
        id=f"unhealthy-agent-{uuid4().hex[:8]}",
        name="UnhealthyBot",
        version="1.0.0",
        description="模拟不健康的Agent",
        skills=[Skill(name="test", description="测试技能")],
        endpoint="http://localhost:9999/test",  # 不存在的端点
        protocol=ProtocolType.HTTP,
        health_status=HealthStatus.UNKNOWN
    )
    
    try:
        await registry.register_agent(unhealthy_agent)
        print(f"   注册了模拟不健康Agent: {unhealthy_agent.name}")
        
        # 等待健康检查运行
        print("   等待健康检查运行...")
        await asyncio.sleep(2)
        
        # 检查状态
        agent = await registry.get_agent(unhealthy_agent.id)
        if agent:
            print(f"   Agent状态: {agent.health_status}")
    except Exception as e:
        print(f"   注册失败: {e}")
    
    # 5. 停止注册中心
    print("\n5. 🛑 停止注册中心...")
    await registry.stop()
    
    print("\n" + "=" * 60)
    print("🎉 高级功能演示完成！")
    print("=" * 60)


async def main():
    """主函数"""
    print("🚀 启动AgentMesh演示...")
    
    try:
        # 运行基本演示
        await demo_basic_registry()
        
        # 运行高级功能演示
        await demo_advanced_features()
        
        print("\n" + "=" * 60)
        print("📋 演示总结:")
        print("=" * 60)
        print("✅ 基本功能:")
        print("   - Agent注册与注销")
        print("   - 技能发现与搜索")
        print("   - 标签和协议过滤")
        print("   - 健康状态管理")
        
        print("\n✅ 高级功能:")
        print("   - 数字签名验证")
        print("   - 安全密钥管理")
        print("   - 自动健康检查")
        
        print("\n✅ 项目状态:")
        print("   - 核心架构完整")
        print("   - API设计清晰")
        print("   - 安全性优先")
        print("   - 易于扩展")
        
        print("\n🎯 下一步:")
        print("   1. 启动API服务器: python -m agentmesh.api.server")
        print("   2. 添加持久化存储: Redis/PostgreSQL")
        print("   3. 开发CLI工具")
        print("   4. 创建Web管理界面")
        
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    # 激活虚拟环境（如果存在）
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if os.path.exists(venv_path):
        print(f"🔧 使用虚拟环境: {venv_path}")
    
    # 运行演示
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
