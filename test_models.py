"""测试数据模型和数据库初始化"""
from backend.database import create_db_and_tables, get_session
from backend.models import User, Node, NodeMetrics
from datetime import datetime


def test_create_tables():
    """测试创建数据库表"""
    print("🔧 创建数据库表...")
    create_db_and_tables()
    print("✅ 数据库表创建成功！\n")


def test_insert_sample_data():
    """测试插入示例数据"""
    print("📝 插入示例数据...")
    
    with next(get_session()) as session:
        # 创建测试用户
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            balance=100.0,
            traffic_limit_gb=100,
            current_traffic_gb=25.5,
            is_active=True
        )
        session.add(user)
        
        # 创建测试节点
        node = Node(
            name="US-West-01",
            ip="192.168.1.100",
            port=1194,
            protocol="OpenVPN",
            ai_score=0.85,
            load_factor=0.42
        )
        session.add(node)
        session.commit()
        session.refresh(node)  # 获取生成的 ID
        
        # 创建测试监控记录
        metrics = NodeMetrics(
            node_id=node.id,
            latency=45,
            packet_loss=0.02,
            recorded_at=datetime.utcnow()
        )
        session.add(metrics)
        session.commit()
        
        print(f"✅ 用户创建成功: {user.email}")
        print(f"✅ 节点创建成功: {node.name} ({node.ip}:{node.port})")
        print(f"✅ 监控记录创建成功: 延迟 {metrics.latency}ms, 丢包率 {metrics.packet_loss*100}%\n")


def test_query_data():
    """测试查询数据"""
    print("🔍 查询数据...")
    
    with next(get_session()) as session:
        # 查询所有用户
        users = session.query(User).all()
        print(f"📊 用户总数: {len(users)}")
        for user in users:
            print(f"   - {user.email} (余额: ¥{user.balance}, 流量: {user.current_traffic_gb}/{user.traffic_limit_gb}GB)")
        
        # 查询所有节点
        nodes = session.query(Node).all()
        print(f"📊 节点总数: {len(nodes)}")
        for node in nodes:
            print(f"   - {node.name} ({node.ip}:{node.port}) - AI评分: {node.ai_score}, 负载: {node.load_factor}")
        
        # 查询所有监控记录
        metrics = session.query(NodeMetrics).all()
        print(f"📊 监控记录总数: {len(metrics)}")
        for metric in metrics:
            print(f"   - 节点{metric.node_id}: 延迟{metric.latency}ms, 丢包{metric.packet_loss*100}%, 记录时间{metric.recorded_at}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SQLModel 数据模型测试")
    print("=" * 60)
    print()
    
    # 1. 创建表
    test_create_tables()
    
    # 2. 插入示例数据
    test_insert_sample_data()
    
    # 3. 查询数据
    test_query_data()
    
    print()
    print("=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)
