import pika

# 建立到Rabbitmq的连接
credentials = pika.PlainCredentials("guest","guest")
conn_para = pika.ConnectionParameters("localhost",credentials=credentials)
conn_broker = pika.BlockingConnection(conn_para)

# 获得信道
channel = conn_broker.channel()

# 声明交换器
channel.exchange_declare(exchange="hello-exchange",type="direct",passive=False,durable=True,auto_delete=False)

# 通过路由键"hola"将队列和交换器绑定起来
channel.queue_declare(queue="hello-queue")
channel.queue_bind(queue="hello-queue",exchange="hello-exchange",routing_key="hola")

# 用于处理传入消息的函数(回调函数)
def msg_consumer2(channel,method,header,body):
    # 消息确认
    channel.basic_ack(delivery_tag=method.delivery_tag)
    if body == "quit":
        # 停止消费并退出
        channel.basic_cancel(consumer_tag="hello-consumer")
        channel.stop_consuming()
    else:
        print('{0}2'.format(body))

    return

# 订阅消费者
channel.basic_consume(msg_consumer2,queue="hello-queue",consumer_tag="hello-consumer")

# 开始消费
channel.start_consuming()