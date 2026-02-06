"""
AI 调度器测试脚本

演示如何使用 AIScheduler 计算节点评分
"""

from backend.services.ai_scheduler import AIScheduler, calculate_scores
import pandas as pd


def test_with_dict_list():
    """测试：使用字典列表作为输入"""
    print("=" * 60)
    print("测试 1: 使用字典列表")
    print("=" * 60)
    
    # 模拟节点数据
    nodes = [
        {
            "id": 1,
            "name": "US-East-01",
            "ip": "192.168.1.100",
            "latency": 20,      # 低延迟
            "load_factor": 0.3   # 低负载
        },
        {
            "id": 2,
            "name": "EU-London-02",
            "ip": "192.168.1.101",
            "latency": 100,     # 中延迟
            "load_factor": 0.7   # 高负载
        },
        {
            "id": 3,
            "name": "Asia-Seoul-01",
            "ip": "192.168.1.102",
            "latency": 50,      # 低延迟
            "load_factor": 0.2   # 极低负载
        },
        {
            "id": 4,
            "name": "US-West-03",
            "ip": "192.168.1.103",
            "latency": 200,     # 高延迟
            "load_factor": 0.9   # 极高负载
        },
    ]
    
    # 计算评分
    result = calculate_scores(nodes)
    
    # 显示结果
    print(f"\n共 {len(result)} 个节点，按 AI 评分排序：\n")
    for node in result:
        print(f"#{node['rank']} {node['name']:<20} "
              f"延迟: {node['latency']:>3}ms  "
              f"负载: {node['load_factor']:.2f}  "
              f"AI 评分: {node['ai_score']:.4f}")
    
    print(f"\n🏆 推荐节点: {result[0]['name']}")
    print()


def test_with_dataframe():
    """测试：使用 Pandas DataFrame 作为输入"""
    print("=" * 60)
    print("测试 2: 使用 Pandas DataFrame")
    print("=" * 60)
    
    # 创建 DataFrame
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Tokyo', 'Singapore', 'Mumbai', 'Sydney', 'Seoul'],
        'latency': [30, 45, 80, 120, 25],
        'load_factor': [0.4, 0.5, 0.3, 0.8, 0.2]
    })
    
    print("\n原始数据:")
    print(df)
    
    # 计算评分
    scheduler = AIScheduler()
    result = scheduler.calculate_scores(df)
    
    # 转换为 DataFrame 展示
    result_df = pd.DataFrame(result)[['rank', 'name', 'latency', 'load_factor', 'ai_score']]
    print("\n排序后的结果:")
    print(result_df)
    print()


def test_custom_weights():
    """测试：自定义权重"""
    print("=" * 60)
    print("测试 3: 自定义权重（延迟优先策略）")
    print("=" * 60)
    
    nodes = [
        {"id": 1, "name": "Low-Latency-High-Load", "latency": 10, "load_factor": 0.9},
        {"id": 2, "name": "High-Latency-Low-Load", "latency": 200, "load_factor": 0.1},
    ]
    
    # 默认权重 (延迟 0.5, 负载 0.3)
    print("\n默认权重 (延迟:0.5, 负载:0.3, 随机:0.2):")
    result1 = calculate_scores(nodes)
    for node in result1:
        print(f"  {node['name']:<30} AI 评分: {node['ai_score']:.4f}")
    
    # 延迟优先 (延迟 0.8, 负载 0.1)
    print("\n延迟优先权重 (延迟:0.8, 负载:0.1, 随机:0.1):")
    result2 = calculate_scores(nodes, latency_weight=0.8, load_weight=0.1, random_weight=0.1)
    for node in result2:
        print(f"  {node['name']:<30} AI 评分: {node['ai_score']:.4f}")
    
    # 负载优先 (延迟 0.2, 负载 0.7)
    print("\n负载优先权重 (延迟:0.2, 负载:0.7, 随机:0.1):")
    result3 = calculate_scores(nodes, latency_weight=0.2, load_weight=0.7, random_weight=0.1)
    for node in result3:
        print(f"  {node['name']:<30} AI 评分: {node['ai_score']:.4f}")
    
    print()


def test_edge_cases():
    """测试：边界情况"""
    print("=" * 60)
    print("测试 4: 边界情况")
    print("=" * 60)
    
    # 单个节点
    print("\n单个节点:")
    single = [{"id": 1, "name": "Only-One", "latency": 50, "load_factor": 0.5}]
    result = calculate_scores(single)
    print(f"  {result[0]['name']}: AI 评分 = {result[0]['ai_score']:.4f}")
    
    # 所有节点延迟相同
    print("\n所有节点延迟相同:")
    same_latency = [
        {"id": 1, "name": "Node-A", "latency": 50, "load_factor": 0.2},
        {"id": 2, "name": "Node-B", "latency": 50, "load_factor": 0.8},
    ]
    result = calculate_scores(same_latency)
    for node in result:
        print(f"  {node['name']}: AI 评分 = {node['ai_score']:.4f}")
    
    print()


if __name__ == "__main__":
    print("\n🤖 AI 节点调度器测试\n")
    
    # 运行所有测试
    test_with_dict_list()
    test_with_dataframe()
    test_custom_weights()
    test_edge_cases()
    
    print("=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
