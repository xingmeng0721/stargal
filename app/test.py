import redis

try:
    r = redis.Redis(
        host="127.0.0.1",
        port=6379,
        password="xm@123456",
        db=0,
        decode_responses=True,
        socket_timeout=3
    )
    # 连通测试
    res = r.ping()
    print("✅ Redis连接成功，ping返回：", res)

    # 简单读写测试
    r.set("test_key", "连接正常")
    print("读取数据：", r.get("test_key"))

except Exception as e:
    print("❌ 连接失败：", str(e))